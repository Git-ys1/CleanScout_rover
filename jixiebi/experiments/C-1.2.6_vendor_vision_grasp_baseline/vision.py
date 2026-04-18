from actuator import COLOR_BLUE, COLOR_RED, COLOR_YELLOW


TARGET_MODE_YELLOW = 'yellow'
TARGET_MODE_RED = 'red'
TARGET_MODE_BLUE = 'blue'

PIXELS_THRESHOLD = 500
DISTANCE_NUMERATOR = 13500
GRAB_DISTANCE_MIN = 90
GRAB_DISTANCE_MAX = 110
APPROACH_CENTER_TOLERANCE_PX = 12
APPROACH_READY_FRAMES = 5
CLAW_OFFSET_PX = 25

RED_THRESHOLDS = [(38, 65, 54, 109, 34, 107)]
YELLOW_THRESHOLDS = [(43, 85, -31, 55, 27, 84)]
BLUE_THRESHOLDS = [(10, 46, -26, 63, -82, -7)]

COLOR_LABELS = {
    COLOR_RED: 'RED',
    COLOR_YELLOW: 'YELLOW',
    COLOR_BLUE: 'BLUE',
}

THRESHOLDS_BY_COLOR = {
    COLOR_RED: RED_THRESHOLDS,
    COLOR_YELLOW: YELLOW_THRESHOLDS,
    COLOR_BLUE: BLUE_THRESHOLDS,
}

TARGET_MODE_TO_COLOR = {
    TARGET_MODE_RED: COLOR_RED,
    TARGET_MODE_YELLOW: COLOR_YELLOW,
    TARGET_MODE_BLUE: COLOR_BLUE,
}


def color_label(color_id):
    return COLOR_LABELS.get(color_id, 'NONE')


def find_max_blob(blobs):
    max_blob = None
    max_size = 0
    for blob in blobs:
        size = blob[2] * blob[3]
        if size > max_size:
            max_blob = blob
            max_size = size
    return max_blob


def estimate_distance_proxy(blob_width):
    if blob_width <= 0:
        return 0
    return DISTANCE_NUMERATOR / (blob_width * 2)


def target_center_error(blob, img_width, img_height, claw_offset):
    pan_error = (img_width / 2) - blob.cx()
    tilt_error = (img_height / 2 + claw_offset) - blob.cy()
    return pan_error, tilt_error


def within_grab_window(distance_proxy, pan_error, tilt_error):
    if distance_proxy < GRAB_DISTANCE_MIN or distance_proxy > GRAB_DISTANCE_MAX:
        return False
    if abs(pan_error) > APPROACH_CENTER_TOLERANCE_PX:
        return False
    if abs(tilt_error) > APPROACH_CENTER_TOLERANCE_PX:
        return False
    return True


def find_target(img, target_mode=TARGET_MODE_YELLOW, enable_color_sorting=False, pixels_threshold=PIXELS_THRESHOLD):
    candidates = []

    if enable_color_sorting:
        colors = (COLOR_RED, COLOR_YELLOW, COLOR_BLUE)
    else:
        colors = (TARGET_MODE_TO_COLOR.get(target_mode, COLOR_YELLOW),)

    for color_id in colors:
        blobs = img.find_blobs(THRESHOLDS_BY_COLOR[color_id], pixels_threshold=pixels_threshold)
        if blobs:
            blob = find_max_blob(blobs)
            if blob is not None:
                candidates.append((color_id, blob))

    if not candidates:
        return 0, None

    color_id, blob = max(candidates, key=lambda item: item[1][2] * item[1][3])
    return color_id, blob
