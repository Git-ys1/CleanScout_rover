#!/usr/bin/env python3

import threading

import RPi.GPIO as GPIO
import pigpio
import rospy
from std_msgs.msg import Bool, Float32, String


class FanDualBridge:
    def __init__(self):
        self.relay_gpio = int(rospy.get_param("~relay_gpio", 17))
        self.fan_a_gpio = int(rospy.get_param("~fan_a_gpio", 18))
        self.fan_b_gpio = int(rospy.get_param("~fan_b_gpio", 19))
        self.fan_a_fg_in_gpio = int(rospy.get_param("~fan_a_fg_in_gpio", 23))
        self.fan_a_fg_out_gpio = int(rospy.get_param("~fan_a_fg_out_gpio", 24))
        self.fan_b_fg_in_gpio = int(rospy.get_param("~fan_b_fg_in_gpio", 25))
        self.fan_b_fg_out_gpio = int(rospy.get_param("~fan_b_fg_out_gpio", 16))
        self.pwm_freq_hz = int(rospy.get_param("~pwm_freq_hz", 25000))
        self.enable_delay = float(rospy.get_param("~enable_delay", 0.3))
        self.disable_delay = float(rospy.get_param("~disable_delay", 0.2))
        self.servo_gpio = int(rospy.get_param("~servo_gpio", 12))
        self.open_angle_deg = float(rospy.get_param("~open_angle_deg", 90.0))
        self.close_angle_deg = float(rospy.get_param("~close_angle_deg", 180.0))
        self.move_settle_s = float(rospy.get_param("~move_settle_s", 0.35))
        self.release_after_move = bool(rospy.get_param("~release_after_move", True))
        self.fg_pulses_per_rev = float(rospy.get_param("~fg_pulses_per_rev", 2.0))
        self.fg_publish_interval_s = float(rospy.get_param("~fg_publish_interval_s", 1.0))
        self.enabled = False
        self.lid_open = False
        self.fan_a_percent = 0.0
        self.fan_b_percent = 0.0
        self.edge_counts = {
            "a_in": 0,
            "a_out": 0,
            "b_in": 0,
            "b_out": 0,
        }
        self.rpm = {
            "a_in": 0.0,
            "a_out": 0.0,
            "b_in": 0.0,
            "b_out": 0.0,
            "fan_a": 0.0,
            "fan_b": 0.0,
        }
        self.fg_lock = threading.Lock()
        self.last_fg_publish_time = rospy.Time.now()

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpio daemon not connected; start pigpiod first")

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.relay_gpio, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.fan_a_gpio, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.fan_b_gpio, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.fan_a_fg_in_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.fan_a_fg_out_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.fan_b_fg_in_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.fan_b_fg_out_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.fan_a_pwm = GPIO.PWM(self.fan_a_gpio, self.pwm_freq_hz)
        self.fan_b_pwm = GPIO.PWM(self.fan_b_gpio, self.pwm_freq_hz)
        self.fan_a_pwm.start(0)
        self.fan_b_pwm.start(0)

        GPIO.add_event_detect(self.fan_a_fg_in_gpio, GPIO.RISING, callback=self.make_fg_callback("a_in"), bouncetime=1)
        GPIO.add_event_detect(self.fan_a_fg_out_gpio, GPIO.RISING, callback=self.make_fg_callback("a_out"), bouncetime=1)
        GPIO.add_event_detect(self.fan_b_fg_in_gpio, GPIO.RISING, callback=self.make_fg_callback("b_in"), bouncetime=1)
        GPIO.add_event_detect(self.fan_b_fg_out_gpio, GPIO.RISING, callback=self.make_fg_callback("b_out"), bouncetime=1)

        self.lid_state_pub = rospy.Publisher("/fan_lid/state", Bool, queue_size=10, latch=True)
        self.summary_pub = rospy.Publisher("/fans/state_summary", String, queue_size=10, latch=True)
        self.fan_a_rpm_pub = rospy.Publisher("/fan_a/rpm", Float32, queue_size=10)
        self.fan_b_rpm_pub = rospy.Publisher("/fan_b/rpm", Float32, queue_size=10)
        self.fan_a_fg_in_rpm_pub = rospy.Publisher("/fan_a/fg_in_rpm", Float32, queue_size=10)
        self.fan_a_fg_out_rpm_pub = rospy.Publisher("/fan_a/fg_out_rpm", Float32, queue_size=10)
        self.fan_b_fg_in_rpm_pub = rospy.Publisher("/fan_b/fg_in_rpm", Float32, queue_size=10)
        self.fan_b_fg_out_rpm_pub = rospy.Publisher("/fan_b/fg_out_rpm", Float32, queue_size=10)
        rospy.Subscriber("/fans/enable", Bool, self.enable_callback, queue_size=10)
        rospy.Subscriber("/fan_a/pwm_percent", Float32, self.fan_a_callback, queue_size=10)
        rospy.Subscriber("/fan_b/pwm_percent", Float32, self.fan_b_callback, queue_size=10)
        self.fg_timer = rospy.Timer(rospy.Duration(self.fg_publish_interval_s), self.publish_fg_rpm)

        self.publish_states()

    def make_fg_callback(self, name):
        def callback(_channel):
            with self.fg_lock:
                self.edge_counts[name] += 1

        return callback

    def angle_to_pulse_us(self, angle_deg):
        angle_deg = max(0.0, min(180.0, angle_deg))
        return int(500.0 + (angle_deg / 180.0) * 2000.0)

    def move_lid(self, open_requested):
        angle = self.open_angle_deg if open_requested else self.close_angle_deg
        pulse_us = self.angle_to_pulse_us(angle)
        self.pi.set_servo_pulsewidth(self.servo_gpio, pulse_us)
        rospy.sleep(self.move_settle_s)
        if self.release_after_move:
            self.pi.set_servo_pulsewidth(self.servo_gpio, 0)
        self.lid_open = open_requested
        self.publish_states()

    def publish_states(self):
        self.lid_state_pub.publish(Bool(data=self.lid_open))
        self.summary_pub.publish(
            String(
                data=(
                    f"enabled={self.enabled} lid_open={self.lid_open} "
                    f"relay={'on' if self.enabled else 'off'} fan_a_pwm={self.fan_a_percent:.1f} fan_b_pwm={self.fan_b_percent:.1f} "
                    f"fan_a_rpm={self.rpm['fan_a']:.1f} fan_b_rpm={self.rpm['fan_b']:.1f}"
                )
            )
        )

    def average_available(self, values):
        available = [value for value in values if value > 0.0]
        if not available:
            return 0.0
        return sum(available) / float(len(available))

    def publish_fg_rpm(self, _event):
        now = rospy.Time.now()
        dt = (now - self.last_fg_publish_time).to_sec()
        if dt <= 0.0:
            return

        with self.fg_lock:
            counts = dict(self.edge_counts)
            for key in self.edge_counts:
                self.edge_counts[key] = 0

        scale = 60.0 / (self.fg_pulses_per_rev * dt)
        self.rpm["a_in"] = counts["a_in"] * scale
        self.rpm["a_out"] = counts["a_out"] * scale
        self.rpm["b_in"] = counts["b_in"] * scale
        self.rpm["b_out"] = counts["b_out"] * scale
        self.rpm["fan_a"] = self.average_available([self.rpm["a_in"], self.rpm["a_out"]])
        self.rpm["fan_b"] = self.average_available([self.rpm["b_in"], self.rpm["b_out"]])

        self.fan_a_fg_in_rpm_pub.publish(Float32(data=self.rpm["a_in"]))
        self.fan_a_fg_out_rpm_pub.publish(Float32(data=self.rpm["a_out"]))
        self.fan_b_fg_in_rpm_pub.publish(Float32(data=self.rpm["b_in"]))
        self.fan_b_fg_out_rpm_pub.publish(Float32(data=self.rpm["b_out"]))
        self.fan_a_rpm_pub.publish(Float32(data=self.rpm["fan_a"]))
        self.fan_b_rpm_pub.publish(Float32(data=self.rpm["fan_b"]))
        self.last_fg_publish_time = now
        self.publish_states()

    def set_a(self, percent):
        percent = max(0.0, min(100.0, percent))
        self.fan_a_pwm.ChangeDutyCycle(percent)

    def set_b(self, percent):
        percent = max(0.0, min(100.0, percent))
        self.fan_b_pwm.ChangeDutyCycle(percent)

    def apply_requested_pwm(self):
        if self.enabled and self.lid_open:
            self.set_a(self.fan_a_percent)
            self.set_b(self.fan_b_percent)
        else:
            self.set_a(0.0)
            self.set_b(0.0)
        self.publish_states()

    def enable_callback(self, msg):
        if msg.data and not self.enabled:
            self.move_lid(True)
            rospy.sleep(self.enable_delay)
            GPIO.output(self.relay_gpio, GPIO.HIGH)
            self.enabled = True
            self.apply_requested_pwm()
        elif not msg.data and self.enabled:
            self.set_a(0.0)
            self.set_b(0.0)
            rospy.sleep(self.disable_delay)
            GPIO.output(self.relay_gpio, GPIO.LOW)
            self.enabled = False
            self.move_lid(False)
            self.publish_states()
        elif msg.data and self.enabled:
            self.apply_requested_pwm()

    def fan_a_callback(self, msg):
        self.fan_a_percent = max(0.0, min(100.0, msg.data))
        self.apply_requested_pwm()

    def fan_b_callback(self, msg):
        self.fan_b_percent = max(0.0, min(100.0, msg.data))
        self.apply_requested_pwm()

    def shutdown(self):
        try:
            self.fg_timer.shutdown()
            self.set_a(0.0)
            self.set_b(0.0)
            GPIO.output(self.relay_gpio, GPIO.LOW)
            self.pi.set_servo_pulsewidth(self.servo_gpio, 0)
        finally:
            self.fan_a_pwm.stop()
            self.fan_b_pwm.stop()
            GPIO.cleanup()
            self.pi.stop()


def main():
    rospy.init_node("csrpi_fan_dual_bridge")
    bridge = FanDualBridge()
    rospy.on_shutdown(bridge.shutdown)
    rospy.spin()


if __name__ == "__main__":
    main()
