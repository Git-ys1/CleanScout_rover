#!/usr/bin/env python3

import argparse
import sys
import time

import pigpio


def angle_to_pulse_us(angle):
    # Current field calibration: 90=open, 180=close.
    # Map 0-180 deg into a conservative 500-2500us range.
    angle = max(0.0, min(180.0, angle))
    return int(500.0 + (angle / 180.0) * 2000.0)


def main():
    parser = argparse.ArgumentParser(description="Direct servo test on GPIO12 using pigpio")
    parser.add_argument("--gpio", type=int, default=12, help="servo signal GPIO, default 12")
    parser.add_argument("--angle", type=float, help="single target angle in degrees")
    parser.add_argument("--open-angle", type=float, default=90.0, help="field calibrated open angle")
    parser.add_argument("--close-angle", type=float, default=180.0, help="field calibrated close angle")
    parser.add_argument("--settle", type=float, default=0.6, help="settle seconds after each move")
    parser.add_argument("--hold", action="store_true", help="keep servo pulses active after move")
    args = parser.parse_args()

    pi = pigpio.pi()
    if not pi.connected:
      print("ERROR: pigpio daemon not connected. Start with: sudo systemctl start pigpiod", file=sys.stderr)
      return 2

    try:
        if args.angle is not None:
            pulse = angle_to_pulse_us(args.angle)
            print(f"move gpio={args.gpio} angle={args.angle} pulse_us={pulse}", flush=True)
            pi.set_servo_pulsewidth(args.gpio, pulse)
            time.sleep(args.settle)
        else:
            for label, angle in (("open", args.open_angle), ("close", args.close_angle)):
                pulse = angle_to_pulse_us(angle)
                print(f"move {label}: gpio={args.gpio} angle={angle} pulse_us={pulse}", flush=True)
                pi.set_servo_pulsewidth(args.gpio, pulse)
                time.sleep(args.settle)

        if not args.hold:
            print(f"release gpio={args.gpio}", flush=True)
            pi.set_servo_pulsewidth(args.gpio, 0)

        return 0
    finally:
        pi.stop()


if __name__ == "__main__":
    raise SystemExit(main())
