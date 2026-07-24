# coding: utf-8
"""Thread-safe ROS-free ASCII/PRAD adapter for the CleanScout arm."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import re
import threading
import time
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    import serial
except Exception:  # pyserial may not exist on a development PC
    serial = None


@dataclass(frozen=True)
class JointPWMMap:
    servo_id: int
    center_us: int = 1500
    us_per_rad: float = 500.0 / 1.5708
    sign: int = 1
    offset_rad: float = 0.0
    min_us: int = 500
    max_us: int = 2200

    def to_pwm(self, rad: float) -> int:
        pwm = self.center_us + self.sign * (
            float(rad) + self.offset_rad
        ) * self.us_per_rad
        return int(max(self.min_us, min(self.max_us, round(pwm))))


DEFAULT_JOINT_MAPS = [
    JointPWMMap(0, center_us=1500, sign=+1, min_us=500, max_us=2490),
    JointPWMMap(1, center_us=1500, sign=-1, min_us=500, max_us=2490),
    JointPWMMap(2, center_us=1500, sign=+1, min_us=500, max_us=2490),
    JointPWMMap(3, center_us=1500, sign=+1, min_us=500, max_us=2490),
    JointPWMMap(4, center_us=1500, sign=+1, min_us=500, max_us=2490),
    JointPWMMap(5, center_us=1500, sign=+1, min_us=500, max_us=2490),
]

POSITION_RE = re.compile(r"#(?P<id>\d{3})P(?P<pwm>\d{4})!")


class PWMReadbackError(RuntimeError):
    """Raised when a required PRAD snapshot is incomplete."""

    def __init__(self, missing_ids, attempts: int, partial=None):
        self.missing_ids = tuple(int(value) for value in missing_ids)
        self.attempts = int(attempts)
        self.partial = dict(partial or {})
        super().__init__(
            "PRAD missing required servo IDs {} after {} attempt(s)".format(
                list(self.missing_ids), self.attempts
            )
        )


@dataclass(frozen=True)
class PWMReadbackSnapshot:
    pwms: Mapping[int, int]
    monotonic_timestamp: float
    attempts: int
    simulated: bool = False

    def __post_init__(self) -> None:
        normalized = {int(key): int(value) for key, value in self.pwms.items()}
        object.__setattr__(self, "pwms", normalized)
        if not math.isfinite(float(self.monotonic_timestamp)):
            raise ValueError("snapshot timestamp must be finite")
        if int(self.attempts) <= 0:
            raise ValueError("snapshot attempts must be positive")

    def ordered(self, ids: Iterable[int] = range(6)) -> Tuple[int, ...]:
        return tuple(int(self.pwms[int(servo_id)]) for servo_id in ids)

    def as_dict(self):
        return {
            "pwms": {str(key): int(value) for key, value in sorted(self.pwms.items())},
            "monotonic_timestamp": float(self.monotonic_timestamp),
            "attempts": int(self.attempts),
            "simulated": bool(self.simulated),
        }


@dataclass(frozen=True)
class ServoCommandResult:
    command: str
    command_packed: bool
    command_written: bool
    readback_reached: bool
    simulated: bool
    motion_end_monotonic: float
    snapshot: Optional[PWMReadbackSnapshot] = None
    mismatches: Mapping[int, Mapping[str, int]] = field(default_factory=dict)
    reason: str = ""

    @property
    def ok(self) -> bool:
        return bool(
            self.command_packed
            and self.readback_reached
            and (self.simulated or self.command_written)
        )


class SerialServoArmAdapter:
    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 115200,
        dry_run: bool = True,
        joint_maps: Optional[List[JointPWMMap]] = None,
        initial_pwms: Optional[Sequence[int]] = None,
        readback_retries: int = 3,
        readback_timeout_s: float = 0.8,
        readback_tolerance_pwm: int = 40,
        motion_settle_s: float = 0.15,
        fixed_pwm_requirements: Optional[Mapping[int, int]] = None,
    ) -> None:
        self.port = str(port)
        self.baudrate = int(baudrate)
        self.dry_run = bool(dry_run)
        self.joint_maps = joint_maps or list(DEFAULT_JOINT_MAPS)
        self.readback_retries = int(readback_retries)
        self.readback_timeout_s = float(readback_timeout_s)
        self.readback_tolerance_pwm = int(readback_tolerance_pwm)
        self.motion_settle_s = float(motion_settle_s)
        self.fixed_pwm_requirements = {
            int(key): int(value)
            for key, value in (
                {4: 1500}
                if fixed_pwm_requirements is None
                else fixed_pwm_requirements
            ).items()
        }
        if self.readback_retries <= 0:
            raise ValueError("readback_retries must be positive")
        if self.readback_timeout_s <= 0.0 or self.motion_settle_s < 0.0:
            raise ValueError("readback timeout must be positive and settle non-negative")
        if self.readback_tolerance_pwm < 0:
            raise ValueError("readback_tolerance_pwm must be non-negative")
        ids = [mapping.servo_id for mapping in self.joint_maps]
        if len(ids) != len(set(ids)):
            raise ValueError("joint_maps contains duplicate servo IDs")
        known_ids = set(ids)
        if any(key not in known_ids for key in self.fixed_pwm_requirements):
            raise ValueError("fixed_pwm_requirements contains an unknown servo")
        maps_by_id = {mapping.servo_id: mapping for mapping in self.joint_maps}
        for servo_id, value in self.fixed_pwm_requirements.items():
            mapping = maps_by_id[servo_id]
            if value < mapping.min_us or value > mapping.max_us:
                raise ValueError("fixed PWM requirement is outside servo range")
        defaults = (
            [mapping.center_us for mapping in self.joint_maps]
            if initial_pwms is None
            else [int(value) for value in initial_pwms]
        )
        if len(defaults) != len(self.joint_maps):
            raise ValueError("initial_pwms must contain one value per servo")
        self._dry_run_pwms = {
            mapping.servo_id: int(value)
            for mapping, value in zip(self.joint_maps, defaults)
        }
        self._ser = None
        self._lock = threading.RLock()
        self.last_joints = [0.0] * 6  # legacy dry-run diagnostic only

    def connect(self) -> None:
        with self._lock:
            if self.dry_run:
                return
            if self._ser is not None:
                return
            if serial is None:
                raise RuntimeError("pyserial is not installed")
            try:
                self._ser = serial.Serial(
                    self.port,
                    self.baudrate,
                    timeout=0.08,
                    write_timeout=0.2,
                    exclusive=True,
                )
            except TypeError:
                self._ser = serial.Serial(
                    self.port,
                    self.baudrate,
                    timeout=0.08,
                    write_timeout=0.2,
                )
            time.sleep(0.1)

    def close(self) -> None:
        with self._lock:
            if self._ser is not None:
                self._ser.close()
                self._ser = None

    def _read_response_locked(
        self, timeout_s: float = 0.8, idle_s: float = 0.08
    ) -> bytes:
        if self._ser is None:
            raise RuntimeError("serial is not connected")
        deadline = time.monotonic() + float(timeout_s)
        last_rx = time.monotonic()
        chunks = []
        while time.monotonic() < deadline:
            waiting = int(getattr(self._ser, "in_waiting", 0))
            if waiting:
                chunks.append(self._ser.read(waiting))
                last_rx = time.monotonic()
            elif chunks and time.monotonic() - last_rx >= float(idle_s):
                break
            else:
                time.sleep(0.01)
        return b"".join(chunks)

    def transact_ascii(
        self, command: str, timeout_s: float = 0.8, delay_s: float = 0.05
    ) -> str:
        """Send one official ASCII query and collect its reply atomically."""

        with self._lock:
            if self.dry_run:
                print("[DRY-RUN QUERY]", command)
                return ""
            if self._ser is None:
                self.connect()
            if hasattr(self._ser, "reset_input_buffer"):
                self._ser.reset_input_buffer()
            self._write_exact_locked(str(command).encode("ascii"))
            self._ser.flush()
            time.sleep(float(delay_s))
            return self._read_response_locked(timeout_s=timeout_s).decode(
                "ascii", errors="replace"
            )

    def read_pwm(self, servo_id: int, timeout_s: float = 0.8) -> Optional[int]:
        servo_id = int(servo_id)
        if servo_id < 0 or servo_id > 253:
            raise ValueError("servo_id must be in 0..253")
        with self._lock:
            if self.dry_run:
                return self._dry_run_pwms.get(servo_id)
            response = self.transact_ascii(
                "#{:03d}PRAD!".format(servo_id), timeout_s=timeout_s
            )
            # A reply for another ID is never accepted as this joint's state.
            for match in POSITION_RE.finditer(response):
                if int(match.group("id")) == servo_id:
                    return int(match.group("pwm"))
            return None

    def read_pwms(
        self, servo_ids: Iterable[int], timeout_s: float = 0.8
    ) -> Dict[int, Optional[int]]:
        """Compatibility read that preserves missing IDs as ``None``."""

        with self._lock:
            return {
                int(servo_id): self.read_pwm(int(servo_id), timeout_s=timeout_s)
                for servo_id in servo_ids
            }

    def read_required_pwms(
        self,
        ids: Iterable[int] = (0, 1, 2, 3, 4, 5),
        retries: Optional[int] = None,
        timeout_s: Optional[float] = None,
    ) -> PWMReadbackSnapshot:
        required, attempts_limit, timeout = self._validate_read_request(
            ids, retries, timeout_s
        )
        with self._lock:
            if self.dry_run:
                values = {servo_id: self._dry_run_pwms[servo_id] for servo_id in required}
                return PWMReadbackSnapshot(
                    values, time.monotonic(), attempts=1, simulated=True
                )
            last_values: Dict[int, int] = {}
            for attempt in range(1, attempts_limit + 1):
                # A snapshot must be internally contemporaneous.  Never stitch
                # values from separate retry attempts into a false success.
                values: Dict[int, int] = {}
                for servo_id in required:
                    value = self.read_pwm(servo_id, timeout_s=timeout)
                    if value is not None:
                        values[servo_id] = int(value)
                missing = [servo_id for servo_id in required if servo_id not in values]
                if not missing:
                    return PWMReadbackSnapshot(
                        values, time.monotonic(), attempts=attempt, simulated=False
                    )
                last_values = values
            raise PWMReadbackError(missing, attempts_limit, last_values)

    def _validate_read_request(self, ids, retries, timeout_s):
        required = tuple(int(value) for value in ids)
        if not required or len(required) != len(set(required)):
            raise ValueError("required PWM IDs must be a non-empty unique sequence")
        known = {mapping.servo_id for mapping in self.joint_maps}
        if any(value not in known for value in required):
            raise ValueError("required PWM IDs contain an unknown servo")
        attempts_limit = self.readback_retries if retries is None else int(retries)
        timeout = self.readback_timeout_s if timeout_s is None else float(timeout_s)
        if attempts_limit <= 0 or timeout <= 0.0:
            raise ValueError("retries and timeout_s must be positive")
        return required, attempts_limit, timeout

    def _maps_by_id(self):
        return {mapping.servo_id: mapping for mapping in self.joint_maps}

    def _normalize_assignments(self, assignments) -> Dict[int, int]:
        maps_by_id = self._maps_by_id()
        normalized = {}
        for key, raw_value in assignments.items():
            servo_id = int(key)
            value = int(raw_value)
            mapping = maps_by_id.get(servo_id)
            if mapping is None:
                raise ValueError("unknown servo id: {}".format(servo_id))
            if value < mapping.min_us or value > mapping.max_us:
                raise ValueError(
                    "servo {} PWM outside configured range: {}".format(
                        servo_id, value
                    )
                )
            normalized[servo_id] = value
        if not normalized:
            raise ValueError("at least one servo assignment is required")
        return dict(sorted(normalized.items()))

    def pack_joint_command(
        self, joints_rad: Iterable[float], duration_ms: int = 1000
    ) -> str:
        values = list(joints_rad)
        assignments = {
            mapping.servo_id: mapping.to_pwm(rad)
            for rad, mapping in zip(values, self.joint_maps)
        }
        return self.pack_partial_pwm_command(assignments, duration_ms)

    def pack_pwm_command(
        self, servo_pwms: Iterable[int], duration_ms: int = 1000
    ) -> str:
        values = [int(value) for value in servo_pwms]
        if len(values) != len(self.joint_maps):
            raise ValueError("servo_pwms must contain exactly six values")
        return self.pack_partial_pwm_command(
            {
                mapping.servo_id: value
                for mapping, value in zip(self.joint_maps, values)
            },
            duration_ms,
        )

    def pack_partial_pwm_command(self, assignments, duration_ms: int = 1000) -> str:
        duration = int(duration_ms)
        if duration < 20 or duration > 9999:
            raise ValueError("duration_ms must be in 20..9999")
        normalized = self._normalize_assignments(assignments)
        frames = [
            "#{:03d}P{:04d}T{:04d}!".format(servo_id, value, duration)
            for servo_id, value in normalized.items()
        ]
        return frames[0] if len(frames) == 1 else "{" + "".join(frames) + "}"

    @staticmethod
    def pack_kinematics_command(
        tool_xyz_m: Iterable[float], duration_ms: int = 1000
    ) -> str:
        xyz = [float(value) for value in tool_xyz_m]
        if len(xyz) != 3 or not all(math.isfinite(value) for value in xyz):
            raise ValueError("tool_xyz_m must contain three finite values")
        forward, left, up = xyz
        if forward <= 0.0:
            raise ValueError("official $KMS requires a positive forward coordinate")
        duration = int(duration_ms)
        if duration < 20 or duration > 9999:
            raise ValueError("official $KMS duration_ms must be in 20..9999")
        return "$KMS:{:.1f},{:.1f},{:.1f},{}!".format(
            left * 1000.0, forward * 1000.0, up * 1000.0, duration
        )

    def _write_motion_command(self, command: str, dry_label: str) -> str:
        with self._lock:
            if self.dry_run:
                print(dry_label, command)
                return command
            if self._ser is None:
                self.connect()
            self._write_exact_locked(command.encode("ascii"))
            self._ser.flush()
            return command

    def _write_exact_locked(self, payload: bytes) -> None:
        if self._ser is None:
            raise RuntimeError("serial is not connected")
        written = self._ser.write(payload)
        if written is None or int(written) != len(payload):
            raise IOError(
                "serial short write: wrote {} of {} bytes".format(
                    written, len(payload)
                )
            )

    def send_joint_command(
        self, joints_rad: Iterable[float], duration_ms: int = 1000
    ) -> str:
        values = list(joints_rad)
        command = self.pack_joint_command(values, duration_ms)
        self.last_joints = values
        if self.dry_run:
            self._dry_run_pwms.update(
                {
                    mapping.servo_id: mapping.to_pwm(rad)
                    for rad, mapping in zip(values, self.joint_maps)
                }
            )
        return self._write_motion_command(command, "[DRY-RUN ARM]")

    def send_pwm_command(
        self, servo_pwms: Iterable[int], duration_ms: int = 1000
    ) -> str:
        values = [int(value) for value in servo_pwms]
        command = self.pack_pwm_command(values, duration_ms)
        if self.dry_run:
            self._dry_run_pwms.update(
                {mapping.servo_id: value for mapping, value in zip(self.joint_maps, values)}
            )
        return self._write_motion_command(command, "[DRY-RUN ARM]")

    def send_partial_pwm_command(self, assignments, duration_ms: int = 1000) -> str:
        normalized = self._normalize_assignments(assignments)
        command = self.pack_partial_pwm_command(normalized, duration_ms)
        if self.dry_run:
            self._dry_run_pwms.update(normalized)
        return self._write_motion_command(command, "[DRY-RUN ARM]")

    def send_kinematics_command(
        self, tool_xyz_m: Iterable[float], duration_ms: int = 1000
    ) -> str:
        command = self.pack_kinematics_command(tool_xyz_m, duration_ms)
        return self._write_motion_command(command, "[DRY-RUN KMS]")

    def send_and_wait_readback(
        self,
        assignments,
        duration_ms: int,
        tolerance_pwm: Optional[int] = None,
        required_ids: Iterable[int] = (0, 1, 2, 3, 4, 5),
        settle_s: Optional[float] = None,
        retries: Optional[int] = None,
        timeout_s: Optional[float] = None,
    ) -> ServoCommandResult:
        """Send one bounded motion and accept completion only after PRAD."""

        normalized = self._normalize_assignments(assignments)
        command = self.pack_partial_pwm_command(normalized, duration_ms)
        tolerance = (
            self.readback_tolerance_pwm
            if tolerance_pwm is None
            else int(tolerance_pwm)
        )
        settle = self.motion_settle_s if settle_s is None else float(settle_s)
        if tolerance < 0 or settle < 0.0:
            raise ValueError("tolerance and settle must be non-negative")
        # Validate everything before the first physical byte can be written.
        required, _, _ = self._validate_read_request(
            required_ids, retries, timeout_s
        )
        if not set(normalized).issubset(set(required)):
            raise ValueError("every commanded servo must be present in required_ids")
        if not set(self.fixed_pwm_requirements).issubset(set(required)):
            raise ValueError("required_ids must include every fixed-PWM servo")
        for servo_id, fixed_pwm in self.fixed_pwm_requirements.items():
            if servo_id in normalized and normalized[servo_id] != fixed_pwm:
                raise ValueError(
                    "Servo{:03d} must remain at PWM {}".format(
                        servo_id, fixed_pwm
                    )
                )
        command_written = False
        motion_end = time.monotonic()
        with self._lock:
            try:
                if self.dry_run:
                    self._dry_run_pwms.update(normalized)
                    print("[DRY-RUN ARM]", command)
                else:
                    if self._ser is None:
                        self.connect()
                    self._write_exact_locked(command.encode("ascii"))
                    self._ser.flush()
                    command_written = True
                    time.sleep(float(duration_ms) / 1000.0 + settle)
                motion_end = time.monotonic()
                snapshot = self.read_required_pwms(
                    required, retries=retries, timeout_s=timeout_s
                )
            except Exception as exc:
                partial_snapshot = None
                if isinstance(exc, PWMReadbackError) and exc.partial:
                    partial_snapshot = PWMReadbackSnapshot(
                        exc.partial,
                        time.monotonic(),
                        attempts=exc.attempts,
                        simulated=False,
                    )
                return ServoCommandResult(
                    command=command,
                    command_packed=True,
                    command_written=command_written,
                    readback_reached=False,
                    simulated=self.dry_run,
                    motion_end_monotonic=motion_end,
                    snapshot=partial_snapshot,
                    mismatches={},
                    reason=str(exc),
                )
            mismatches = {}
            for servo_id, expected in normalized.items():
                actual = snapshot.pwms.get(servo_id)
                if actual is None or abs(int(actual) - int(expected)) > tolerance:
                    mismatches[servo_id] = {
                        "expected_pwm": int(expected),
                        "actual_pwm": -1 if actual is None else int(actual),
                        "delta_pwm": -1 if actual is None else abs(int(actual) - int(expected)),
                    }
            for servo_id, expected in self.fixed_pwm_requirements.items():
                actual = snapshot.pwms.get(servo_id)
                # Frozen Servo004 is an exact structural gate, not a normal
                # arrival-tolerance comparison.
                if actual is None or int(actual) != int(expected):
                    mismatches[servo_id] = {
                        "expected_pwm": int(expected),
                        "actual_pwm": -1 if actual is None else int(actual),
                        "delta_pwm": -1 if actual is None else abs(int(actual) - int(expected)),
                    }
            return ServoCommandResult(
                command=command,
                command_packed=True,
                command_written=command_written,
                readback_reached=not mismatches,
                simulated=self.dry_run,
                motion_end_monotonic=float(motion_end),
                snapshot=snapshot,
                mismatches=mismatches,
                reason=(
                    ""
                    if not mismatches
                    else "PRAD target mismatch: {}".format(mismatches)
                ),
            )

    def send_stop(self, servo_ids: Optional[Iterable[int]] = None) -> str:
        """Explicit operator-requested PDST only; never called on normal exit."""

        known_ids = {mapping.servo_id for mapping in self.joint_maps}
        ids = list(
            known_ids if servo_ids is None else (int(value) for value in servo_ids)
        )
        if not ids or any(servo_id not in known_ids for servo_id in ids):
            raise ValueError("servo_ids must contain known servo ids")
        commands = ["#{:03d}PDST!".format(servo_id) for servo_id in sorted(ids)]
        payload = "".join(commands)
        with self._lock:
            if self.dry_run:
                print("[DRY-RUN STOP]", payload)
                return payload
            if self._ser is None:
                self.connect()
            for frame in commands:
                self._write_exact_locked(frame.encode("ascii"))
                self._ser.flush()
                time.sleep(0.03)
        return payload

    def stop(self) -> None:
        # Kept only for an explicit caller.  Dynamic runtime never invokes it
        # automatically because PDST releases this heavy arm's holding state.
        self.send_stop()
