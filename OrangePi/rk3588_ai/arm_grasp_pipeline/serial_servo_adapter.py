# coding: utf-8
"""ROS-free serial execution adapter for RF1/official arm protocol."""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Iterable, List, Optional

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
    # gripper in learning package is semantic hand value; calibrate separately if RF1 expects PWM.
    JointPWMMap(5, center_us=1500, sign=+1),
]


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

    def pack_joint_command(self, joints_rad: Iterable[float], duration_ms: int = 1000) -> str:
        js = list(joints_rad)
        frames = []
        for rad, mp in zip(js, self.joint_maps):
            frames.append(f"#{mp.servo_id:03d}P{mp.to_pwm(rad):04d}T{int(duration_ms):04d}!")
        # RF4 USART state machine supports {...} mode3. Use one atomic multi-servo frame.
        return "{" + "".join(frames) + "}"

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

    def stop(self) -> None:
        # Avoid #255PDST! until RF1 all-stop path is proven safe; stop axes one by one.
        cmd = "".join(f"#{mp.servo_id:03d}PDST!" for mp in self.joint_maps[:6])
        if self.dry_run:
            print("[DRY-RUN STOP]", cmd)
            return
        if self._ser is None:
            self.connect()
        self._ser.write(cmd.encode("ascii"))
        self._ser.flush()
