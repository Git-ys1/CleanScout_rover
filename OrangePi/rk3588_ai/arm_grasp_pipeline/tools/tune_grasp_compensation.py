#!/usr/bin/env python3
# coding: utf-8
"""Safely inspect and tune physically named grasp compensation values.

This tool is deliberately configuration-only: it imports no camera, serial,
servo, IK, or motion module and therefore cannot move the arm.  Values ending
in ``_mm`` are entered and displayed in millimetres; JSON values stay in SI
metres.

Examples::

  # Read-only inspection (the default):
  python3 tools/tune_grasp_compensation.py --check-only

  # Read-only preview of a 2 mm left and 1 mm lower correction:
  python3 tools/tune_grasp_compensation.py \
      --set lateral_mm=2 --set vertical_mm=-1

  # Interactive keyboard tuning; ``save`` still asks for the literal SAVE:
  python3 tools/tune_grasp_compensation.py --interactive --step-mm 1

  # Scripted save requires two independent, explicit flags:
  python3 tools/tune_grasp_compensation.py \
      --set along_mm=1 --write --confirm-save SAVE

Every save creates a byte-for-byte JSON backup first and a Markdown change
record afterwards.  No command-line option enables hardware access.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
import json
import math
from pathlib import Path
import shutil
import sys
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/arm_grasp_default.json"
SAVE_TOKEN = "SAVE"


@dataclass(frozen=True)
class FieldSpec:
    """One user-facing value and its exact physical meaning."""

    key: str
    path: Tuple[object, ...]
    unit: str
    json_per_display_unit: float
    physical_meaning: str


# Positive directions match geometry.approach_frame_matrix(): columns are
# [along, lateral, vertical].  These are labels, not hidden compensation.
FIELD_SPECS: Tuple[FieldSpec, ...] = (
    FieldSpec(
        "along_mm",
        ("grasp_compensation", "grasp_bias_approach_frame_m", 0),
        "mm",
        0.001,
        "前后：沿末端接近轴；正值向物体内部/前进，负值后退。",
    ),
    FieldSpec(
        "lateral_mm",
        ("grasp_compensation", "grasp_bias_approach_frame_m", 1),
        "mm",
        0.001,
        "左右：局部 approach 横向轴；正值沿该帧 +lateral。",
    ),
    FieldSpec(
        "vertical_mm",
        ("grasp_compensation", "grasp_bias_approach_frame_m", 2),
        "mm",
        0.001,
        "高低：局部 approach 竖直轴；正值向上，负值向下。",
    ),
    FieldSpec(
        "grasp_height_mm",
        ("grasp_compensation", "grasp_height_offset_m"),
        "mm",
        0.001,
        "额外抓取高度：叠加到 vertical；正值向上。",
    ),
    FieldSpec(
        "depth_bias_mm",
        ("grasp_compensation", "depth_bias_m"),
        "mm",
        0.001,
        "深度：D435 对当前材质/距离的系统偏置；正值增加光学深度。",
    ),
    FieldSpec(
        "camera_x_mm",
        ("grasp_compensation", "camera_point_bias_m", 0),
        "mm",
        0.001,
        "相机点 X 系统误差，仅用于已确认的相机坐标偏差。",
    ),
    FieldSpec(
        "camera_y_mm",
        ("grasp_compensation", "camera_point_bias_m", 1),
        "mm",
        0.001,
        "相机点 Y 系统误差，仅用于已确认的相机坐标偏差。",
    ),
    FieldSpec(
        "camera_z_mm",
        ("grasp_compensation", "camera_point_bias_m", 2),
        "mm",
        0.001,
        "相机点 Z 系统误差，仅用于已确认的相机坐标偏差。",
    ),
    FieldSpec(
        "object_radius_mm",
        ("object_geometry", "bottle_radius_m"),
        "mm",
        0.001,
        "物体半径参考值；不会静默覆盖实际 surface_to_center。",
    ),
    FieldSpec(
        "surface_to_center_mm",
        ("grasp_compensation", "object_surface_to_grasp_center_m"),
        "mm",
        0.001,
        "从相机可见表面沿 object_center_axis 推进到抓取中心的距离。",
    ),
    FieldSpec(
        "final_insertion_mm",
        ("grasp_compensation", "final_insertion_m"),
        "mm",
        0.001,
        "最终插入：遮挡近场后沿 +along 的受限盲插距离，只允许非负小量。",
    ),
    FieldSpec(
        "pixel_x_px",
        ("grasp_compensation", "target_pixel_offset_px", 0),
        "px",
        1.0,
        "检测框选点的像素 X 偏移；正值向 RGB 图像右侧。",
    ),
    FieldSpec(
        "pixel_y_px",
        ("grasp_compensation", "target_pixel_offset_px", 1),
        "px",
        1.0,
        "检测框选点的像素 Y 偏移；正值向 RGB 图像下方。",
    ),
    FieldSpec(
        "pixel_y_ratio",
        ("grasp_compensation", "target_pixel_y_ratio"),
        "ratio",
        1.0,
        "抓取像素在检测框顶部(0)到底部(1)之间的纵向比例。",
    ),
)
FIELD_BY_KEY: Dict[str, FieldSpec] = {spec.key: spec for spec in FIELD_SPECS}


def _load_json(path: Path) -> MutableMapping[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("configuration root must be a JSON object")
    return value


def _walk_parent(config: MutableMapping[str, object], path: Sequence[object]):
    value = config
    for part in path[:-1]:
        if isinstance(part, int):
            if not isinstance(value, list) or part >= len(value):
                raise ValueError("missing configuration path: {}".format(path))
            value = value[part]
        else:
            if not isinstance(value, dict) or part not in value:
                raise ValueError("missing configuration path: {}".format(path))
            value = value[part]
    return value, path[-1]


def _get_json_value(config: MutableMapping[str, object], spec: FieldSpec) -> float:
    parent, final = _walk_parent(config, spec.path)
    try:
        raw = parent[final]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("missing configuration path for {}".format(spec.key)) from exc
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError("{} must be finite".format(spec.key))
    return value


def _set_json_value(
    config: MutableMapping[str, object], spec: FieldSpec, display_value: float
) -> None:
    value = float(display_value)
    if not math.isfinite(value):
        raise ValueError("{} must be finite".format(spec.key))
    parent, final = _walk_parent(config, spec.path)
    parent[final] = value * spec.json_per_display_unit


def display_value(config: MutableMapping[str, object], key: str) -> float:
    spec = FIELD_BY_KEY[key]
    return _get_json_value(config, spec) / spec.json_per_display_unit


def validate_config(config: MutableMapping[str, object]) -> None:
    """Validate tuning values without importing any hardware-facing module."""

    for spec in FIELD_SPECS:
        value = _get_json_value(config, spec)
        if spec.unit == "mm" and abs(value) > 1.0:
            raise ValueError(
                "{} exceeds one metre; check mm/m units".format(spec.key)
            )

    compensation = config.get("grasp_compensation")
    geometry = config.get("object_geometry")
    if not isinstance(compensation, Mapping) or not isinstance(geometry, Mapping):
        raise ValueError("grasp_compensation and object_geometry are required")

    ratio = display_value(config, "pixel_y_ratio")
    if ratio < 0.0 or ratio > 1.0:
        raise ValueError("pixel_y_ratio must be in [0, 1]")

    realsense = config.get("realsense", {})
    if isinstance(realsense, Mapping):
        width = float(realsense.get("width", 0.0))
        height = float(realsense.get("height", 0.0))
        if width > 0.0 and abs(display_value(config, "pixel_x_px")) > width:
            raise ValueError("pixel_x_px exceeds configured RGB width")
        if height > 0.0 and abs(display_value(config, "pixel_y_px")) > height:
            raise ValueError("pixel_y_px exceeds configured RGB height")

    radius = _get_json_value(config, FIELD_BY_KEY["object_radius_mm"])
    surface = _get_json_value(config, FIELD_BY_KEY["surface_to_center_mm"])
    insertion = _get_json_value(config, FIELD_BY_KEY["final_insertion_mm"])
    if radius <= 0.0:
        raise ValueError("object_radius_mm must be positive")
    if surface < 0.0:
        raise ValueError("surface_to_center_mm must be non-negative")
    if insertion < 0.0:
        raise ValueError("final_insertion_mm must be non-negative")

    try:
        maximum = float(compensation["max_final_insertion_m"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("grasp_compensation.max_final_insertion_m is required") from exc
    if not math.isfinite(maximum) or maximum < 0.0:
        raise ValueError("max_final_insertion_m must be finite and non-negative")
    if insertion > maximum + 1e-12:
        raise ValueError(
            "final_insertion_mm exceeds configured max_final_insertion_m ({:.3f} mm)".format(
                maximum * 1000.0
            )
        )


def apply_assignment(config: MutableMapping[str, object], assignment: str) -> str:
    if "=" not in assignment:
        raise ValueError("assignment must be NAME=VALUE")
    key, raw = (part.strip() for part in assignment.split("=", 1))
    if key not in FIELD_BY_KEY:
        raise ValueError(
            "unknown field {!r}; choose {}".format(key, ", ".join(FIELD_BY_KEY))
        )
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError("{} requires a numeric value".format(key)) from exc
    spec = FIELD_BY_KEY[key]
    old_value = display_value(config, key)
    _set_json_value(config, spec, value)
    try:
        validate_config(config)
    except (TypeError, ValueError):
        _set_json_value(config, spec, old_value)
        raise
    return key


def _changed_keys(
    before: MutableMapping[str, object], after: MutableMapping[str, object]
) -> List[str]:
    return [
        spec.key
        for spec in FIELD_SPECS
        if not math.isclose(
            display_value(before, spec.key),
            display_value(after, spec.key),
            rel_tol=0.0,
            abs_tol=1e-12,
        )
    ]


def _tcp_label(config: Mapping[str, object]) -> str:
    tool = config.get("tool_tcp", {})
    if not isinstance(tool, Mapping):
        return "UNKNOWN"
    active = str(tool.get("active_grasp_tcp", "UNKNOWN"))
    calibrated = tool.get("{}_calibrated".format(active), False)
    return "{} (calibrated={})".format(active.upper(), bool(calibrated))


def render_current(config: MutableMapping[str, object]) -> str:
    validate_config(config)
    lines = [
        "CONFIGURATION_ONLY hardware_access=false motion_possible=false",
        "ACTIVE_TCP {}".format(_tcp_label(config)),
        "",
        "Physical compensation values:",
    ]
    for spec in FIELD_SPECS:
        lines.append(
            "  {:24s} {:+10.3f} {:5s}  {}".format(
                spec.key, display_value(config, spec.key), spec.unit, spec.physical_meaning
            )
        )
    lines.extend(
        [
            "",
            "Note: object_radius_mm is a measured/reference radius;",
            "surface_to_center_mm is the value actually applied to the visible surface.",
        ]
    )
    return "\n".join(lines)


def build_report(
    config_path: Path,
    before: MutableMapping[str, object],
    after: MutableMapping[str, object],
    *,
    saved: bool,
    backup_path: Optional[Path],
) -> str:
    validate_config(before)
    validate_config(after)
    changed = set(_changed_keys(before, after))
    lines = [
        "# Grasp compensation tuning record",
        "",
        "- Generated: `{}`".format(datetime.now().astimezone().isoformat()),
        "- Config: `{}`".format(config_path),
        "- Configuration saved: `{}`".format(str(bool(saved)).lower()),
        "- Backup: `{}`".format(str(backup_path) if backup_path else "none"),
        "- Hardware access: `false` (this tool has no serial/motion imports)",
        "- Active grasp TCP: `{}`".format(_tcp_label(after)),
        "",
        "## Values",
        "",
        "| Field | Before | After | Unit | Changed | Physical meaning |",
        "|---|---:|---:|---|:---:|---|",
    ]
    for spec in FIELD_SPECS:
        lines.append(
            "| `{}` | {:+.3f} | {:+.3f} | {} | {} | {} |".format(
                spec.key,
                display_value(before, spec.key),
                display_value(after, spec.key),
                spec.unit,
                "yes" if spec.key in changed else "no",
                spec.physical_meaning,
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation guardrails",
            "",
            "- `along/lateral/vertical` belong to the current local approach frame, not base XYZ.",
            "- `depth_bias_mm` changes aligned D435 optical depth; it is not an RGB/depth pixel registration offset.",
            "- `object_radius_mm` is reference geometry. `surface_to_center_mm` is the applied visible-surface-to-center correction.",
            "- `final_insertion_mm` is a non-negative, bounded +along insertion and is checked against `max_final_insertion_m`.",
            "- This record does not claim a grasp or any mechanical-arm arrival.",
        ]
    )
    return "\n".join(lines) + "\n"


def _backup(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    destination = path.with_name(path.name + ".bak." + stamp)
    shutil.copy2(str(path), str(destination))
    return destination


def _default_report_path(config_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return config_path.parent / "tuning_reports" / ("grasp-compensation-" + stamp + ".md")


def save_config(
    config_path: Path,
    before: MutableMapping[str, object],
    after: MutableMapping[str, object],
    report_path: Optional[Path] = None,
) -> Tuple[Path, Path]:
    validate_config(after)
    backup = _backup(config_path)
    with config_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(after, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    report = report_path or _default_report_path(config_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        build_report(config_path, before, after, saved=True, backup_path=backup),
        encoding="utf-8",
    )
    return backup, report


def _interactive_help() -> str:
    return """Commands (all are configuration-only):
  show                  show every value and its physical meaning
  1 | 2                 select 1 mm or 2 mm keyboard increment
  w/s                   along + / - (front/forward, back)
  d/a                   lateral + / - (right/left in local frame)
  r/f                   vertical + / - (up/down)
  e/q                   depth_bias + / -
  t/g                   surface_to_center + / -
  y/h                   object_radius + / -
  i/k                   final_insertion + / -
  set NAME=VALUE        set an explicit displayed-unit value
  sync-radius           copy object_radius_mm to surface_to_center_mm
  pixel-y RATIO         set bbox Y ratio in [0,1]
  undo                  undo one edit
  reset                 restore values loaded at program start
  pause | <space>       pause marker (no hardware controller exists here)
  save                  type SAVE at the second prompt; backup + report first
  quit                  exit without saving current unsaved edits
"""


_KEY_DELTAS = {
    "w": ("along_mm", +1.0),
    "s": ("along_mm", -1.0),
    "d": ("lateral_mm", +1.0),
    "a": ("lateral_mm", -1.0),
    "r": ("vertical_mm", +1.0),
    "f": ("vertical_mm", -1.0),
    "e": ("depth_bias_mm", +1.0),
    "q": ("depth_bias_mm", -1.0),
    "t": ("surface_to_center_mm", +1.0),
    "g": ("surface_to_center_mm", -1.0),
    "y": ("object_radius_mm", +1.0),
    "h": ("object_radius_mm", -1.0),
    "i": ("final_insertion_mm", +1.0),
    "k": ("final_insertion_mm", -1.0),
}


def interactive_session(
    config_path: Path,
    initial: MutableMapping[str, object],
    *,
    step_mm: float,
    report_path: Optional[Path] = None,
) -> Tuple[MutableMapping[str, object], bool]:
    current = deepcopy(initial)
    history: List[MutableMapping[str, object]] = []
    saved = False
    step = float(step_mm)
    print(_interactive_help())
    print(render_current(current))
    while True:
        try:
            raw = input("tuner> ")
        except EOFError:
            print("EOF_EXIT unsaved_changes={}".format(bool(_changed_keys(initial, current))))
            return current, saved
        command = raw.strip()
        lowered = command.lower()
        if not command or lowered == "pause":
            print("PAUSED configuration_only=true hardware_motion=false")
            continue
        if lowered in ("quit", "exit"):
            print("EXIT unsaved_changes={}".format(bool(_changed_keys(initial, current))))
            return current, saved
        if lowered in ("help", "?"):
            print(_interactive_help())
            continue
        if lowered == "show":
            print(render_current(current))
            continue
        if lowered in ("1", "2"):
            step = float(lowered)
            print("STEP_MM {:.0f}".format(step))
            continue
        if lowered in _KEY_DELTAS:
            key, direction = _KEY_DELTAS[lowered]
            history.append(deepcopy(current))
            try:
                apply_assignment(
                    current,
                    "{}={}".format(key, display_value(current, key) + direction * step),
                )
            except ValueError as exc:
                current = history.pop()
                print("REJECTED {}".format(exc))
                continue
            print("UPDATED {}={:+.3f} {} fresh_observation_required=true".format(
                key, display_value(current, key), FIELD_BY_KEY[key].unit
            ))
            continue
        if lowered.startswith("set "):
            history.append(deepcopy(current))
            try:
                key = apply_assignment(current, command[4:].strip())
            except ValueError as exc:
                current = history.pop()
                print("REJECTED {}".format(exc))
                continue
            print("UPDATED {}={:+.3f} {} fresh_observation_required=true".format(
                key, display_value(current, key), FIELD_BY_KEY[key].unit
            ))
            continue
        if lowered.startswith("pixel-y "):
            history.append(deepcopy(current))
            try:
                key = apply_assignment(current, "pixel_y_ratio=" + command.split(None, 1)[1])
            except ValueError as exc:
                current = history.pop()
                print("REJECTED {}".format(exc))
                continue
            print("UPDATED {}={:+.3f} ratio fresh_observation_required=true".format(
                key, display_value(current, key)
            ))
            continue
        if lowered == "sync-radius":
            history.append(deepcopy(current))
            apply_assignment(
                current,
                "surface_to_center_mm={}".format(display_value(current, "object_radius_mm")),
            )
            print("UPDATED surface_to_center_mm={:+.3f} mm from=object_radius_mm fresh_observation_required=true".format(
                display_value(current, "surface_to_center_mm")
            ))
            continue
        if lowered == "undo":
            if history:
                current = history.pop()
                print("UNDO_OK fresh_observation_required=true")
            else:
                print("UNDO_EMPTY")
            continue
        if lowered == "reset":
            history.append(deepcopy(current))
            current = deepcopy(initial)
            print("RESET_TO_STARTUP_DEFAULTS fresh_observation_required=true")
            continue
        if lowered == "save":
            confirmation = input("Type SAVE to back up and write JSON: ").strip()
            if confirmation != SAVE_TOKEN:
                print("SAVE_CANCELLED confirmation_mismatch=true")
                continue
            backup, report = save_config(
                config_path, initial, current, report_path=report_path
            )
            saved = True
            print("CONFIG_BACKUP {}".format(backup))
            print("CONFIG_WRITTEN {}".format(config_path))
            print("REPORT_WRITTEN {}".format(report))
            return current, saved
        print("UNKNOWN_COMMAND {!r}; enter help".format(command))


def parse_args(argv: Optional[Iterable[str]] = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="validate/show or preview values without modifying the JSON",
    )
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument(
        "--step-mm", type=float, choices=(1.0, 2.0), default=1.0
    )
    parser.add_argument(
        "--set",
        dest="assignments",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="set a displayed-unit value; repeat as needed",
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--confirm-save",
        default="",
        help="scripted writes require the exact literal SAVE",
    )
    parser.add_argument(
        "--report",
        default="",
        help="Markdown path; writes automatically generate a report if omitted",
    )
    return parser.parse_args(argv)


def run(args) -> int:
    if args.interactive and (args.write or args.assignments):
        raise ValueError("--interactive cannot be combined with --write or --set")
    if args.check_only and args.write:
        raise ValueError("--check-only and --write are mutually exclusive")
    if args.confirm_save and not args.write:
        raise ValueError("--confirm-save is only valid with --write")

    config_path = Path(args.config).expanduser().resolve()
    before = _load_json(config_path)
    validate_config(before)

    report_path = Path(args.report).expanduser().resolve() if args.report else None
    if args.interactive:
        interactive_session(
            config_path,
            before,
            step_mm=args.step_mm,
            report_path=report_path,
        )
        return 0

    after = deepcopy(before)
    for assignment in args.assignments:
        apply_assignment(after, assignment)
    validate_config(after)
    print(render_current(after))
    changed = _changed_keys(before, after)
    print("PREVIEW_CHANGED_FIELDS {}".format(",".join(changed) if changed else "none"))

    if args.write:
        if args.confirm_save != SAVE_TOKEN:
            raise ValueError("--write requires --confirm-save SAVE")
        backup, report = save_config(
            config_path, before, after, report_path=report_path
        )
        print("CONFIG_BACKUP {}".format(backup))
        print("CONFIG_WRITTEN {}".format(config_path))
        print("REPORT_WRITTEN {}".format(report))
    else:
        print("CHECK_ONLY config_not_modified=true")
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                build_report(
                    config_path, before, after, saved=False, backup_path=None
                ),
                encoding="utf-8",
            )
            print("REPORT_WRITTEN {}".format(report_path))
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print("ERROR {}".format(exc), file=sys.stderr)
        raise SystemExit(2)
