"""Host-side replay/fuzz contract tests for the combined firmware protocols."""

from __future__ import annotations

import random
import re
import unittest

SERVO_MIN = 500
SERVO_MAX = 2490


def parse_motion(line: str) -> tuple[str, tuple[object, ...]]:
    fields = line.rstrip("\r\n").split(",")
    if fields == ["STOP"]:
        return "STOP", ()
    if fields == ["ESTOP"]:
        return "ESTOP", ()
    if fields == ["CLEAR_ESTOP"]:
        return "CLEAR_ESTOP", ()
    if fields == ["INFO"]:
        return "INFO", ()
    if len(fields) == 5 and fields[0] == "W":
        return "W", tuple(float(value) for value in fields[1:])
    if len(fields) == 2 and fields[0] in {"E", "D"}:
        channel = int(fields[1])
        if not 1 <= channel <= 4:
            raise ValueError("channel")
        return fields[0], (channel,)
    if len(fields) == 3 and fields[0] == "M":
        channel = int(fields[1])
        pwm = int(fields[2])
        if not 1 <= channel <= 4 or not -1000 <= pwm <= 1000:
            raise ValueError("range")
        return "M", (channel, pwm)
    raise ValueError("bad_prefix")


MOVE_RE = re.compile(r"#(?P<id>\d{3})P(?P<pwm>\d{4})T(?P<time>\d{4})!")
STOP_RE = re.compile(r"#(?P<id>\d{3})PDST!")
QUERY_RE = re.compile(r"#(?P<id>\d{3})PRAD!")


def _check_id(value: int) -> None:
    if not 0 <= value <= 5:
        raise ValueError("LIMIT")


def _parse_move(frame: str) -> tuple[int, int, int]:
    match = MOVE_RE.fullmatch(frame)
    if not match:
        raise ValueError("BAD_FRAME")
    servo_id = int(match.group("id"))
    pwm = int(match.group("pwm"))
    duration = int(match.group("time"))
    _check_id(servo_id)
    if not SERVO_MIN <= pwm <= SERVO_MAX:
        raise ValueError("LIMIT")
    return servo_id, pwm, duration


def parse_arm(frame: str) -> tuple[str, tuple[object, ...]]:
    special = {
        "@HELLO:ARM_V2!": "HELLO",
        "@INFO!": "INFO",
        "@DIAG!": "DIAG",
        "@PING!": "PING",
        "@ESTOP!": "ESTOP",
        "@CLEAR:ESTOP!": "CLEAR_ESTOP",
    }
    if frame in special:
        return special[frame], ()
    if frame.startswith("$"):
        raise ValueError("UNSUPPORTED")
    if frame.startswith("{"):
        if not frame.endswith("}"):
            raise ValueError("BAD_FRAME")
        payload = frame[1:-1]
        moves = []
        offset = 0
        while offset < len(payload):
            move = payload[offset : offset + 15]
            if len(move) != 15:
                raise ValueError("BAD_FRAME")
            moves.append(_parse_move(move))
            offset += 15
        if not 1 <= len(moves) <= 6 or len({move[0] for move in moves}) != len(moves):
            raise ValueError("BAD_FRAME")
        return "MOVE_GROUP", tuple(moves)
    if frame.startswith("#"):
        move = MOVE_RE.fullmatch(frame)
        if move:
            return "MOVE", (_parse_move(frame),)
        stop = STOP_RE.fullmatch(frame)
        if stop:
            servo_id = int(stop.group("id"))
            _check_id(servo_id)
            return "STOP", (servo_id,)
        query = QUERY_RE.fullmatch(frame)
        if query:
            servo_id = int(query.group("id"))
            _check_id(servo_id)
            return "QUERY", (servo_id,)
    raise ValueError("BAD_FRAME")


def normalize_bus_response(stream: bytes) -> bytes:
    """UART5 resynchronizes on the newest '#', matching the firmware RX FSM."""
    frame = bytearray()
    for value in stream:
        if value == ord("#"):
            frame[:] = b"#"
        elif frame:
            frame.append(value)
            if value == ord("!"):
                return bytes(frame)
    raise ValueError("incomplete")


class ProtocolContractTests(unittest.TestCase):
    def test_motion_legacy_contract(self) -> None:
        self.assertEqual(parse_motion("W,0.1,-0.2,0.3,-0.4\n")[0], "W")
        self.assertEqual(parse_motion("M,4,-1000\n"), ("M", (4, -1000)))
        self.assertEqual(parse_motion("E,1\n"), ("E", (1,)))
        self.assertEqual(parse_motion("D,4\n"), ("D", (4,)))
        self.assertEqual(parse_motion("STOP\n"), ("STOP", ()))

    def test_cross_uart_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_motion("#000P1500T0200!\n")
        with self.assertRaises(ValueError):
            parse_arm("W,0,0,0,0\n")

    def test_arm_single_group_stop_query(self) -> None:
        self.assertEqual(parse_arm("#000P1500T0200!")[0], "MOVE")
        self.assertEqual(
            parse_arm("{#000P1500T0200!#001P1600T0200!}")[0],
            "MOVE_GROUP",
        )
        self.assertEqual(parse_arm("#003PDST!"), ("STOP", (3,)))
        self.assertEqual(parse_arm("#005PRAD!"), ("QUERY", (5,)))
        self.assertEqual(len("#003PDST!"), 9)
        self.assertEqual(len("#005PRAD!"), 9)

    def test_arm_bounds_and_broadcast_rejected(self) -> None:
        parse_arm("#000P0500T0000!")
        parse_arm("#005P2490T9999!")
        for frame in ("#000P0499T0000!", "#000P2500T0000!", "#255PDST!"):
            with self.assertRaises(ValueError):
                parse_arm(frame)

    def test_group_is_atomic_and_rejects_duplicates(self) -> None:
        with self.assertRaises(ValueError):
            parse_arm("{#000P1500T0200!#001P9999T0200!}")
        with self.assertRaises(ValueError):
            parse_arm("{#000P1500T0200!#000P1600T0200!}")

    def test_v2_and_unsupported(self) -> None:
        self.assertEqual(parse_arm("@HELLO:ARM_V2!"), ("HELLO", ()))
        self.assertEqual(parse_arm("@PING!"), ("PING", ()))
        self.assertEqual(parse_arm("@DIAG!"), ("DIAG", ()))
        self.assertEqual(parse_arm("@ESTOP!"), ("ESTOP", ()))
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED"):
            parse_arm("$KMS:1,2,3!")

    def test_uart5_duplicate_hash_resynchronization(self) -> None:
        self.assertEqual(normalize_bus_response(b"##000P1500!"), b"#000P1500!")

    def test_fragment_and_concatenation_replay(self) -> None:
        stream = "#000P1500T0200!#001PRAD!@PING!"
        frames = re.findall(r"(?:#[^!]*!|@[^!]*!)", stream)
        self.assertEqual(len(frames), 3)
        self.assertEqual([parse_arm(frame)[0] for frame in frames], ["MOVE", "QUERY", "PING"])

    def test_random_bytes_never_parse_as_motion_without_contract(self) -> None:
        rng = random.Random(0xC550)
        accepted = 0
        for _ in range(2000):
            line = "".join(chr(rng.randrange(32, 127)) for _ in range(rng.randrange(0, 80)))
            try:
                parse_motion(line)
                accepted += 1
            except (ValueError, TypeError):
                pass
        self.assertEqual(accepted, 0)

    def test_random_arm_frames_do_not_execute(self) -> None:
        rng = random.Random(0xA25)
        accepted = 0
        alphabet = "#{}$@!PDT0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ,.-"
        for _ in range(4000):
            frame = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 128)))
            try:
                parse_arm(frame)
                accepted += 1
            except ValueError:
                pass
        self.assertEqual(accepted, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
