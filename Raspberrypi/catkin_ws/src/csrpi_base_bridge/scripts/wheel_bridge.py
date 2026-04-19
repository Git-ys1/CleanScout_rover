#!/usr/bin/env python3

import threading
import time

import rospy
import serial
from std_msgs.msg import Float32MultiArray, Int32MultiArray, String


class WheelBridge:
    def __init__(self):
        self.port = rospy.get_param("~port", "/dev/csr_uno")
        self.baudrate = int(rospy.get_param("~baudrate", 115200))
        self.send_rate_hz = float(rospy.get_param("~send_rate_hz", 20.0))
        self.reconnect_delay = float(rospy.get_param("~reconnect_delay", 1.0))
        self.ready_timeout = float(rospy.get_param("~ready_timeout", 8.0))
        self.default_targets = rospy.get_param("~default_targets", [0, 0, 0, 0])

        self.serial_conn = None
        self.serial_lock = threading.Lock()
        self.ready_seen = False
        self.last_targets = self.normalize_targets(self.default_targets)

        self.raw_pub = rospy.Publisher("/csr_base/raw_serial_line", String, queue_size=50)
        self.enc_pub = rospy.Publisher("/csr_base/encoder_debug", Float32MultiArray, queue_size=20)
        self.pid_pub = rospy.Publisher("/csr_base/pid_debug", Float32MultiArray, queue_size=20)
        self.status_pub = rospy.Publisher("/csr_base/bridge_status", String, queue_size=20, latch=True)
        self.ack_pub = rospy.Publisher("/csr_base/ack", String, queue_size=20)

        rospy.Subscriber("/csr_base/wheel_targets", Int32MultiArray, self.targets_callback, queue_size=20)

    def normalize_targets(self, values):
        if len(values) != 4:
            raise ValueError("wheel target list must have exactly 4 values")
        return tuple(int(value) for value in values)

    def targets_callback(self, msg):
        if len(msg.data) != 4:
            rospy.logwarn("ignoring wheel target with %d entries", len(msg.data))
            return
        self.last_targets = self.normalize_targets(msg.data)

    def publish_status(self, text):
        rospy.loginfo(text)
        self.status_pub.publish(String(data=text))

    def open_serial(self):
        self.publish_status(f"connecting serial {self.port} @ {self.baudrate}")
        conn = serial.Serial(self.port, self.baudrate, timeout=0.1)
        conn.reset_input_buffer()
        conn.reset_output_buffer()
        return conn

    def close_serial(self):
        with self.serial_lock:
            if self.serial_conn is not None:
                try:
                    self.serial_conn.close()
                except serial.SerialException:
                    pass
                self.serial_conn = None
        self.ready_seen = False

    def wait_ready(self):
        deadline = time.time() + self.ready_timeout
        while not rospy.is_shutdown() and time.time() < deadline:
            line = self.read_line_once()
            if not line:
                continue
            if line in ("CSR_UNO_READY", "READY"):
                self.ready_seen = True
                self.publish_status(f"received {line}")
                return True
        self.publish_status("ready timeout, reconnecting")
        return False

    def ensure_connection(self):
        while not rospy.is_shutdown():
            if self.serial_conn is not None and self.ready_seen:
                return True

            try:
                self.close_serial()
                with self.serial_lock:
                    self.serial_conn = self.open_serial()
                if self.wait_ready():
                    self.publish_status("serial connected")
                    return True
            except (OSError, serial.SerialException) as exc:
                self.publish_status(f"serial connect failed: {exc}")
                self.close_serial()

            rospy.sleep(self.reconnect_delay)
        return False

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
            self.publish_status(f"serial read failed: {read_error}")
            self.close_serial()
            return None

        if not raw:
            return None

        line = raw.decode("utf-8", errors="replace").strip()
        if line:
            self.handle_line(line)
        return line

    def handle_line(self, line):
        self.raw_pub.publish(String(data=line))

        if line in ("CSR_UNO_READY", "READY"):
            self.ready_seen = True
            return

        if line == "ACK:W":
            self.ack_pub.publish(String(data=line))
            return

        parts = [part.strip() for part in line.split(",")]
        tag = parts[0] if parts else ""

        if tag == "ENC":
            numeric = self.parse_numeric_fields(parts[1:])
            if numeric is not None:
                self.enc_pub.publish(Float32MultiArray(data=numeric))
        elif tag == "PID":
            numeric = self.parse_numeric_fields(parts[1:])
            if numeric is not None:
                self.pid_pub.publish(Float32MultiArray(data=numeric))
        elif tag.startswith("ERR"):
            self.publish_status(line)

    def parse_numeric_fields(self, fields):
        values = []
        try:
            for field in fields:
                values.append(float(field))
        except ValueError:
            rospy.logwarn("unable to parse numeric serial line: %s", ",".join(fields))
            return None
        return values

    def send_loop(self):
        rate = rospy.Rate(self.send_rate_hz)
        while not rospy.is_shutdown():
            if not self.ensure_connection():
                break

            w1, w2, w3, w4 = self.last_targets
            frame = f"W,{w1},{w2},{w3},{w4}\n"

            with self.serial_lock:
                conn = self.serial_conn
                try:
                    conn.write(frame.encode("utf-8"))
                    conn.flush()
                except (AttributeError, serial.SerialException) as exc:
                    write_error = exc
                else:
                    write_error = None

            if write_error is not None:
                self.publish_status(f"serial write failed: {write_error}")
                self.close_serial()

            rate.sleep()

    def read_loop(self):
        while not rospy.is_shutdown():
            if self.serial_conn is None:
                rospy.sleep(0.05)
                continue
            self.read_line_once()

    def spin(self):
        reader = threading.Thread(target=self.read_loop, daemon=True)
        reader.start()
        self.send_loop()


def main():
    rospy.init_node("csrpi_wheel_bridge")
    bridge = WheelBridge()
    bridge.spin()


if __name__ == "__main__":
    main()
