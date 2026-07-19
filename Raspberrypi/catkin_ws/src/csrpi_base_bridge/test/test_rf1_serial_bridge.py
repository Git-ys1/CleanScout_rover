#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import threading
import time
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rf1_serial_bridge.py"
SPEC = importlib.util.spec_from_file_location("rf1_serial_bridge", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BlockingSerial:
    def __init__(self):
        self.read_started = threading.Event()
        self.release_read = threading.Event()
        self.writes = []

    def readline(self):
        self.read_started.set()
        self.release_read.wait(timeout=0.3)
        return b""

    def write(self, payload):
        self.writes.append(payload)

    def flush(self):
        pass

    def close(self):
        self.release_read.set()


class Rf1SerialBridgeLockTest(unittest.TestCase):
    def make_bridge(self, conn):
        bridge = MODULE.Rf1SerialBridge.__new__(MODULE.Rf1SerialBridge)
        bridge.serial_conn = conn
        bridge.connection_lock = threading.Lock()
        bridge.serial_read_lock = threading.Lock()
        bridge.serial_write_lock = threading.Lock()
        return bridge

    def test_blocking_read_does_not_delay_writes(self):
        conn = BlockingSerial()
        bridge = self.make_bridge(conn)
        reader = threading.Thread(target=bridge.read_line_once)
        reader.start()
        self.assertTrue(conn.read_started.wait(timeout=0.1))

        started = time.monotonic()
        bridge.send_frame("W,0.000,0.000,0.000,0.000\n")
        elapsed = time.monotonic() - started

        conn.release_read.set()
        reader.join(timeout=0.5)
        self.assertLess(elapsed, 0.1)
        self.assertEqual(conn.writes, [b"W,0.000,0.000,0.000,0.000\n"])

    def test_stale_read_error_cannot_close_new_connection(self):
        old_conn = BlockingSerial()
        new_conn = BlockingSerial()
        bridge = self.make_bridge(new_conn)

        bridge.close_serial(expected_conn=old_conn)

        self.assertIs(bridge.current_connection(), new_conn)


if __name__ == "__main__":
    unittest.main()
