SOF0 = 0x43
SOF1 = 0x4A
VERSION = 0x01
MAX_PAYLOAD = 16

TYPE_COLOR_FOUND = 0x10
TYPE_ARM_BUSY = 0x11
TYPE_PICK_DONE = 0x12
TYPE_PICK_TIMEOUT = 0x13
TYPE_ARM_FAIL = 0x14
TYPE_HEARTBEAT = 0x15
TYPE_ACK = 0x80
TYPE_PICK_WINDOW = 0x81
TYPE_ABORT = 0x82
TYPE_PING = 0x83


def crc8_atm(data):
    crc = 0
    for value in data:
        crc ^= value
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


class CjLink:
    def __init__(self, uart):
        self.uart = uart
        self.seq = 1
        self.rx = bytearray()

    def _send(self, frame_type, payload=b""):
        payload = bytes(payload)
        frame = bytearray([SOF0, SOF1, VERSION, self.seq & 0xFF, frame_type & 0xFF, len(payload) & 0xFF])
        frame.extend(payload)
        frame.append(crc8_atm(frame[2:]))
        self.uart.write(frame)
        self.seq = (self.seq + 1) & 0xFF

    def send_color_found(self, color_id):
        self._send(TYPE_COLOR_FOUND, bytes([color_id & 0xFF]))

    def send_arm_busy(self, state=1):
        self._send(TYPE_ARM_BUSY, bytes([state & 0xFF]))

    def send_pick_done(self, color_id):
        self._send(TYPE_PICK_DONE, bytes([color_id & 0xFF]))

    def send_pick_timeout(self, color_id):
        self._send(TYPE_PICK_TIMEOUT, bytes([color_id & 0xFF]))

    def send_arm_fail(self, reason):
        self._send(TYPE_ARM_FAIL, bytes([reason & 0xFF]))

    def send_heartbeat(self, state):
        self._send(TYPE_HEARTBEAT, bytes([state & 0xFF]))

    def send_ack(self, seq, frame_type):
        self._send(TYPE_ACK, bytes([seq & 0xFF, frame_type & 0xFF]))

    def _extract_frame(self):
        while len(self.rx) >= 2:
            if self.rx[0] == SOF0 and self.rx[1] == SOF1:
                break
            del self.rx[0]

        if len(self.rx) < 7:
            return None

        payload_len = self.rx[5]
        frame_len = 7 + payload_len
        if payload_len > MAX_PAYLOAD:
            del self.rx[0]
            return None

        if len(self.rx) < frame_len:
            return None

        frame = self.rx[:frame_len]
        del self.rx[:frame_len]

        if frame[2] != VERSION:
            return None

        if crc8_atm(frame[2:-1]) != frame[-1]:
            return None

        return {
            "version": frame[2],
            "seq": frame[3],
            "type": frame[4],
            "payload": bytes(frame[6:-1]),
        }

    def poll(self):
        frames = []
        while self.uart.any():
            self.rx.append(self.uart.readchar())
            parsed = self._extract_frame()
            while parsed is not None:
                frames.append(parsed)
                parsed = self._extract_frame()
        return frames