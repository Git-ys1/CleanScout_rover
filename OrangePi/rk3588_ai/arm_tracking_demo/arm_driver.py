#!/usr/bin/env python3
"""Safe mechanical-arm driver wrapper for the OrangePi tracking demo."""

from __future__ import annotations

import json
import time
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Union


Number = Union[int, float]


DEFAULT_CONFIG = {
    "protocol": "yh_pwm_text",
    "timeout_s": 0.2,
    "echo_commands": True,
    "yaw_joint": "joint0",
    "pitch_joint": "joint3",
    "yaw_servo_index": 0,
    "pitch_servo_index": 3,
    "duration_ms": 200,
    "yaw_init": 0.0,
    "pitch_init": 1.2,
    "yaw_pwm_neutral": 1500,
    "pitch_pwm_neutral": 1500,
    "yaw_pwm_per_rad": 500,
    "pitch_pwm_per_rad": 500,
    "yaw_pwm_sign": 1,
    "pitch_pwm_sign": -1,
    "pwm_min": 900,
    "pwm_max": 2100,
    "reference_hold_joints": [0.0, -0.930, 1.6, 1.2, 0.0, 0.801],
    "stop_servo_indices": [0, 3],
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
                "pyserial is required for real arm output. Install it in the RKNN env first."
            ) from exc

        self.serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=float(self.config.get("timeout_s", 0.2)),
        )
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

        protocol = str(self.config.get("protocol", "yh_pwm_text"))
        if protocol == "yh_pwm_text":
            joints = {
                "yaw": yaw,
                "pitch": pitch,
            }
        else:
            joints = list(self.config["reference_hold_joints"])
            joints[0] = yaw
            joints[3] = pitch
        return self.set_joints(joints, duration_ms=duration_ms)

    def stop(self):
        protocol = str(self.config.get("protocol", "yh_pwm_text"))
        if protocol == "yh_pwm_text":
            # Avoid the official firmware's all-stop path until the
            # pwmServo_stop_motion(255) out-of-range access is fixed/verified.
            for index in self.config.get("stop_servo_indices", [0, 3]):
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
        yaw_index = int(self.config["yaw_servo_index"])
        pitch_index = int(self.config["pitch_servo_index"])
        yaw_pwm = self._angle_to_pwm(float(joints[0]), "yaw")
        pitch_pwm = self._angle_to_pwm(float(joints[3]), "pitch")
        duration = int(_clamp(int(duration_ms), 20, 9999))
        command = "#{:03d}P{:04d}T{:04d}!#{:03d}P{:04d}T{:04d}!".format(
            yaw_index,
            yaw_pwm,
            duration,
            pitch_index,
            pitch_pwm,
            duration,
        )
        return command.encode("ascii")

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
        self.serial.write(payload)
        self.serial.flush()


if __name__ == "__main__":
    driver = ArmDriver("/dev/ttyS7", 115200, dry_run=True)
    driver.connect()
    driver.set_yaw_pitch(0.0, 1.2, 200)
    driver.stop()
    driver.close()
