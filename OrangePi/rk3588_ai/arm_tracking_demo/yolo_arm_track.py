#!/usr/bin/env python3
"""YOLO11 RKNN target tracking with safe dry-run arm visual servo."""

from __future__ import annotations

import argparse
import glob
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import yaml

from arm_driver import ArmDriver, ArmDriverError
from target_selector import select_target
from visual_servo import VisualServo, config_from_mapping, normalize_control_axes


WINDOW_NAME = "YOLO11 Arm Tracking"
DEFAULT_YOLO_DIR = Path.home() / "rk3588_ai/rknn_model_zoo/examples/yolo11/python"
DEFAULT_CONFIG = Path(__file__).resolve().parent / "config/arm_track_config.yaml"


def str2bool(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "y", "on"):
        return True
    if text in ("0", "false", "no", "n", "off"):
        return False
    raise argparse.ArgumentTypeError("expected true/false, got {}".format(value))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run YOLO11 RKNN visual tracking and optionally command the arm."
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--yolo_dir", default=str(DEFAULT_YOLO_DIR))
    parser.add_argument("--model_path", default="/home/orangepi/rk3588_ai/models/official_yolo11.rknn")
    parser.add_argument("--target", default="rk3588")
    parser.add_argument("--device_id", default=None)
    parser.add_argument("--camera", default="0")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--fourcc", default="MJPG")
    parser.add_argument(
        "--track_class",
        default="",
        help="COCO class name, or 'any' for any recognized class; config default is used when omitted",
    )
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--selection_strategy", default="nearest_center", choices=("nearest_center", "highest_conf"))
    parser.add_argument("--serial_port", default="")
    parser.add_argument("--baudrate", type=int, default=0)
    parser.add_argument("--dry_run", type=str2bool, default=True)
    parser.add_argument("--enable_arm", action="store_true")
    parser.add_argument(
        "--prepare_pose",
        type=str2bool,
        default=None,
        help="move Servo001/002 to the configured forward tracking pose before opening the camera",
    )
    parser.add_argument("--control_rate", type=float, default=0.0)
    parser.add_argument("--dead_zone", type=int, default=0)
    parser.add_argument(
        "--control_axes",
        default="",
        help="comma-separated arm axes to command, for example 'yaw', 'lift', or 'yaw,pitch'",
    )
    parser.add_argument("--save_path", default="")
    parser.add_argument("--snapshot_path", default="")
    parser.add_argument("--print_boxes", action="store_true")
    parser.add_argument("--print_cmd", action="store_true")
    parser.add_argument(
        "--list_classes",
        action="store_true",
        help="print all class names supported by the loaded YOLO model and exit",
    )
    parser.add_argument("--max_frames", type=int, default=0)
    parser.add_argument("--skip", type=int, default=0)
    parser.add_argument("--log_interval", type=int, default=30)
    parser.add_argument("--no_show", action="store_true")
    return parser.parse_args()


def load_config(path: str):
    config_path = Path(path).expanduser()
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def import_yolo_helpers(yolo_dir: str):
    yolo_path = Path(yolo_dir).expanduser().resolve()
    if not yolo_path.exists():
        raise RuntimeError("YOLO directory not found: {}".format(yolo_path))
    sys.path.insert(0, str(yolo_path))
    from yolo11 import CLASSES, IMG_SIZE, COCO_test_helper, post_process, setup_model

    return CLASSES, IMG_SIZE, COCO_test_helper, post_process, setup_model


def camera_source(value):
    try:
        return int(value)
    except ValueError:
        return value


def source_label(source):
    if isinstance(source, int):
        return "/dev/video{}".format(source)
    return str(source)


def camera_candidates(requested):
    candidates = []
    seen = set()

    def add(source):
        label = source_label(source)
        if label not in seen:
            candidates.append((source, label))
            seen.add(label)

    add(camera_source(requested))
    for path in sorted(glob.glob("/dev/video[0-9]*")):
        add(path)
    return candidates


def decode_fourcc(value):
    number = int(round(value))
    chars = [chr((number >> (8 * index)) & 0xFF) for index in range(4)]
    return "".join(char if 32 <= ord(char) < 127 else "?" for char in chars)


def open_camera(args):
    if len(args.fourcc) != 4:
        raise ValueError("--fourcc must contain exactly four characters")

    fourcc = cv2.VideoWriter_fourcc(*args.fourcc.upper())
    failures = []
    for source, label in camera_candidates(args.camera):
        print("Trying camera {}".format(label))
        capture = cv2.VideoCapture(source, cv2.CAP_V4L2)
        if not capture.isOpened():
            failures.append("{}: open failed".format(label))
            capture.release()
            continue

        capture.set(cv2.CAP_PROP_FOURCC, fourcc)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
        capture.set(cv2.CAP_PROP_FPS, args.fps)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        first_frame = None
        for _ in range(10):
            ok, frame = capture.read()
            if ok and frame is not None and frame.size:
                first_frame = frame
                break
            time.sleep(0.05)

        if first_frame is None:
            failures.append("{}: no video frames".format(label))
            capture.release()
            continue

        return capture, label, first_frame

    raise RuntimeError("Unable to open video stream: {}".format("; ".join(failures)))


def camera_info(capture, label):
    try:
        backend = capture.getBackendName()
    except Exception:
        backend = "unknown"
    info = {
        "device": label,
        "backend": backend,
        "width": int(round(capture.get(cv2.CAP_PROP_FRAME_WIDTH))),
        "height": int(round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))),
        "fps": capture.get(cv2.CAP_PROP_FPS),
        "fourcc": decode_fourcc(capture.get(cv2.CAP_PROP_FOURCC)),
    }
    print(
        "Camera opened: {device}, backend={backend}, {width}x{height} @ {fps:.3f} FPS, fourcc={fourcc}".format(
            **info
        )
    )
    return info


def create_writer(path, frame_size, fps):
    output = Path(path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    for codec in ("MJPG", "mp4v", "XVID"):
        writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*codec), fps, frame_size)
        if writer.isOpened():
            print("Saving video to {} codec={} fps={:.3f}".format(output, codec, fps))
            return writer, output
        writer.release()
        if output.exists():
            output.unlink()
    raise RuntimeError("Unable to open video writer: {}".format(output))


def smooth(previous, current, alpha=0.15):
    if previous <= 0:
        return current
    return (1.0 - alpha) * previous + alpha * current


def draw_detections(image, boxes, scores, classes, class_names, print_boxes=False):
    if boxes is None:
        return
    height, width = image.shape[:2]
    for box, score, class_id in zip(boxes, scores, classes):
        x1, y1, x2, y2 = [int(round(value)) for value in box]
        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(0, min(x2, width - 1))
        y2 = max(0, min(y2, height - 1))
        class_index = int(class_id)
        label = "{} {:.2f}".format(class_names[class_index].strip(), float(score))
        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(image, label, (x1, max(20, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
        if print_boxes:
            print("{} @ ({}, {}, {}, {}) {:.3f}".format(label, x1, y1, x2, y2, float(score)))


def draw_target(image, target):
    if target is None:
        return
    cx = int(round(target["cx"]))
    cy = int(round(target["cy"]))
    cv2.circle(image, (cx, cy), 6, (0, 0, 255), -1)
    cv2.putText(image, "TARGET", (cx + 8, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)


def draw_status(image, status_lines):
    line_height = 23
    width = min(image.shape[1] - 8, 610)
    cv2.rectangle(image, (8, 8), (width, 18 + line_height * len(status_lines)), (0, 0, 0), -1)
    for index, text in enumerate(status_lines):
        cv2.putText(image, text, (15, 30 + index * line_height), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (0, 255, 0), 2)


def build_servo(config, args):
    vs_config = dict(config.get("visual_servo", {}))
    if args.control_rate > 0:
        vs_config["control_rate_hz"] = args.control_rate
    if args.dead_zone > 0:
        vs_config["dead_zone_px"] = args.dead_zone
    if args.control_axes:
        vs_config["control_axes"] = list(normalize_control_axes(args.control_axes))
    return VisualServo(config_from_mapping(vs_config))


def build_driver(config, args):
    serial_cfg = dict(config.get("serial", {}))
    driver_cfg = dict(config.get("driver", {}))
    if "timeout_s" in serial_cfg:
        driver_cfg["timeout_s"] = serial_cfg["timeout_s"]
    port = args.serial_port or serial_cfg.get("port", "/dev/ttyUSB0")
    baudrate = args.baudrate or int(serial_cfg.get("baudrate", 115200))
    return ArmDriver(port=port, baudrate=baudrate, dry_run=args.dry_run, config=driver_cfg)


def arm_stop_indices(driver, axes):
    axes = set(normalize_control_axes(axes))
    indices = []
    if "yaw" in axes:
        indices.append(int(driver.config["yaw_servo_index"]))
    if "lift" in axes:
        indices.append(int(driver.config["lift_servo_index"]))
    if "pitch" in axes:
        indices.append(int(driver.config["pitch_servo_index"]))
    return indices


def send_arm_result(driver, result, duration_ms: int, axes):
    axes = set(normalize_control_axes(axes))
    command_axes = result.get("command_axes") or axes
    command_axes = set(normalize_control_axes(command_axes))
    values = {}
    for axis in ("yaw", "lift", "pitch"):
        if axis in axes and axis in command_axes:
            values[axis] = result[axis]
    return driver.set_axis_values(values, duration_ms=duration_ms)


def run(args):
    if args.skip < 0:
        raise ValueError("--skip must be zero or greater")
    if args.max_frames < 0:
        raise ValueError("--max_frames must be zero or greater")
    if (not args.dry_run) and (not args.enable_arm):
        raise ValueError("Real serial output requires --enable_arm --dry_run false")

    config = load_config(args.config)
    class_names, img_size, coco_helper_cls, post_process, setup_model = import_yolo_helpers(args.yolo_dir)
    if args.list_classes:
        print("\n".join(name.strip() for name in class_names))
        return
    target_cfg = dict(config.get("target_selector", {}))
    servo = build_servo(config, args)
    driver = build_driver(config, args)
    active_axes = tuple(servo.control_axes)
    active_stop_indices = arm_stop_indices(driver, active_axes)

    capture = None
    writer = None
    model = None
    last_frame = None
    arm_paused = False
    stop_reason = "unknown"

    try:
        if args.enable_arm:
            driver.connect()
            prepare_pose = args.prepare_pose
            if prepare_pose is None:
                prepare_pose = bool(driver.config.get("prepare_tracking_pose", True))
            if prepare_pose:
                payload = driver.prepare_tracking_pose()
                if args.print_cmd and not args.dry_run:
                    print(
                        "arm_prepare_pose_hex={}".format(
                            " ".join("{:02x}".format(byte) for byte in payload)
                        )
                    )
                if not args.dry_run:
                    time.sleep(float(driver.config.get("tracking_pose_settle_s", 4.0)))
        capture, camera_label, pending_frame = open_camera(args)
        info = camera_info(capture, camera_label)

        model_args = argparse.Namespace(
            model_path=os.path.expanduser(args.model_path),
            target=args.target,
            device_id=args.device_id,
        )
        model, platform = setup_model(model_args)
        if platform != "rknn":
            raise RuntimeError("Camera tracking demo requires an RKNN model")

        duration_ms = int(dict(config.get("driver", {})).get("duration_ms", 200))
        arm_stop_sent = False
        if args.enable_arm and not arm_paused:
            payload = send_arm_result(driver, servo.last_result, duration_ms, active_axes)
            arm_stop_sent = False
            if payload and args.print_cmd and not args.dry_run:
                print("arm_initial_pose_hex={}".format(" ".join("{:02x}".format(byte) for byte in payload)))

        frame_width = pending_frame.shape[1]
        frame_height = pending_frame.shape[0]
        if args.save_path:
            save_fps = min(max(info["fps"] if info["fps"] > 0 else args.fps, 1.0), 15.0)
            writer, _ = create_writer(args.save_path, (frame_width, frame_height), save_fps)

        if not args.no_show:
            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(WINDOW_NAME, frame_width, frame_height)

        coco_helper = coco_helper_cls(enable_letter_box=True)
        frame_count = 0
        inference_count = 0
        read_failures = 0
        pipeline_fps = 0.0
        yolo_fps = 0.0
        infer_ms = 0.0
        last_loop_time = time.perf_counter()
        last_boxes = None
        last_classes = None
        last_scores = None
        last_target = None
        last_servo_result = servo.last_result

        while True:
            if pending_frame is not None:
                frame = pending_frame
                pending_frame = None
                ok = True
            else:
                ok, frame = capture.read()

            if not ok or frame is None or not frame.size:
                read_failures += 1
                if read_failures >= 10:
                    stop_reason = "camera read failed 10 consecutive times"
                    break
                continue
            read_failures = 0
            frame_count += 1

            run_inference = (frame_count - 1) % (args.skip + 1) == 0
            if run_inference:
                coco_helper.letter_box_info_list.clear()
                input_image = coco_helper.letter_box(
                    im=frame.copy(),
                    new_shape=(img_size[1], img_size[0]),
                    pad_color=(0, 0, 0),
                )
                input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
                input_data = np.expand_dims(input_image, axis=0)

                infer_start = time.perf_counter()
                outputs = model.run([input_data])
                infer_elapsed = time.perf_counter() - infer_start
                if outputs is None:
                    raise RuntimeError("RKNN inference returned None")

                boxes, classes, scores = post_process(outputs)
                if boxes is not None:
                    boxes = coco_helper.get_real_box(boxes)
                last_boxes = boxes
                last_classes = classes
                last_scores = scores
                inference_count += 1
                infer_ms = infer_elapsed * 1000.0
                yolo_fps = smooth(yolo_fps, 1.0 / infer_elapsed)

            target = select_target(
                last_boxes,
                last_classes,
                last_scores,
                frame.shape[1],
                frame.shape[0],
                target_class=args.track_class or target_cfg.get("track_class", "any"),
                conf=args.conf if args.conf is not None else float(target_cfg.get("conf", 0.25)),
                strategy=args.selection_strategy or target_cfg.get("strategy", "nearest_center"),
                class_names=class_names,
            )
            last_target = target
            target_box = None if target is None else target["box"]
            last_servo_result = servo.update(target_box, frame.shape[1], frame.shape[0])

            if args.enable_arm and (not arm_paused) and last_servo_result["should_send"]:
                if last_servo_result["active"]:
                    payload = send_arm_result(driver, last_servo_result, duration_ms, active_axes)
                    arm_stop_sent = False
                    if payload and args.print_cmd and not args.dry_run:
                        print("arm_payload_hex={}".format(" ".join("{:02x}".format(byte) for byte in payload)))
            elif args.enable_arm and (not arm_paused) and (not last_servo_result["active"]):
                if not arm_stop_sent:
                    driver.stop(active_stop_indices)
                    arm_stop_sent = True
                    if args.print_cmd:
                        print("arm inactive: lost_count={}".format(last_servo_result["lost_count"]))

            visual = frame.copy()
            draw_detections(visual, last_boxes, last_scores, last_classes, class_names, print_boxes=args.print_boxes)
            draw_target(visual, last_target)

            now = time.perf_counter()
            loop_elapsed = now - last_loop_time
            last_loop_time = now
            if loop_elapsed > 0:
                pipeline_fps = smooth(pipeline_fps, 1.0 / loop_elapsed)

            detection_count = 0 if last_boxes is None else len(last_boxes)
            target_label = "none"
            if last_target is not None:
                target_label = "{} {:.2f} ({:.0f},{:.0f})".format(
                    last_target["class_name"],
                    last_target["score"],
                    last_target["cx"],
                    last_target["cy"],
                )
            status_lines = [
                "Pipeline FPS: {:.1f}  YOLO FPS: {:.1f} ({:.1f} ms)".format(pipeline_fps, yolo_fps, infer_ms),
                "Detections: {}  Target: {}".format(detection_count, target_label),
                "err=({:.1f},{:.1f}) yaw={:.3f} lift={:.3f} pitch={:.3f}".format(
                    float(last_servo_result["error_x"]),
                    float(last_servo_result["error_y"]),
                    float(last_servo_result["yaw"]),
                    float(last_servo_result["lift"]),
                    float(last_servo_result["pitch"]),
                ),
                "dry_run={} enable_arm={} paused={} serial_connected={}".format(
                    args.dry_run,
                    args.enable_arm,
                    arm_paused,
                    driver.connected,
                ),
                "control_axes={} command_axes={}".format(
                    ",".join(active_axes) if active_axes else "none",
                    ",".join(last_servo_result.get("command_axes", [])) or "none",
                ),
                "q/ESC quit  s snapshot  space pause arm  r reset active axes",
            ]
            draw_status(visual, status_lines)
            last_frame = visual

            if writer is not None:
                writer.write(visual)

            if not args.no_show:
                cv2.imshow(WINDOW_NAME, visual)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    stop_reason = "q pressed"
                    break
                if key == 27:
                    stop_reason = "ESC pressed"
                    break
                if key == ord("s") and args.snapshot_path:
                    save_snapshot(args.snapshot_path, visual)
                if key == ord(" "):
                    arm_paused = not arm_paused
                    print("arm_paused={}".format(arm_paused))
                if key == ord("r"):
                    servo.reset()
                    if args.enable_arm and not arm_paused:
                        payload = send_arm_result(driver, servo.last_result, duration_ms, active_axes)
                        if payload and args.print_cmd and not args.dry_run:
                            print("arm_reset_pose_hex={}".format(" ".join("{:02x}".format(byte) for byte in payload)))
                        arm_stop_sent = False
                    print("visual servo reset")
                try:
                    if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) == 0:
                        stop_reason = "window closed"
                        break
                except cv2.error:
                    pass

            if args.log_interval > 0 and frame_count % args.log_interval == 0:
                print(
                    "Frames={}, inferences={}, pipeline_fps={:.2f}, yolo_fps={:.2f}, "
                    "infer_ms={:.2f}, detections={}, target={}, yaw={:.3f}, lift={:.3f}, pitch={:.3f}".format(
                        frame_count,
                        inference_count,
                        pipeline_fps,
                        yolo_fps,
                        infer_ms,
                        detection_count,
                        "yes" if last_target else "no",
                        float(last_servo_result["yaw"]),
                        float(last_servo_result["lift"]),
                        float(last_servo_result["pitch"]),
                    )
                )

            if args.max_frames and frame_count >= args.max_frames:
                stop_reason = "max_frames reached"
                break

        if args.snapshot_path and last_frame is not None:
            save_snapshot(args.snapshot_path, last_frame)

        print(
            "Stopped: {}. Frames={}, inferences={}, pipeline_fps={:.2f}, yolo_fps={:.2f}, infer_ms={:.2f}".format(
                stop_reason,
                frame_count,
                inference_count,
                pipeline_fps,
                yolo_fps,
                infer_ms,
            )
        )
    except KeyboardInterrupt:
        stop_reason = "KeyboardInterrupt"
        print("Interrupted")
    finally:
        try:
            if args.enable_arm:
                driver.stop(active_stop_indices)
        except ArmDriverError as exc:
            print("Arm stop warning: {}".format(exc))
        driver.close()
        if capture is not None:
            capture.release()
            print("Camera released")
        if writer is not None:
            writer.release()
            print("Video writer released")
        if model is not None:
            model.release()
            print("RKNN model released")
        cv2.destroyAllWindows()
        print("OpenCV windows destroyed")


def save_snapshot(path: str, image):
    snapshot = Path(path).expanduser()
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(snapshot), image):
        raise RuntimeError("Unable to save snapshot: {}".format(snapshot))
    print("Snapshot saved to {}".format(snapshot))


if __name__ == "__main__":
    run(parse_args())
