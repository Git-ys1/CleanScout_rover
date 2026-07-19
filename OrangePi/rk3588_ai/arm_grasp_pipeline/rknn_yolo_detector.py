# coding: utf-8
"""Small ROS-free RKNN YOLO11 adapter for the D435 grasp runtime."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time
from typing import List, Optional, Tuple

try:
    import cv2
except ImportError:  # Keep constructor/config tests hardware-free.
    cv2 = None
import numpy as np

from .target_depth import BBox


class RknnYolo11Detector:
    def __init__(self, model_path: str, yolo_dir: str, target: str = "rk3588",
                 device_id: Optional[str] = None,
                 object_threshold: Optional[float] = None) -> None:
        self.model_path = str(Path(model_path).expanduser())
        self.yolo_dir = str(Path(yolo_dir).expanduser())
        self.target = target
        self.device_id = device_id
        self.object_threshold = (
            None if object_threshold is None else float(object_threshold)
        )
        if (self.object_threshold is not None
                and not 0.0 < self.object_threshold <= 1.0):
            raise ValueError("object_threshold must be in (0, 1]")
        self.model = None
        self.class_names = ()
        self.img_size = (640, 640)
        self.helper = None
        self.post_process = None

    def start(self) -> None:
        if not Path(self.yolo_dir).exists():
            raise RuntimeError("YOLO directory not found: {}".format(self.yolo_dir))
        if self.yolo_dir not in sys.path:
            sys.path.insert(0, self.yolo_dir)
        import yolo11
        if self.object_threshold is not None:
            # The vendor post_process reads this module global. Set it here so
            # CLI --conf affects first-stage detection instead of only filtering
            # detections that already survived the hard-coded 0.25 threshold.
            yolo11.OBJ_THRESH = self.object_threshold

        args = argparse.Namespace(
            model_path=os.path.expanduser(self.model_path),
            target=self.target,
            device_id=self.device_id,
        )
        self.model, platform = yolo11.setup_model(args)
        if platform != "rknn":
            raise RuntimeError("grasp runtime requires an RKNN model")
        self.class_names = tuple(str(name).strip() for name in yolo11.CLASSES)
        self.img_size = yolo11.IMG_SIZE
        self.helper = yolo11.COCO_test_helper(enable_letter_box=True)
        self.post_process = yolo11.post_process

    def close(self) -> None:
        if self.model is not None and hasattr(self.model, "release"):
            self.model.release()
        self.model = None

    def infer(self, frame_bgr: np.ndarray) -> Tuple[List[BBox], float]:
        if cv2 is None:
            raise RuntimeError("opencv-python is required for RKNN YOLO inference")
        if self.model is None or self.helper is None or self.post_process is None:
            raise RuntimeError("RknnYolo11Detector.start() must be called before infer()")
        self.helper.letter_box_info_list.clear()
        image = self.helper.letter_box(
            im=frame_bgr.copy(),
            new_shape=(self.img_size[1], self.img_size[0]),
            pad_color=(0, 0, 0),
        )
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        input_data = np.expand_dims(image, axis=0)
        started = time.perf_counter()
        outputs = self.model.run([input_data])
        infer_ms = (time.perf_counter() - started) * 1000.0
        if outputs is None:
            raise RuntimeError("RKNN inference returned None")
        boxes, classes, scores = self.post_process(outputs)
        if boxes is None:
            return [], infer_ms
        boxes = self.helper.get_real_box(boxes)
        detections = []
        for box, class_id, score in zip(boxes, classes, scores):
            index = int(class_id)
            name = self.class_names[index] if 0 <= index < len(self.class_names) else str(index)
            x1, y1, x2, y2 = [int(round(float(value))) for value in box]
            detections.append(BBox(x1, y1, x2, y2, float(score), name.strip().lower()))
        return detections, infer_ms

    @staticmethod
    def select_target(detections: List[BBox], frame_shape, target_class: str,
                      confidence: float, strategy: str = "nearest_center") -> Optional[BBox]:
        height, width = frame_shape[:2]
        name = str(target_class).strip().lower().replace(" ", "")
        candidates = [
            item for item in detections
            if item.score >= confidence and (
                name == "any" or item.cls.strip().lower().replace(" ", "") == name
            )
        ]
        if not candidates:
            return None
        if strategy == "highest_conf":
            return max(candidates, key=lambda item: item.score)
        return min(
            candidates,
            key=lambda item: (item.center[0] - width / 2.0) ** 2 + (item.center[1] - height / 2.0) ** 2,
        )
