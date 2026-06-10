import argparse
import glob
import os
import time
from pathlib import Path

import cv2
import numpy as np

from yolo11 import (
    CLASSES,
    IMG_SIZE,
    COCO_test_helper,
    post_process,
    setup_model,
)


WINDOW_NAME = "YOLO11 RKNN Camera"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run YOLO11 RKNN inference on a V4L2 camera."
    )
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--target", default="rk3588")
    parser.add_argument("--device_id", default=None)
    parser.add_argument(
        "--camera",
        default="0",
        help="Camera index or device path. Other /dev/videoN nodes are tried if it fails.",
    )
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--fourcc", default="MJPG")
    parser.add_argument("--save_path", default="")
    parser.add_argument("--snapshot_path", default="")
    parser.add_argument("--no_show", action="store_true")
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Skip this many captured frames between NPU inferences.",
    )
    parser.add_argument("--print_boxes", action="store_true")
    parser.add_argument(
        "--max_frames",
        type=int,
        default=0,
        help="Stop after this many frames; zero runs until q, ESC, or interruption.",
    )
    parser.add_argument("--log_interval", type=int, default=30)
    return parser.parse_args()


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

    raise RuntimeError(
        "Unable to open a video stream. Attempts: {}".format(
            "; ".join(failures)
        )
    )


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
        "Camera opened: {device}, backend={backend}, "
        "{width}x{height} @ {fps:.3f} FPS, fourcc={fourcc}".format(**info)
    )
    return info


def create_writer(path, frame_size, fps):
    output = Path(path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    codec_candidates = ("MJPG", "mp4v", "XVID")
    for codec in codec_candidates:
        writer = cv2.VideoWriter(
            str(output),
            cv2.VideoWriter_fourcc(*codec),
            fps,
            frame_size,
        )
        if writer.isOpened():
            print(
                "Saving video to {} with codec={} at {:.3f} FPS".format(
                    output, codec, fps
                )
            )
            return writer, output, codec
        writer.release()
        if output.exists():
            output.unlink()
    raise RuntimeError(
        "Unable to open video writer {} with codecs {}".format(
            output, ", ".join(codec_candidates)
        )
    )


def draw_detections(image, boxes, scores, classes, print_boxes=False):
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
        label = "{} {:.2f}".format(CLASSES[class_index].strip(), float(score))

        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        text_size, baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2
        )
        text_y = max(text_size[1] + 4, y1)
        cv2.rectangle(
            image,
            (x1, text_y - text_size[1] - 4),
            (min(width - 1, x1 + text_size[0] + 4), text_y + baseline),
            (255, 0, 0),
            -1,
        )
        cv2.putText(
            image,
            label,
            (x1 + 2, text_y - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )

        if print_boxes:
            print(
                "{} @ ({}, {}, {}, {}) {:.3f}".format(
                    CLASSES[class_index].strip(),
                    x1,
                    y1,
                    x2,
                    y2,
                    float(score),
                )
            )


def draw_status(image, pipeline_fps, yolo_fps, infer_ms, detections):
    lines = [
        "Pipeline FPS: {:.1f}".format(pipeline_fps),
        "YOLO FPS: {:.1f} ({:.1f} ms)".format(yolo_fps, infer_ms),
        "Detections: {}".format(detections),
        "q / ESC: quit",
    ]
    line_height = 24
    cv2.rectangle(
        image,
        (8, 8),
        (315, 14 + line_height * len(lines)),
        (0, 0, 0),
        -1,
    )
    for index, text in enumerate(lines):
        cv2.putText(
            image,
            text,
            (15, 30 + index * line_height),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (0, 255, 0),
            2,
        )


def smooth(previous, current, alpha=0.15):
    if previous <= 0:
        return current
    return (1.0 - alpha) * previous + alpha * current


def run(args):
    if args.skip < 0:
        raise ValueError("--skip must be zero or greater")
    if args.max_frames < 0:
        raise ValueError("--max_frames must be zero or greater")

    capture = None
    writer = None
    model = None
    last_frame = None
    stop_reason = "unknown"

    try:
        capture, camera_label, pending_frame = open_camera(args)
        info = camera_info(capture, camera_label)

        model_args = argparse.Namespace(
            model_path=os.path.expanduser(args.model_path),
            target=args.target,
            device_id=args.device_id,
        )
        model, platform = setup_model(model_args)
        if platform != "rknn":
            raise RuntimeError("Camera demo requires an RKNN model")

        frame_width = pending_frame.shape[1]
        frame_height = pending_frame.shape[0]
        if args.save_path:
            save_fps = info["fps"] if info["fps"] > 0 else args.fps
            save_fps = min(max(save_fps, 1.0), 15.0)
            writer, _, _ = create_writer(
                args.save_path,
                (frame_width, frame_height),
                save_fps,
            )

        if not args.no_show:
            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(WINDOW_NAME, frame_width, frame_height)

        coco_helper = COCO_test_helper(enable_letter_box=True)
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
                    new_shape=(IMG_SIZE[1], IMG_SIZE[0]),
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

                if args.print_boxes and boxes is not None:
                    print("Frame {}:".format(frame_count))
                    draw_detections(
                        frame.copy(),
                        boxes,
                        scores,
                        classes,
                        print_boxes=True,
                    )

            visual = frame.copy()
            draw_detections(
                visual,
                last_boxes,
                last_scores,
                last_classes,
                print_boxes=False,
            )

            now = time.perf_counter()
            loop_elapsed = now - last_loop_time
            last_loop_time = now
            if loop_elapsed > 0:
                pipeline_fps = smooth(pipeline_fps, 1.0 / loop_elapsed)
            detection_count = 0 if last_boxes is None else len(last_boxes)
            draw_status(
                visual,
                pipeline_fps,
                yolo_fps,
                infer_ms,
                detection_count,
            )
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
                try:
                    window_visible = cv2.getWindowProperty(
                        WINDOW_NAME, cv2.WND_PROP_VISIBLE
                    )
                    if window_visible == 0:
                        stop_reason = "window closed"
                        break
                except cv2.error:
                    pass

            if args.log_interval > 0 and frame_count % args.log_interval == 0:
                print(
                    "Frames={}, inferences={}, pipeline_fps={:.2f}, "
                    "yolo_fps={:.2f}, infer_ms={:.2f}, detections={}".format(
                        frame_count,
                        inference_count,
                        pipeline_fps,
                        yolo_fps,
                        infer_ms,
                        detection_count,
                    )
                )

            if args.max_frames and frame_count >= args.max_frames:
                stop_reason = "max_frames reached"
                break

        if args.snapshot_path and last_frame is not None:
            snapshot = Path(args.snapshot_path).expanduser()
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(snapshot), last_frame):
                raise RuntimeError(
                    "Unable to save snapshot: {}".format(snapshot)
                )
            print("Snapshot saved to {}".format(snapshot))

        print(
            "Stopped: {}. Frames={}, inferences={}, "
            "pipeline_fps={:.2f}, yolo_fps={:.2f}, infer_ms={:.2f}".format(
                stop_reason,
                frame_count,
                inference_count,
                pipeline_fps,
                yolo_fps,
                infer_ms,
            )
        )
    finally:
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


if __name__ == "__main__":
    run(parse_args())
