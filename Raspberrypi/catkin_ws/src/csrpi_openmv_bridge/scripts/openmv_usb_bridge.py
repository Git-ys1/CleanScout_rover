#!/usr/bin/env python3

import threading
import time

import rospy
import serial
from std_msgs.msg import Empty, Int32, String


class OpenMvUsbBridge:
    def __init__(self):
        self.port = rospy.get_param("~port", "/dev/ttyACM0")
        self.baudrate = int(rospy.get_param("~baudrate", 115200))
        self.read_timeout = float(rospy.get_param("~read_timeout", 0.2))
        self.write_timeout = float(rospy.get_param("~write_timeout", 0.5))
        self.reconnect_delay = float(rospy.get_param("~reconnect_delay", 1.0))
        self.offline_timeout = float(rospy.get_param("~offline_timeout", 1.0))

        self.serial_handle = None
        self.serial_lock = threading.Lock()
        self.online = False
        self.last_line_time = 0.0

        self.status_raw_pub = rospy.Publisher("/openmv/status_raw", String, queue_size=50)
        self.event_pub = rospy.Publisher("/openmv/event", String, queue_size=20)
        self.ack_pub = rospy.Publisher("/openmv/ack", String, queue_size=20)
        self.error_pub = rospy.Publisher("/openmv/error", String, queue_size=20)
        self.status_pub = rospy.Publisher("/openmv/status", String, queue_size=20)
        self.online_pub = rospy.Publisher("/openmv/online", String, queue_size=5, latch=True)

        rospy.Subscriber("/openmv/cmd_mode", String, self.cmd_mode_callback, queue_size=10)
        rospy.Subscriber("/openmv/cmd_observe_tilt", Int32, self.cmd_observe_tilt_callback, queue_size=10)
        rospy.Subscriber("/openmv/cmd_ping", Empty, self.cmd_ping_callback, queue_size=10)
        rospy.Subscriber("/openmv/cmd_status", Empty, self.cmd_status_callback, queue_size=10)

        self.reader_thread = threading.Thread(target=self.reader_loop, daemon=True)
        self.reader_thread.start()
        self.watchdog_timer = rospy.Timer(rospy.Duration(0.5), self.watchdog_callback)
        self.publish_online(False)

    def publish_online(self, online):
        self.online = online
        self.online_pub.publish(String(data="online" if online else "offline"))

    def connect(self):
        with self.serial_lock:
            if self.serial_handle and self.serial_handle.is_open:
                return True
            try:
                self.serial_handle = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.read_timeout,
                    write_timeout=self.write_timeout,
                )
                rospy.loginfo("[openmv-bridge] serial connected: %s", self.port)
                return True
            except Exception as exc:
                rospy.logwarn_throttle(5.0, "[openmv-bridge] serial connect failed: %s", exc)
                self.serial_handle = None
                return False

    def disconnect(self):
        with self.serial_lock:
            if self.serial_handle is not None:
                try:
                    self.serial_handle.close()
                except Exception:
                    pass
            self.serial_handle = None
        self.publish_online(False)

    def send_line(self, line):
        with self.serial_lock:
            if self.serial_handle is None or not self.serial_handle.is_open:
                rospy.logwarn("[openmv-bridge] send skipped, serial offline: %s", line)
                return
            payload = (line + "\n").encode("utf-8")
            self.serial_handle.write(payload)
            self.serial_handle.flush()
            rospy.loginfo("[openmv-bridge] tx: %s", line)

    def cmd_mode_callback(self, msg):
        self.send_line(f"MODE,{msg.data.strip()}")

    def cmd_observe_tilt_callback(self, msg):
        self.send_line(f"OBS_TILT,{int(msg.data)}")

    def cmd_ping_callback(self, _msg):
        self.send_line("PING")

    def cmd_status_callback(self, _msg):
        self.send_line("STATUS")

    def handle_line(self, line):
        self.last_line_time = time.time()
        if not self.online:
            self.publish_online(True)

        self.status_raw_pub.publish(String(data=line))
        if line.startswith("EVENT,"):
            self.event_pub.publish(String(data=line))
        elif line.startswith("ACK,"):
            self.ack_pub.publish(String(data=line))
        elif line.startswith("ERR,"):
            self.error_pub.publish(String(data=line))
        elif line.startswith("STATUS,"):
            self.status_pub.publish(String(data=line))

    def reader_loop(self):
        while not rospy.is_shutdown():
            if not self.connect():
                time.sleep(self.reconnect_delay)
                continue

            try:
                raw = self.serial_handle.readline()
                if not raw:
                    time.sleep(0.02)
                    continue
                line = raw.decode("utf-8", errors="replace").strip()
                if line:
                    rospy.loginfo("[openmv-bridge] rx: %s", line)
                    self.handle_line(line)
            except Exception as exc:
                rospy.logwarn("[openmv-bridge] serial read failed: %s", exc)
                self.disconnect()
                time.sleep(self.reconnect_delay)

    def watchdog_callback(self, _event):
        if self.last_line_time <= 0.0:
            return
        if time.time() - self.last_line_time > self.offline_timeout:
            self.publish_online(False)

    def shutdown(self):
        self.watchdog_timer.shutdown()
        self.disconnect()


def main():
    rospy.init_node("openmv_usb_bridge")
    bridge = OpenMvUsbBridge()
    rospy.on_shutdown(bridge.shutdown)
    rospy.spin()


if __name__ == "__main__":
    main()
