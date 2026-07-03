#!/usr/bin/env python3
"""Safe mechanical-arm driver wrapper for the OrangePi tracking demo."""

from __future__ import annotations

import json
import os
import time
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Union


Number = Union[int, float]


DEFAULT_CONFIG = {
    "protocol": "yh_pwm_text",
    "timeout_s": 0.2,
    "echo_commands": True,
    "wrap_multi_command": True,
    "yaw_servo_index": 0,
    "lift_servo_index": 1,
    "pitch_servo_index": 3,
    "servo_ids": [0, 1, 2, 3, 4, 5],
    "duration_ms": 200,
    "yaw_init": 0.0,
    "lift_init": -0.930,
    "pitch_init": 1.2,
    "yaw_pwm_neutral": 1500,
    "lift_pwm_neutral": 1912,
    "pitch_pwm_neutral": 884,
    "yaw_pwm_per_rad": 500,
    "lift_pwm_per_rad": 500,
    "pitch_pwm_per_rad": 500,
    "yaw_pwm_sign": 1,
    "lift_pwm_sign": 1,
    "pitch_pwm_sign": -1,
    "pwm_min": 500,
    "pwm_max": 2200,
    "reference_hold_joints": [0.0, -0.930, 1.6, 1.2, 0.0, 0.801],
    "hold_servo_pwms": [1500, 1912, 1915, 884, 1500, 1500],
    "stop_servo_indices": [0],
    "prepare_tracking_pose": True,
    "tracking_pose_pwms": {0: 1500, 1: 1912, 2: 1915, 3: 884, 4: 1500, 5: 1500},
    "tracking_pose_duration_ms": 1500,
    "tracking_pose_settle_s": 4.0,
    "tracking_pose_stages": [
        {"pwms": {1: 1912, 2: 1915}, "duration_ms": 3000, "settle_s": 1.0},
        {"pwms": {0: 1500, 3: 884, 4: 1500, 5: 1500}, "duration_ms": 1500, "settle_s": 0.8},
    ],
}


class ArmDriverError(RuntimeError):
    """Raised when the arm driver cannot safely execute a command."""


def _merge_config(config: Optional[Mapping[str, object]]) -> Dict[str, object]:
    merged = dict(DEFAULT_CONFIG)
    if config:
        for key, value in config.items():
            merged[key] = value
    return merged


def _clamp(value: Number, low: Number, high: Number) -> Number:
    return max(low, min(high, value))


def _i16_bytes(value: int) -> List[int]:
    if value < -32768 or value > 32767:
        raise ArmDriverError("int16 value out of range: {}".format(value))
    if value < 0:
        value = (1 << 16) + value
    return [(value >> 8) & 0xFF, value & 0xFF]


def _checksum(data: Sequence[int], count: int) -> int:
    return sum(data[:count]) & 0xFF


def hex_bytes(payload: bytes) -> str:
    return " ".join("{:02x}".format(byte) for byte in payload)


class ArmDriver:
    """Single communication boundary for mechanical-arm commands.

    Real serial output is disabled by default. In non-dry-run mode pyserial
    must be installed and the target serial port must be explicitly selected.
    """

    def __init__(self, port: str, baudrate: int, dry_run: bool = True, config=None):
        self.port = port
        self.baudrate = int(baudrate)
        self.dry_run = bool(dry_run)
        self.config = _merge_config(config)
        self.serial = None
        self.connected = False
        self.last_joints = list(self.config["reference_hold_joints"])
        self.last_yaw = float(self.config["yaw_init"])
        self.last_lift = float(self.config["lift_init"])
        self.last_pitch = float(self.config["pitch_init"])
        self.last_payload = b""

    def connect(self):
        if self.dry_run:
            self.connected = True
            if self.config.get("echo_commands", True):
                print("[ArmDriver] dry-run connect port={} baud={}".format(self.port, self.baudrate))
            return True

        try:
            import serial  # type: ignore
        except Exception as exc:
            raise ArmDriverError(
                "pyserial is required for real arm output. Install it with: "
                "~/rk3588_ai/rknn_lite_env/bin/python3 -m pip install pyserial"
            ) from exc

        serial_options = {
            "port": self.port,
            "baudrate": self.baudrate,
            "timeout": float(self.config.get("timeout_s", 0.2)),
        }
        if os.name == "posix":
            # Linux otherwise allows multiple processes to open the same tty,
            # which can split or misroute bus-servo replies between tools.
            serial_options["exclusive"] = True
        try:
            self.serial = serial.Serial(**serial_options)
        except Exception as exc:
            raise ArmDriverError(
                "cannot exclusively open serial port {}: {}".format(self.port, exc)
            ) from exc
        self.connected = True
        return True

    def set_joints(self, joints, duration_ms: int = 200):
        if duration_ms <= 0:
            raise ArmDriverError("duration_ms must be positive")

        normalized = self._normalize_joints(joints)
        protocol = str(self.config.get("protocol", "yh_pwm_text"))
        if protocol == "yh_pwm_text":
            payload = self._pack_yh_pwm_text(normalized, duration_ms)
        elif protocol == "reference_binary_ik_0x90":
            payload = self._pack_reference_ik_frame(normalized, duration_ms)
        elif protocol == "reference_binary_arm_0x80":
            payload = self._pack_reference_arm_frame(normalized)
        else:
            raise ArmDriverError("unsupported arm protocol: {}".format(protocol))

        self.last_joints = normalized
        self.last_payload = payload
        self._write_payload(payload)
        return payload

    def set_yaw_pitch(self, yaw: Number, pitch: Number, duration_ms: int = 200):
        yaw = float(yaw)
        pitch = float(pitch)
        self.last_yaw = yaw
        self.last_pitch = pitch

        if str(self.config.get("protocol", "yh_pwm_text")) == "yh_pwm_text":
            payload = self._pack_yh_pwm_text_commands(
                [
                    (int(self.config["yaw_servo_index"]), self._angle_to_pwm(yaw, "yaw")),
                    (int(self.config["pitch_servo_index"]), self._angle_to_pwm(pitch, "pitch")),
                ],
                duration_ms,
            )
            self.last_payload = payload
            self._write_payload(payload)
            return payload

        joints = list(self.config["reference_hold_joints"])
        joints[0] = yaw
        joints[3] = pitch
        return self.set_joints(joints, duration_ms=duration_ms)

    def set_axis_values(self, values: Mapping[str, Number], duration_ms: int = 200):
        """Command only selected logical axes.

        This keeps the visual-servo stages independent: yaw -> Servo000,
        lift -> Servo001, pitch -> Servo003. Other servos hold their current
        physical pose and are not re-commanded unless the caller asks for them.
        """
        axes = []
        for axis in ("yaw", "lift", "pitch"):
            if axis in values:
                axes.append((axis, float(values[axis])))
        if not axes:
            return b""

        for axis, value in axes:
            if axis == "yaw":
                self.last_yaw = value
            elif axis == "lift":
                self.last_lift = value
            elif axis == "pitch":
                self.last_pitch = value

        if str(self.config.get("protocol", "yh_pwm_text")) == "yh_pwm_text":
            axis_to_servo = {
                "yaw": int(self.config["yaw_servo_index"]),
                "lift": int(self.config["lift_servo_index"]),
                "pitch": int(self.config["pitch_servo_index"]),
            }
            commands = [
                (axis_to_servo[axis], self._angle_to_pwm(value, axis))
                for axis, value in axes
            ]
            return self.set_servo_pwms(commands, duration_ms=duration_ms)

        joints = list(self.last_joints)
        for axis, value in axes:
            if axis == "yaw":
                joints[0] = value
            elif axis == "lift":
                joints[1] = value
            elif axis == "pitch":
                joints[3] = value
        return self.set_joints(joints, duration_ms=duration_ms)

    def set_yaw(self, yaw: Number, duration_ms: int = 200):
        yaw = float(yaw)
        self.last_yaw = yaw
        if str(self.config.get("protocol", "yh_pwm_text")) == "yh_pwm_text":
            payload = self._pack_yh_pwm_text_commands(
                [(int(self.config["yaw_servo_index"]), self._angle_to_pwm(yaw, "yaw"))],
                duration_ms,
            )
            self.last_payload = payload
            self._write_payload(payload)
            return payload

        joints = list(self.last_joints)
        joints[0] = yaw
        return self.set_joints(joints, duration_ms=duration_ms)

    def set_lift(self, lift: Number, duration_ms: int = 200):
        lift = float(lift)
        self.last_lift = lift
        if str(self.config.get("protocol", "yh_pwm_text")) == "yh_pwm_text":
            payload = self._pack_yh_pwm_text_commands(
                [(int(self.config["lift_servo_index"]), self._angle_to_pwm(lift, "lift"))],
                duration_ms,
            )
            self.last_payload = payload
            self._write_payload(payload)
            return payload

        joints = list(self.last_joints)
        joints[1] = lift
        return self.set_joints(joints, duration_ms=duration_ms)

    def set_pitch(self, pitch: Number, duration_ms: int = 200):
        pitch = float(pitch)
        self.last_pitch = pitch
        if str(self.config.get("protocol", "yh_pwm_text")) == "yh_pwm_text":
            payload = self._pack_yh_pwm_text_commands(
                [(int(self.config["pitch_servo_index"]), self._angle_to_pwm(pitch, "pitch"))],
                duration_ms,
            )
            self.last_payload = payload
            self._write_payload(payload)
            return payload

        joints = list(self.last_joints)
        joints[3] = pitch
        return self.set_joints(joints, duration_ms=duration_ms)

    def set_servo_pwm(self, servo_id: int, pwm: int, duration_ms: int = 200):
        servo_id = int(servo_id)
        pwm = int(pwm)
        if servo_id < 0 or servo_id > 254:
            raise ArmDriverError("servo id out of range: {}".format(servo_id))
        pwm_min = int(self.config["pwm_min"])
        pwm_max = int(self.config["pwm_max"])
        if pwm < pwm_min or pwm > pwm_max:
            raise ArmDriverError(
                "servo {} pwm out of configured range {}..{}: {}".format(
                    servo_id, pwm_min, pwm_max, pwm
                )
            )
        payload = self._pack_yh_pwm_text_commands([(servo_id, pwm)], duration_ms)
        self.last_payload = payload
        self._write_payload(payload)
        return payload

    def set_servo_pwms(self, commands, duration_ms: int = 200):
        normalized = []
        for servo_id, pwm in commands:
            servo_id = int(servo_id)
            pwm = int(pwm)
            if servo_id < 0 or servo_id > 254:
                raise ArmDriverError("servo id out of range: {}".format(servo_id))
            pwm_min = int(self.config["pwm_min"])
            pwm_max = int(self.config["pwm_max"])
            if pwm < pwm_min or pwm > pwm_max:
                raise ArmDriverError(
                    "servo {} pwm out of configured range {}..{}: {}".format(
                        servo_id, pwm_min, pwm_max, pwm
                    )
                )
            normalized.append((servo_id, pwm))
        if not normalized:
            raise ArmDriverError("at least one servo command is required")
        payload = self._pack_yh_pwm_text_commands(normalized, duration_ms)
        self.last_payload = payload
        self._write_payload(payload)
        return payload

    def prepare_tracking_pose(self):
        stages = self.config.get("tracking_pose_stages")
        if stages:
            last_payload = b""
            for stage in stages:
                pose = stage.get("pwms", {})
                commands = list(pose.items()) if isinstance(pose, Mapping) else list(pose)
                duration_ms = int(stage.get("duration_ms", 3000))
                last_payload = self.set_servo_pwms(commands, duration_ms)
                if not self.dry_run:
                    time.sleep((duration_ms / 1000.0) + float(stage.get("settle_s", 0.5)))
            return last_payload

        pose = self.config.get(
            "tracking_pose_pwms",
            {0: 1500, 1: 1907, 2: 1900, 3: 900, 4: 1500, 5: 1500},
        )
        commands = list(pose.items()) if isinstance(pose, Mapping) else list(pose)
        return self.set_servo_pwms(
            commands,
            int(self.config.get("tracking_pose_duration_ms", 1500)),
        )

    def stop(self, servo_indices=None):
        protocol = str(self.config.get("protocol", "yh_pwm_text"))
        if protocol == "yh_pwm_text":
            # Avoid the official firmware's all-stop path until the
            # pwmServo_stop_motion(255) out-of-range access is fixed/verified.
            indices = (
                servo_indices
                if servo_indices is not None
                else self.config.get("stop_servo_indices", [0, 3])
            )
            for index in indices:
                self._write_payload("#{:03d}PDST!".format(int(index)).encode("ascii"))
        elif self.config.get("echo_commands", True):
            print("[ArmDriver] stop requested; binary reference protocol has no verified stop frame")

    def close(self):
        if self.serial is not None:
            self.serial.close()
        self.connected = False

    def _normalize_joints(self, joints) -> List[float]:
        base = list(self.config["reference_hold_joints"])
        if isinstance(joints, Mapping):
            for key, value in joints.items():
                if key == "yaw":
                    base[0] = float(value)
                elif key == "lift":
                    base[1] = float(value)
                elif key == "pitch":
                    base[3] = float(value)
                elif isinstance(key, str) and key.startswith("joint"):
                    base[int(key[5:])] = float(value)
                else:
                    raise ArmDriverError("unknown joint key: {}".format(key))
            return base

        if isinstance(joints, Iterable):
            values = [float(value) for value in joints]
            if len(values) != 6:
                raise ArmDriverError("set_joints list must contain 6 values")
            return values

        raise ArmDriverError("joints must be a mapping or 6-item list")

    def _angle_to_pwm(self, angle: float, axis: str) -> int:
        if axis == "yaw":
            neutral_angle = float(self.config["yaw_init"])
            neutral_pwm = float(self.config["yaw_pwm_neutral"])
            scale = float(self.config["yaw_pwm_per_rad"])
            sign = float(self.config["yaw_pwm_sign"])
        elif axis == "lift":
            neutral_angle = float(self.config["lift_init"])
            neutral_pwm = float(self.config["lift_pwm_neutral"])
            scale = float(self.config["lift_pwm_per_rad"])
            sign = float(self.config["lift_pwm_sign"])
        elif axis == "pitch":
            neutral_angle = float(self.config["pitch_init"])
            neutral_pwm = float(self.config["pitch_pwm_neutral"])
            scale = float(self.config["pitch_pwm_per_rad"])
            sign = float(self.config["pitch_pwm_sign"])
        else:
            raise ArmDriverError("unknown axis: {}".format(axis))

        pwm = neutral_pwm + sign * (angle - neutral_angle) * scale
        pwm = int(round(_clamp(pwm, self.config["pwm_min"], self.config["pwm_max"])))
        return pwm

    def _pack_yh_pwm_text(self, joints: Sequence[float], duration_ms: int) -> bytes:
        hold_pwms = list(self.config.get("hold_servo_pwms", [1500] * 6))
        servo_ids = list(self.config.get("servo_ids", [0, 1, 2, 3, 4, 5]))
        if len(hold_pwms) < len(servo_ids):
            hold_pwms.extend([1500] * (len(servo_ids) - len(hold_pwms)))

        commands = []
        for servo_id in servo_ids:
            servo_id = int(servo_id)
            if servo_id == int(self.config["yaw_servo_index"]):
                pwm = self._angle_to_pwm(float(joints[0]), "yaw")
            elif servo_id == int(self.config["lift_servo_index"]):
                pwm = self._angle_to_pwm(float(joints[1]), "lift")
            elif servo_id == int(self.config["pitch_servo_index"]):
                pwm = self._angle_to_pwm(float(joints[3]), "pitch")
            else:
                pwm = int(hold_pwms[servo_id]) if servo_id < len(hold_pwms) else 1500
            commands.append((servo_id, pwm))

        return self._pack_yh_pwm_text_commands(commands, duration_ms)

    def _pack_yh_pwm_text_commands(self, commands, duration_ms: int) -> bytes:
        duration = int(_clamp(int(duration_ms), 20, 9999))
        frames = [
            "#{:03d}P{:04d}T{:04d}!".format(int(servo_id), int(pwm), duration)
            for servo_id, pwm in commands
        ]
        payload = "".join(frames)
        if len(frames) > 1 and bool(self.config.get("wrap_multi_command", True)):
            # The official bus-servo table and STM32 parser use {...} for a
            # multi-servo command bundle. Single-servo commands stay unwrapped.
            payload = "{" + payload + "}"
        return payload.encode("ascii")

    def send_text_command(self, command: str) -> bytes:
        """Send one raw bus-servo ASCII command and return immediately available bytes."""
        if not command:
            raise ArmDriverError("command must not be empty")
        payload = command.encode("ascii")
        self._write_payload(payload)
        return self.read_available()

    def read_available(self) -> bytes:
        if self.dry_run:
            return b""
        if not self.connected or self.serial is None:
            raise ArmDriverError("serial is not connected")
        end_time = time.time() + float(self.config.get("timeout_s", 0.2))
        chunks = []
        while time.time() < end_time:
            waiting = int(getattr(self.serial, "in_waiting", 0))
            if waiting > 0:
                chunks.append(self.serial.read(waiting))
            else:
                time.sleep(0.01)
        return b"".join(chunks)

    def _pack_reference_arm_frame(self, joints: Sequence[float]) -> bytes:
        frame = [0xAA, 0x55, 0x11, 0x80]
        for value in joints:
            frame.extend(_i16_bytes(int(round(float(value) * 1000.0))))
        frame.append(_checksum(frame, 16))
        return bytes(frame)

    def _pack_reference_ik_frame(self, joints: Sequence[float], duration_ms: int) -> bytes:
        frame = [0xAA, 0x55, 0x13, 0x90]
        for value in joints:
            frame.extend(_i16_bytes(int(round(float(value) * 1000.0))))
        frame.extend(_i16_bytes(int(duration_ms)))
        frame.append(_checksum(frame, 18))
        return bytes(frame)

    def _write_payload(self, payload: bytes):
        if self.dry_run:
            if self.config.get("echo_commands", True):
                print(
                    json.dumps(
                        {
                            "dry_run": True,
                            "port": self.port,
                            "baudrate": self.baudrate,
                            "payload_ascii": payload.decode("ascii", errors="replace"),
                            "payload_hex": hex_bytes(payload),
                            "time": time.time(),
                        },
                        ensure_ascii=False,
                    )
                )
            return

        if not self.connected or self.serial is None:
            raise ArmDriverError("serial is not connected")
        if self.config.get("echo_commands", True):
            print(
                json.dumps(
                    {
                        "dry_run": False,
                        "port": self.port,
                        "baudrate": self.baudrate,
                        "payload_ascii": payload.decode("ascii", errors="replace"),
                        "payload_hex": hex_bytes(payload),
                        "time": time.time(),
                    },
                    ensure_ascii=False,
                )
            )
        self.serial.write(payload)
        self.serial.flush()


if __name__ == "__main__":
    driver = ArmDriver("/dev/ttyS7", 115200, dry_run=True)
    driver.connect()
    driver.set_yaw_pitch(0.0, 1.2, 200)
    driver.stop()
    driver.close()
