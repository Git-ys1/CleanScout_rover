from pyb import millis


CMD_STOP = 0x00
CMD_TILT_UP = 0x01
CMD_TILT_DOWN = 0x02
CMD_PAN_LEFT = 0x03
CMD_PAN_RIGHT = 0x04
CMD_CLAW_OPEN = 0x0A
CMD_CLAW_CLOSE = 0x0B
CMD_CENTER = 0x0C
CMD_DEMO_LOOP_START = 0x0D


COMMAND_NAMES = {
    CMD_STOP: "STOP",
    CMD_TILT_UP: "TILT_UP",
    CMD_TILT_DOWN: "TILT_DOWN",
    CMD_PAN_LEFT: "PAN_LEFT",
    CMD_PAN_RIGHT: "PAN_RIGHT",
    CMD_CLAW_OPEN: "CLAW_OPEN",
    CMD_CLAW_CLOSE: "CLAW_CLOSE",
    CMD_CENTER: "CENTER",
    CMD_DEMO_LOOP_START: "DEMO_LOOP_START",
}


def command_name(command):
    return COMMAND_NAMES.get(command, "UNKNOWN")


class InjectedCommandSource:
    def __init__(self):
        self._queue = []

    def push(self, command):
        self._queue.append(command)

    def next_command(self, now_ms):
        _ = now_ms
        if not self._queue:
            return None
        return self._queue.pop(0)


class DemoLoopSource:
    def __init__(self, loop_pause_ms):
        self.loop_pause_ms = loop_pause_ms
        self.sequence = self._build_sequence()
        self.index = 0
        self.next_due_ms = millis()

    def _build_sequence(self):
        sequence = [CMD_DEMO_LOOP_START, CMD_CENTER]
        sequence += [CMD_TILT_UP] * 5
        sequence += [CMD_TILT_DOWN] * 10
        sequence += [CMD_CENTER]
        sequence += [CMD_PAN_LEFT] * 5
        sequence += [CMD_PAN_RIGHT] * 10
        sequence += [CMD_CENTER, CMD_CLAW_CLOSE, CMD_CLAW_OPEN]
        return sequence

    def next_command(self, now_ms):
        if now_ms < self.next_due_ms:
            return None

        command = self.sequence[self.index]
        self.index += 1

        if self.index >= len(self.sequence):
            self.index = 0
            self.next_due_ms = now_ms + self.loop_pause_ms
        else:
            self.next_due_ms = now_ms

        return command
