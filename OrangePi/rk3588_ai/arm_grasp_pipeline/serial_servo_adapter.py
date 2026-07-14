# coding: utf-8
"""ROS-free serial execution adapter for RF1/official arm protocol."""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
import time
from typing import Dict, Iterable, List, Optional

try:
    import serial
except Exception:  # pyserial may not exist on dev PC
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
        pwm = self.center_us + self.sign * (float(rad) + self.offset_rad) * self.us_per_rad
        return int(max(self.min_us, min(self.max_us, round(pwm))))


DEFAULT_JOINT_MAPS = [
    JointPWMMap(0, center_us=1500, sign=+1),
    JointPWMMap(1, center_us=1500, sign=+1),
    JointPWMMap(2, center_us=1500, sign=+1),
    # RF4 y_servo.c already reverses index 3 as aim=3000-aim; keep only one side reversed after RF1实测。
    JointPWMMap(3, center_us=1500, sign=+1),
    JointPWMMap(4, center_us=1500, sign=+1),
    # The official controller exposes the full 005 range through P0600/P2400.
    JointPWMMap(5, center_us=1500, sign=+1, min_us=500, max_us=2500),
]

POSITION_RE = re.compile(r"#(?P<id>\d{3})P(?P<pwm>\d{4})!")


class SerialServoArmAdapter:
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200, dry_run: bool = True,
                 joint_maps: Optional[List[JointPWMMap]] = None) -> None:
        self.port = port
        self.baudrate = baudrate
        self.dry_run = dry_run
        self.joint_maps = joint_maps or DEFAULT_JOINT_MAPS
        self._ser = None
        self.last_joints = [0.0] * 6

    def connect(self) -> None:
        if self.dry_run:
            return
        if serial is None:
            raise RuntimeError("pyserial is not installed")
        try:
            self._ser = serial.Serial(self.port, self.baudrate, timeout=0.08, write_timeout=0.2, exclusive=True)
        except TypeError:
            # Windows pyserial and older pyserial builds may not expose exclusive.
            self._ser = serial.Serial(self.port, self.baudrate, timeout=0.08, write_timeout=0.2)
        time.sleep(0.1)

    def close(self) -> None:
        if self._ser is not None:
            self._ser.close()
            self._ser = None

    def _read_response(self, timeout_s: float = 0.8, idle_s: float = 0.08) -> bytes:
        if self._ser is None:
            raise RuntimeError("serial is not connected")
        deadline = time.time() + float(timeout_s)
        last_rx = time.time()
        chunks = []
        while time.time() < deadline:
            waiting = int(getattr(self._ser, "in_waiting", 0))
            if waiting:
                chunks.append(self._ser.read(waiting))
                last_rx = time.time()
            elif chunks and time.time() - last_rx >= float(idle_s):
                break
            else:
                time.sleep(0.01)
        return b"".join(chunks)

    def transact_ascii(self, command: str, timeout_s: float = 0.8,
                       delay_s: float = 0.05) -> str:
        """Send one official text command and collect its ASCII reply."""
        if self.dry_run:
            print("[DRY-RUN QUERY]", command)
            return ""
        if self._ser is None:
            self.connect()
        if hasattr(self._ser, "reset_input_buffer"):
            self._ser.reset_input_buffer()
        self._ser.write(str(command).encode("ascii"))
        self._ser.flush()
        time.sleep(float(delay_s))
        return self._read_response(timeout_s=timeout_s).decode(
            "ascii", errors="replace"
        )

    def read_pwm(self, servo_id: int, timeout_s: float = 0.8) -> Optional[int]:
        """Read one bus servo position using the documented ``PRAD`` command."""
        servo_id = int(servo_id)
        if servo_id < 0 or servo_id > 253:
            raise ValueError("servo_id must be in 0..253")
        response = self.transact_ascii(
            "#{:03d}PRAD!".format(servo_id), timeout_s=timeout_s
        )
        for match in POSITION_RE.finditer(response):
            if int(match.group("id")) == servo_id:
                return int(match.group("pwm"))
        return None

    def read_pwms(self, servo_ids: Iterable[int],
                  timeout_s: float = 0.8) -> Dict[int, Optional[int]]:
        """Read several positions sequentially so replies cannot be interleaved."""
        return {
            int(servo_id): self.read_pwm(int(servo_id), timeout_s=timeout_s)
            for servo_id in servo_ids
        }

    def pack_joint_command(self, joints_rad: Iterable[float], duration_ms: int = 1000) -> str:
        js = list(joints_rad)
        frames = []
        for rad, mp in zip(js, self.joint_maps):
            frames.append(f"#{mp.servo_id:03d}P{mp.to_pwm(rad):04d}T{int(duration_ms):04d}!")
        # RF4 USART state machine supports {...} mode3. Use one atomic multi-servo frame.
        return "{" + "".join(frames) + "}"

    def pack_pwm_command(self, servo_pwms: Iterable[int], duration_ms: int = 1000) -> str:
        values = [int(value) for value in servo_pwms]
        if len(values) != len(self.joint_maps):
            raise ValueError("servo_pwms must contain exactly six values")
        frames = []
        for value, mapping in zip(values, self.joint_maps):
            if value < mapping.min_us or value > mapping.max_us:
                raise ValueError("servo {} PWM outside configured range: {}".format(mapping.servo_id, value))
            frames.append(f"#{mapping.servo_id:03d}P{value:04d}T{int(duration_ms):04d}!")
        return "{" + "".join(frames) + "}"

    def pack_partial_pwm_command(self, assignments, duration_ms: int = 1000) -> str:
        normalized = []
        maps_by_id = {mapping.servo_id: mapping for mapping in self.joint_maps}
        for servo_id, value in sorted((int(key), int(value)) for key, value in assignments.items()):
            mapping = maps_by_id.get(servo_id)
            if mapping is None:
                raise ValueError("unknown servo id: {}".format(servo_id))
            if value < mapping.min_us or value > mapping.max_us:
                raise ValueError("servo {} PWM outside configured range: {}".format(servo_id, value))
            normalized.append(f"#{servo_id:03d}P{value:04d}T{int(duration_ms):04d}!")
        if not normalized:
            raise ValueError("at least one servo assignment is required")
        return normalized[0] if len(normalized) == 1 else "{" + "".join(normalized) + "}"

    @staticmethod
    def pack_kinematics_command(tool_xyz_m: Iterable[float], duration_ms: int = 1000) -> str:
        """Pack the official ``$KMS:x,y,z,time!`` command.

        Python uses ``[forward, left, up]`` metres. The official firmware uses
        ``[left, forward, up]`` millimetres and only moves Servo000..003.
        """
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
            left * 1000.0,
            forward * 1000.0,
            up * 1000.0,
            duration,
        )

    def send_joint_command(self, joints_rad: Iterable[float], duration_ms: int = 1000) -> str:
        cmd = self.pack_joint_command(joints_rad, duration_ms)
        self.last_joints = list(joints_rad)
        if self.dry_run:
            print("[DRY-RUN ARM]", cmd)
            return cmd
        if self._ser is None:
            self.connect()
        self._ser.write(cmd.encode("ascii"))
        self._ser.flush()
        return cmd

    def send_pwm_command(self, servo_pwms: Iterable[int], duration_ms: int = 1000) -> str:
        cmd = self.pack_pwm_command(servo_pwms, duration_ms)
        if self.dry_run:
            print("[DRY-RUN ARM]", cmd)
            return cmd
        if self._ser is None:
            self.connect()
        self._ser.write(cmd.encode("ascii"))
        self._ser.flush()
        return cmd

    def send_partial_pwm_command(self, assignments, duration_ms: int = 1000) -> str:
        cmd = self.pack_partial_pwm_command(assignments, duration_ms)
        if self.dry_run:
            print("[DRY-RUN CENTER]", cmd)
            return cmd
        if self._ser is None:
            self.connect()
        self._ser.write(cmd.encode("ascii"))
        self._ser.flush()
        return cmd

    def send_kinematics_command(self, tool_xyz_m: Iterable[float], duration_ms: int = 1000) -> str:
        cmd = self.pack_kinematics_command(tool_xyz_m, duration_ms)
        if self.dry_run:
            print("[DRY-RUN KMS]", cmd)
            return cmd
        if self._ser is None:
            self.connect()
        self._ser.write(cmd.encode("ascii"))
        self._ser.flush()
        return cmd

    def send_stop(self, servo_ids: Optional[Iterable[int]] = None) -> str:
        """Stop selected servos without using the unsafe global 255 branch."""
        known_ids = {mapping.servo_id for mapping in self.joint_maps}
        ids = list(known_ids if servo_ids is None else (int(value) for value in servo_ids))
        if not ids or any(servo_id not in known_ids for servo_id in ids):
            raise ValueError("servo_ids must contain known servo ids")
        cmd = "".join(f"#{servo_id:03d}PDST!" for servo_id in sorted(ids))
        if self.dry_run:
            print("[DRY-RUN STOP]", cmd)
            return cmd
        if self._ser is None:
            self.connect()
        self._ser.write(cmd.encode("ascii"))
        self._ser.flush()
        return cmd

    def stop(self) -> None:
        # Avoid #255PDST! until RF1 all-stop path is proven safe; stop axes one by one.
        self.send_stop()
