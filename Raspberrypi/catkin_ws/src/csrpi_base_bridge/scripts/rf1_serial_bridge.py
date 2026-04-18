#!/usr/bin/env python3

import threading
import time

import rospy
import serial
from std_msgs.msg import Bool, Float32MultiArray, Int16MultiArray, Int32MultiArray, String


class Rf1SerialBridge:
    def __init__(self):
        self.port = rospy.get_param(
            "~port",
            "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0",
        )
        self.fallback_port = rospy.get_param("~fallback_port", "/dev/ttyUSB0")
        self.baudrate = int(rospy.get_param("~baudrate", 115200))
        self.timeout = float(rospy.get_param("~timeout", 0.2))
        self.send_rate_hz = float(rospy.get_param("~send_rate_hz", 50.0))
        self.reconnect_delay = float(rospy.get_param("~reconnect_delay", 1.0))
        self.drain_seconds = float(rospy.get_param("~drain_seconds", 0.6))
        self.stop_burst_count = int(rospy.get_param("~stop_burst_count", 3))
        self.default_targets = self.normalize_targets(
            rospy.get_param("~default_targets", [0.0, 0.0, 0.0, 0.0])
        )

        self.serial_conn = None
        self.serial_lock = threading.Lock()
        self.ready_seen = False
        self.last_targets = self.default_targets
        self.last_rx_time = 0.0

        self.ready_pub = rospy.Publisher("/rf1/ready", Bool, queue_size=10, latch=True)
        self.raw_pub = rospy.Publisher("/rf1/raw_rx", String, queue_size=100)
        self.vel_pub = rospy.Publisher("/rf1/vel", Float32MultiArray, queue_size=20)
        self.pwm_pub = rospy.Publisher("/rf1/pwm", Int16MultiArray, queue_size=20)
        self.enc_pub = rospy.Publisher("/rf1/enc", Int32MultiArray, queue_size=20)
        self.dbg_pub = rospy.Publisher("/rf1/dbg", String, queue_size=20)
        self.status_pub = rospy.Publisher("/rf1/status", String, queue_size=20, latch=True)
        self.ack_pub = rospy.Publisher("/rf1/ack", String, queue_size=20)
        self.err_pub = rospy.Publisher("/rf1/error", String, queue_size=20)

        rospy.Subscriber(
            "/rf1/wheel_target_ms",
            Float32MultiArray,
            self.targets_callback,
            queue_size=20,
        )

        self.publish_ready(False)

    def normalize_targets(self, values):
        if len(values) != 4:
            raise ValueError("rf1 wheel target list must have exactly 4 values")
        return tuple(float(value) for value in values)

    def targets_callback(self, msg):
        if len(msg.data) != 4:
            rospy.logwarn("ignoring rf1 wheel target with %d entries", len(msg.data))
            return
        self.last_targets = self.normalize_targets(msg.data)

    def publish_ready(self, ready):
        self.ready_pub.publish(Bool(data=ready))

    def publish_status(self, text):
        rospy.loginfo(text)
        self.status_pub.publish(String(data=text))

    def candidate_ports(self):
        ports = []
        for port in (self.port, self.fallback_port):
            if port and port not in ports:
                ports.append(port)
        return ports

    def open_serial(self):
        last_error = None
        for port in self.candidate_ports():
            try:
                self.publish_status(f"connecting RF1 serial {port} @ {self.baudrate}")
                conn = serial.Serial(port, self.baudrate, timeout=self.timeout)
                conn.reset_input_buffer()
                conn.reset_output_buffer()
                self.port = port
                return conn
            except (OSError, serial.SerialException) as exc:
                last_error = exc
                self.publish_status(f"serial connect failed on {port}: {exc}")
        if last_error is None:
            raise serial.SerialException("no RF1 serial port configured")
        raise last_error

    def close_serial(self):
        with self.serial_lock:
            if self.serial_conn is not None:
                try:
                    self.serial_conn.close()
                except serial.SerialException:
                    pass
                self.serial_conn = None
        self.ready_seen = False
        self.publish_ready(False)

    def drain_after_open(self):
        deadline = time.time() + self.drain_seconds
        while not rospy.is_shutdown() and time.time() < deadline:
            line = self.read_line_once()
            if line is None:
                continue

    def ensure_connection(self):
        while not rospy.is_shutdown():
            if self.serial_conn is not None:
                return True
            try:
                self.close_serial()
                with self.serial_lock:
                    self.serial_conn = self.open_serial()
                self.drain_after_open()
                self.publish_status("RF1 serial connected")
                return True
            except (OSError, serial.SerialException) as exc:
                self.publish_status(f"RF1 serial reconnect pending: {exc}")
                self.close_serial()
            rospy.sleep(self.reconnect_delay)
        return False

    def parse_float_fields(self, fields):
        try:
            return [float(field) for field in fields]
        except ValueError:
            rospy.logwarn("unable to parse float serial line: %s", ",".join(fields))
            return None

    def parse_int_fields(self, fields):
        values = []
        try:
            for field in fields:
                values.append(int(round(float(field))))
        except ValueError:
            rospy.logwarn("unable to parse int serial line: %s", ",".join(fields))
            return None
        return values

    def handle_line(self, line):
        self.last_rx_time = time.time()
        self.raw_pub.publish(String(data=line))

        if line == "CSR_RF1_READY":
            self.ready_seen = True
            self.publish_ready(True)
            return

        if line.startswith("ACK:"):
            self.publish_ready(True)
            self.ack_pub.publish(String(data=line))
            return

        if line.startswith("ERR:"):
            self.err_pub.publish(String(data=line))
            self.publish_status(line)
            return

        parts = [part.strip() for part in line.split(",")]
        tag = parts[0] if parts else ""
        fields = parts[1:]

        if tag == "VEL":
            numeric = self.parse_float_fields(fields)
            if numeric is not None:
                self.publish_ready(True)
                self.vel_pub.publish(Float32MultiArray(data=numeric))
        elif tag == "PWM":
            numeric = self.parse_int_fields(fields)
            if numeric is not None:
                self.publish_ready(True)
                self.pwm_pub.publish(Int16MultiArray(data=numeric))
        elif tag == "ENC":
            numeric = self.parse_int_fields(fields)
            if numeric is not None:
                self.publish_ready(True)
                self.enc_pub.publish(Int32MultiArray(data=numeric))
        elif tag == "DBG":
            self.publish_ready(True)
            self.dbg_pub.publish(String(data=line))

    def read_line_once(self):
        read_error = None
        with self.serial_lock:
            conn = self.serial_conn
            if conn is None:
                return None
            try:
                raw = conn.readline()
            except serial.SerialException as exc:
                read_error = exc
                raw = None

        if read_error is not None:
            self.publish_status(f"RF1 serial read failed: {read_error}")
            self.close_serial()
            return None

        if not raw:
            return None

        line = raw.decode("utf-8", errors="replace").strip()
        if line:
            self.handle_line(line)
        return line

    def format_targets_frame(self, targets):
        a, b, c, d = targets
        return f"W,{a:.3f},{b:.3f},{c:.3f},{d:.3f}\n"

    def send_frame(self, frame):
        with self.serial_lock:
            conn = self.serial_conn
            if conn is None:
                raise serial.SerialException("RF1 serial not connected")
            conn.write(frame.encode("utf-8"))
            conn.flush()

    def send_stop_burst(self):
        if self.serial_conn is None:
            return
        for _ in range(max(1, self.stop_burst_count)):
            try:
                self.send_frame("STOP\n")
            except (AttributeError, serial.SerialException):
                self.close_serial()
                return
            time.sleep(0.05)

    def send_loop(self):
        rate = rospy.Rate(self.send_rate_hz)
        while not rospy.is_shutdown():
            if not self.ensure_connection():
                break

            frame = self.format_targets_frame(self.last_targets)
            try:
                self.send_frame(frame)
            except (AttributeError, serial.SerialException) as exc:
                self.publish_status(f"RF1 serial write failed: {exc}")
                self.close_serial()

            rate.sleep()

        self.send_stop_burst()

    def read_loop(self):
        while not rospy.is_shutdown():
            if self.serial_conn is None:
                rospy.sleep(0.05)
                continue
            self.read_line_once()

    def spin(self):
        rospy.on_shutdown(self.shutdown)
        reader = threading.Thread(target=self.read_loop, daemon=True)
        reader.start()
        self.send_loop()

    def shutdown(self):
        self.send_stop_burst()
        self.close_serial()


def main():
    rospy.init_node("rf1_serial_bridge")
    bridge = Rf1SerialBridge()
    bridge.spin()


if __name__ == "__main__":
    main()
