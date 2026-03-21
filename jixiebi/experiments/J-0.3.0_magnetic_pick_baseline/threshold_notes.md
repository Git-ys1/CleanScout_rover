# Threshold Notes

## Rule
- 阈值必须来自 OpenMV IDE：
  - `Histogram`
  - `Threshold Editor`
- 不允许把下面的占位值写成“已实测冻结值”

## Current Placeholder Thresholds

### Black Capacitor
- Target mode: `TARGET_MODE_BLACK_CAP`
- Placeholder threshold: `(0, 28, -12, 12, -12, 12)`
- Placeholder pixels threshold: `120`
- Placeholder shape filter:
  - `aspect_ratio = 0.45 .. 1.90`
  - `density >= 0.35`
  - `solidity >= 0.45`
  - center ROI enabled

### Gold Nut
- Target mode: `TARGET_MODE_GOLD_HARDWARE`
- Placeholder threshold: `(35, 80, -5, 18, 10, 45)`
- Placeholder pixels threshold: `90`
- Placeholder shape filter:
  - `aspect_ratio = 0.60 .. 1.60`
  - `density >= 0.30`
  - `compactness >= 0.25`
  - `roundness >= 0.15`
  - `elongation <= 0.55`

## Distance Proxy Template

### Black Capacitor
- Formula: `distance_proxy = DISTANCE_NUMERATOR / blob_width`
- Placeholder numerator: `4200`
- Placeholder window: `28 .. 42`

### Gold Nut
- Formula: `distance_proxy = DISTANCE_NUMERATOR / blob_width`
- Placeholder numerator: `3600`
- Placeholder window: `20 .. 34`

## Hardware Calibration To Fill
- Actual black capacitor threshold:
- Actual gold nut threshold:
- Actual black capacitor distance window:
- Actual gold nut distance window:
