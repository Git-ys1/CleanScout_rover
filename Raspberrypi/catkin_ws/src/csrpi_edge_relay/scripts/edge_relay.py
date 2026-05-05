#!/usr/bin/env python3

import json
import math
import ssl
import threading
import time

import rospy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, LaserScan
from std_msgs.msg import Bool, Float32, String

try:
    import websocket
except ImportError:  # pragma: no cover
    websocket = None


class EdgeRelay:
    def __init__(self):
        self.url = rospy.get_param("~url", "wss://api.hzhhds.top/edge/ros")
        self.fallback_url = rospy.get_param("~fallback_url", "ws://10.156.250.190:3000/edge/ros")
        self.primary_failures_before_fallback = int(rospy.get_param("~primary_failures_before_fallback", 3))
        self.device_id = rospy.get_param("~device_id", "csrpi-001")
        self.device_token = rospy.get_param("~device_token", "")
        self.heartbeat_ms = int(rospy.get_param("~heartbeat_ms", 5000))
        self.odom_hz = float(rospy.get_param("~odom_hz", 5.0))
        self.imu_hz = float(rospy.get_param("~imu_hz", 5.0))
        self.scan_hz = float(rospy.get_param("~scan_hz", 1.0))
        self.cmd_repeat_hz = float(rospy.get_param("~cmd_repeat_hz", 10.0))
        self.default_hold_ms = int(rospy.get_param("~default_hold_ms", 400))
        self.reconnect_delay_ms = int(rospy.get_param("~reconnect_delay_ms", 1000))
        self.scan_danger_threshold = float(rospy.get_param("~scan_danger_threshold", 0.35))

        self.max_vx = 0.20
        self.max_vy = 0.15
        self.max_wz = 0.35

        self.ws = None
        self.ws_lock = threading.Lock()
        self.connected = False
        self.hello_acked = False
        self.recv_thread = None
        self.stop_event = threading.Event()
        self.active_url = self.url
        self.primary_connect_failures = 0
        self.last_odom = None
        self.last_imu = None
        self.last_scan = None
        self.last_fans_enabled = False
        self.last_fan_a_pwm = 0.0
        self.last_fan_b_pwm = 0.0
        self.last_fan_a_rpm = 0.0
        self.last_fan_b_rpm = 0.0
        self.last_fan_lid_open = False
        self.last_fan_summary = ""
        self.last_heartbeat_sent = 0.0
        self.last_telemetry_sent = 0.0
        self.cmd_hold_until = 0.0
        self.cmd_message = Twist()
        self.stop_requested = False

        self.cmd_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=20)
        self.fans_enable_pub = rospy.Publisher("/fans/enable", Bool, queue_size=10)
        self.fan_a_pwm_pub = rospy.Publisher("/fan_a/pwm_percent", Float32, queue_size=10)
        self.fan_b_pwm_pub = rospy.Publisher("/fan_b/pwm_percent", Float32, queue_size=10)
        rospy.Subscriber("/odom", Odometry, self.odom_callback, queue_size=20)
        rospy.Subscriber("/imu/data", Imu, self.imu_callback, queue_size=20)
        rospy.Subscriber("/scan", LaserScan, self.scan_callback, queue_size=5)
        rospy.Subscriber("/fans/enable", Bool, self.fans_enable_callback, queue_size=10)
        rospy.Subscriber("/fan_a/pwm_percent", Float32, self.fan_a_pwm_callback, queue_size=10)
        rospy.Subscriber("/fan_b/pwm_percent", Float32, self.fan_b_pwm_callback, queue_size=10)
        rospy.Subscriber("/fan_a/rpm", Float32, self.fan_a_rpm_callback, queue_size=10)
        rospy.Subscriber("/fan_b/rpm", Float32, self.fan_b_rpm_callback, queue_size=10)
        rospy.Subscriber("/fan_lid/state", Bool, self.fan_lid_state_callback, queue_size=10)
        rospy.Subscriber("/fans/state_summary", String, self.fan_summary_callback, queue_size=10)

    def clamp(self, value, lower, upper):
        if value < lower:
            return lower
        if value > upper:
            return upper
        return value

    def now_ms(self):
        return int(time.time() * 1000)

    def odom_callback(self, msg):
        self.last_odom = msg

    def imu_callback(self, msg):
        self.last_imu = msg

    def scan_callback(self, msg):
        self.last_scan = msg

    def fans_enable_callback(self, msg):
        self.last_fans_enabled = bool(msg.data)

    def fan_a_pwm_callback(self, msg):
        self.last_fan_a_pwm = float(msg.data)

    def fan_b_pwm_callback(self, msg):
        self.last_fan_b_pwm = float(msg.data)

    def fan_a_rpm_callback(self, msg):
        self.last_fan_a_rpm = float(msg.data)

    def fan_b_rpm_callback(self, msg):
        self.last_fan_b_rpm = float(msg.data)

    def fan_lid_state_callback(self, msg):
        self.last_fan_lid_open = bool(msg.data)

    def fan_summary_callback(self, msg):
        self.last_fan_summary = msg.data

    def odom_payload(self):
        if self.last_odom is None:
            return None
        msg = self.last_odom
        return {
            "x": msg.pose.pose.position.x,
            "y": msg.pose.pose.position.y,
            "vx": msg.twist.twist.linear.x,
            "vy": msg.twist.twist.linear.y,
            "wz": msg.twist.twist.angular.z,
        }

    def imu_payload(self):
        if self.last_imu is None:
            return None
        msg = self.last_imu
        return {
            "ax": msg.linear_acceleration.x,
            "ay": msg.linear_acceleration.y,
            "az": msg.linear_acceleration.z,
            "gx": msg.angular_velocity.x,
            "gy": msg.angular_velocity.y,
            "gz": msg.angular_velocity.z,
        }

    def scan_summary_payload(self):
        if self.last_scan is None or not self.last_scan.ranges:
            return None

        ranges = [r for r in self.last_scan.ranges if math.isfinite(r)]
        if not ranges:
            return {
                "frontMin": None,
                "leftMin": None,
                "rightMin": None,
                "danger": False,
                "buckets": [],
            }

        count = len(self.last_scan.ranges)

        def sector_min(center_deg, half_width_deg):
            values = []
            for idx, value in enumerate(self.last_scan.ranges):
                if not math.isfinite(value):
                    continue
                angle_deg = math.degrees(self.last_scan.angle_min + idx * self.last_scan.angle_increment)
                if self.angle_distance_deg(angle_deg, center_deg) <= half_width_deg:
                    values.append(value)
            return min(values) if values else None

        front_min = sector_min(0.0, 25.0)
        left_min = sector_min(90.0, 25.0)
        right_min = sector_min(-90.0, 25.0)

        buckets = []
        bucket_count = 12
        bucket_size = max(1, count // bucket_count)
        for idx in range(bucket_count):
            start = idx * bucket_size
            end = min(count, start + bucket_size)
            chunk = [r for r in self.last_scan.ranges[start:end] if math.isfinite(r)]
            buckets.append(min(chunk) if chunk else None)

        min_range = min(ranges)
        return {
            "frontMin": front_min,
            "leftMin": left_min,
            "rightMin": right_min,
            "danger": min_range < self.scan_danger_threshold,
            "buckets": buckets,
        }

    def angle_distance_deg(self, a, b):
        return abs(((a - b + 180.0) % 360.0) - 180.0)

    def hello_payload(self):
        return {
            "op": "hello",
            "deviceId": self.device_id,
            "token": self.device_token,
            "transport": "edge-relay",
            "topics": {
                "cmd_vel": "/cmd_vel",
                "odom": "/odom",
                "imu": "/imu/data",
                "scan": "/scan",
            },
            "capabilities": ["manual_control", "odom", "imu", "scan_summary"],
        }

    def heartbeat_payload(self):
        return {
            "op": "heartbeat",
            "deviceId": self.device_id,
            "ts": self.now_ms(),
        }

    def telemetry_payload(self):
        return {
            "op": "telemetry",
            "deviceId": self.device_id,
            "odom": self.odom_payload(),
            "imu": self.imu_payload(),
            "scanSummary": self.scan_summary_payload(),
            "fans": self.fan_payload(),
            "ts": self.now_ms(),
        }

    def fan_payload(self):
        return {
            "enabled": self.last_fans_enabled,
            "fanA": {
                "pwm": self.last_fan_a_pwm,
                "rpm": self.last_fan_a_rpm,
            },
            "fanB": {
                "pwm": self.last_fan_b_pwm,
                "rpm": self.last_fan_b_rpm,
            },
            "lidOpen": self.last_fan_lid_open,
            "summary": self.last_fan_summary,
        }

    def send_json(self, payload):
        body = json.dumps(payload, separators=(",", ":"))
        with self.ws_lock:
            if self.ws is None:
                return
            self.ws.send(body)

    def select_connect_url(self):
        if self.fallback_url and self.primary_connect_failures >= max(1, self.primary_failures_before_fallback):
            return self.fallback_url
        return self.url

    def log_ws_closed(self, exc):
        code = getattr(exc, "status_code", None)
        reason = getattr(exc, "reason", None)
        if code is None and hasattr(exc, "args") and exc.args:
            reason = exc.args[0]
        rospy.logwarn("edge relay websocket closed: code=%s reason=%s", str(code), str(reason))

    def handle_message(self, text):
        try:
            payload = json.loads(text)
        except ValueError:
            rospy.logwarn("edge relay received invalid json: %s", text)
            return

        op = payload.get("op")
        if op == "hello_ack":
            accepted = bool(payload.get("accepted", False))
            self.hello_acked = accepted
            rospy.loginfo("edge relay hello_ack accepted=%s deviceId=%s", accepted, payload.get("deviceId"))
        elif op == "manual_control":
            vx = self.clamp(float(payload.get("vx", 0.0)), -self.max_vx, self.max_vx)
            vy = self.clamp(float(payload.get("vy", 0.0)), -self.max_vy, self.max_vy)
            wz = self.clamp(float(payload.get("wz", 0.0)), -self.max_wz, self.max_wz)
            hold_ms = self.safe_hold_ms(payload)
            self.cmd_message.linear.x = vx
            self.cmd_message.linear.y = vy
            self.cmd_message.angular.z = wz
            self.cmd_hold_until = time.time() + (max(0, hold_ms) / 1000.0)
            self.stop_requested = False
        elif op == "stop":
            self.stop_requested = True
            self.cmd_hold_until = 0.0
            self.cmd_message = Twist()
        elif op == "fan_enable":
            self.fans_enable_pub.publish(Bool(data=bool(payload.get("enabled", False))))
        elif op == "fan_pwm":
            fan_a = self.clamp(float(payload.get("fanA", 0.0)), 0.0, 100.0)
            fan_b = self.clamp(float(payload.get("fanB", 0.0)), 0.0, 100.0)
            self.fan_a_pwm_pub.publish(Float32(data=fan_a))
            self.fan_b_pwm_pub.publish(Float32(data=fan_b))

    def safe_hold_ms(self, payload):
        try:
            hold_ms = int(payload.get("holdMs", self.default_hold_ms))
        except (TypeError, ValueError):
            hold_ms = self.default_hold_ms
        return max(0, min(hold_ms, self.default_hold_ms))

    def recv_loop(self):
        while not rospy.is_shutdown() and not self.stop_event.is_set():
            try:
                with self.ws_lock:
                    active_ws = self.ws
                if active_ws is None:
                    time.sleep(0.1)
                    continue
                message = active_ws.recv()
                if not message:
                    raise RuntimeError("websocket closed by peer")
                if message:
                    self.handle_message(message)
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as exc:  # pragma: no cover
                self.log_ws_closed(exc)
                self.close_ws()
                return

    def close_ws(self):
        self.connected = False
        self.hello_acked = False
        self.stop_event.set()
        with self.ws_lock:
            if self.ws is not None:
                try:
                    self.ws.close()
                except Exception:
                    pass
                self.ws = None

    def connect(self):
        if websocket is None:
            raise RuntimeError(
                "python websocket client dependency missing; install python3-websocket"
            )

        headers = []
        if self.device_token:
            headers.append(f"Authorization: Bearer {self.device_token}")

        self.stop_event = threading.Event()
        self.active_url = self.select_connect_url()
        self.ws = websocket.create_connection(
            self.active_url,
            header=headers,
            sslopt={"cert_reqs": ssl.CERT_REQUIRED},
            timeout=1,
        )
        self.connected = True
        self.hello_acked = False
        if self.active_url == self.url:
            self.primary_connect_failures = 0
        self.send_json(self.hello_payload())
        self.recv_thread = threading.Thread(target=self.recv_loop, daemon=True)
        self.recv_thread.start()

    def command_tick(self):
        now = time.time()
        msg = Twist()
        if not self.stop_requested and now < self.cmd_hold_until:
            msg = self.cmd_message
        self.cmd_pub.publish(msg)

    def telemetry_tick(self):
        if not self.hello_acked:
            return

        now = time.time()

        if now - self.last_heartbeat_sent >= (self.heartbeat_ms / 1000.0):
            self.send_json(self.heartbeat_payload())
            self.last_heartbeat_sent = now

        min_period = 1.0 / max(self.odom_hz, self.imu_hz, self.scan_hz)
        if now - self.last_telemetry_sent >= min_period:
            self.send_json(self.telemetry_payload())
            self.last_telemetry_sent = now

    def spin(self):
        reconnect_delay = max(1.0, self.reconnect_delay_ms / 1000.0)
        cmd_rate = rospy.Rate(self.cmd_repeat_hz)
        while not rospy.is_shutdown():
            try:
                if self.ws is None:
                    target_url = self.select_connect_url()
                    rospy.loginfo("edge relay connecting to %s", target_url)
                    self.connect()
                    reconnect_delay = max(1.0, self.reconnect_delay_ms / 1000.0)
                    self.last_heartbeat_sent = 0.0
                    self.last_telemetry_sent = 0.0

                if self.ws is None:
                    raise RuntimeError("websocket unavailable after connect")

                self.command_tick()
                self.telemetry_tick()
                cmd_rate.sleep()
            except Exception as exc:  # pragma: no cover
                if self.ws is None and self.active_url == self.url:
                    self.primary_connect_failures += 1
                    if self.fallback_url and self.primary_connect_failures >= max(1, self.primary_failures_before_fallback):
                        rospy.logwarn(
                            "edge relay primary endpoint failed %d times, switching to fallback %s",
                            self.primary_connect_failures,
                            self.fallback_url,
                        )
                rospy.logwarn("edge relay reconnect pending: %s", str(exc))
                self.close_ws()
                self.cmd_pub.publish(Twist())
                rospy.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2.0, 30.0)

        self.cmd_pub.publish(Twist())
        self.close_ws()


def main():
    rospy.init_node("edge_relay")
    EdgeRelay().spin()


if __name__ == "__main__":
    main()
