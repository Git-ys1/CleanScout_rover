TARGET_MODE_BLACK_CAP = "black_cap"
TARGET_MODE_GOLD_HARDWARE = "gold_hardware"

CLAW_OFFSET_PX = 25


TARGET_CONFIGS = {
    TARGET_MODE_BLACK_CAP: {
        "label": "BLACK_CAP",
        # TODO: replace with Threshold Editor / Histogram values from hardware.
        "thresholds": [(0, 28, -12, 12, -12, 12)],
        "pixels_threshold": 120,
        "min_pixels": 100,
        "aspect_ratio_min": 0.45,
        "aspect_ratio_max": 1.90,
        "density_min": 0.35,
        "solidity_min": 0.45,
        "compactness_min": 0.0,
        "roundness_min": 0.0,
        "elongation_max": 0.85,
        "use_center_roi": True,
        "roi_margin_x_ratio": 0.18,
        "roi_margin_y_ratio": 0.15,
        "distance_numerator": 4200,
        "approach_distance_min": 28,
        "approach_distance_max": 42,
        "center_tolerance_px": 10,
        "ready_frames": 5,
    },
    TARGET_MODE_GOLD_HARDWARE: {
        "label": "GOLD_NUT",
        # TODO: replace with Threshold Editor / Histogram values from hardware.
        "thresholds": [(35, 80, -5, 18, 10, 45)],
        "pixels_threshold": 90,
        "min_pixels": 70,
        "aspect_ratio_min": 0.60,
        "aspect_ratio_max": 1.60,
        "density_min": 0.30,
        "solidity_min": 0.35,
        "compactness_min": 0.25,
        "roundness_min": 0.15,
        "elongation_max": 0.55,
        "use_center_roi": False,
        "roi_margin_x_ratio": 0.0,
        "roi_margin_y_ratio": 0.0,
        "distance_numerator": 3600,
        "approach_distance_min": 20,
        "approach_distance_max": 34,
        "center_tolerance_px": 9,
        "ready_frames": 5,
    },
}


def get_target_config(target_mode):
    return TARGET_CONFIGS[target_mode]


def target_label(target_mode):
    return TARGET_CONFIGS[target_mode]["label"]


def blob_x(blob):
    return blob.x() if hasattr(blob, "x") else blob[0]


def blob_y(blob):
    return blob.y() if hasattr(blob, "y") else blob[1]


def blob_w(blob):
    return blob.w() if hasattr(blob, "w") else blob[2]


def blob_h(blob):
    return blob.h() if hasattr(blob, "h") else blob[3]


def blob_pixels(blob):
    return blob.pixels() if hasattr(blob, "pixels") else blob[4]


def blob_rect(blob):
    return blob.rect() if hasattr(blob, "rect") else (blob_x(blob), blob_y(blob), blob_w(blob), blob_h(blob))


def blob_cx(blob):
    return blob.cx() if hasattr(blob, "cx") else blob_x(blob) + int(blob_w(blob) / 2)


def blob_cy(blob):
    return blob.cy() if hasattr(blob, "cy") else blob_y(blob) + int(blob_h(blob) / 2)


def blob_area(blob):
    return blob_w(blob) * blob_h(blob)


def blob_metric(blob, metric_name, default_value):
    metric = getattr(blob, metric_name, None)
    if metric is None:
        return default_value
    try:
        return metric()
    except TypeError:
        return default_value


def blob_in_center_roi(blob, img, margin_x_ratio, margin_y_ratio):
    img_w = img.width()
    img_h = img.height()
    min_x = int(img_w * margin_x_ratio)
    max_x = int(img_w * (1 - margin_x_ratio))
    min_y = int(img_h * margin_y_ratio)
    max_y = int(img_h * (1 - margin_y_ratio))
    return min_x <= blob_cx(blob) <= max_x and min_y <= blob_cy(blob) <= max_y


def blob_passes_filter(target_mode, blob, img):
    config = get_target_config(target_mode)
    pixels = blob_pixels(blob)
    width = blob_w(blob)
    height = blob_h(blob)

    if pixels < config["min_pixels"]:
        return False
    if width <= 0 or height <= 0:
        return False

    aspect_ratio = width / float(height)
    if aspect_ratio < config["aspect_ratio_min"]:
        return False
    if aspect_ratio > config["aspect_ratio_max"]:
        return False

    density = blob_metric(blob, "density", 1.0)
    if density < config["density_min"]:
        return False

    solidity = blob_metric(blob, "solidity", 1.0)
    if solidity < config["solidity_min"]:
        return False

    compactness = blob_metric(blob, "compactness", 1.0)
    if compactness < config["compactness_min"]:
        return False

    roundness = blob_metric(blob, "roundness", 1.0)
    if roundness < config["roundness_min"]:
        return False

    elongation = blob_metric(blob, "elongation", 0.0)
    if elongation > config["elongation_max"]:
        return False

    if config["use_center_roi"] and not blob_in_center_roi(
        blob,
        img,
        config["roi_margin_x_ratio"],
        config["roi_margin_y_ratio"],
    ):
        return False

    return True


def find_max_blob(blobs):
    max_blob = None
    max_score = -1
    for blob in blobs:
        score = blob_area(blob) + blob_pixels(blob)
        if score > max_score:
            max_blob = blob
            max_score = score
    return max_blob


def find_target(img, target_mode):
    config = get_target_config(target_mode)
    blobs = img.find_blobs(
        config["thresholds"],
        pixels_threshold=config["pixels_threshold"],
        area_threshold=config["pixels_threshold"],
        merge=True,
    )
    if not blobs:
        return None

    filtered = []
    for blob in blobs:
        if blob_passes_filter(target_mode, blob, img):
            filtered.append(blob)

    if not filtered:
        return None

    return find_max_blob(filtered)


def estimate_distance_proxy(blob_width, target_mode):
    if blob_width <= 0:
        return 0
    config = get_target_config(target_mode)
    return config["distance_numerator"] / float(blob_width)


def target_center_error(blob, img_width, img_height, claw_offset):
    pan_error = (img_width / 2) - blob_cx(blob)
    tilt_error = (img_height / 2 + claw_offset) - blob_cy(blob)
    return pan_error, tilt_error


def within_approach_window(distance_proxy, pan_error, tilt_error, target_mode):
    config = get_target_config(target_mode)
    if distance_proxy < config["approach_distance_min"]:
        return False
    if distance_proxy > config["approach_distance_max"]:
        return False
    if abs(pan_error) > config["center_tolerance_px"]:
        return False
    if abs(tilt_error) > config["center_tolerance_px"]:
        return False
    return True
