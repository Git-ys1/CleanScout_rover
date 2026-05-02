# Fan And Edge Integration Contract

This document is for backend engineers integrating the Raspberry Pi side fan/servo bridge and edge relay into backend APIs.

## Scope

Current active capabilities exposed on Raspberry Pi side:

1. Fan master enable
2. Dual fan PWM control
3. Dual fan RPM feedback
4. Edge relay manual control bridge

Current lid servo is not exposed as a standalone frontend control.
It is internally coupled to fan enable interlock.

## Active ROS Topics

### Control inputs

1. `/fans/enable`
   Type: `std_msgs/Bool`
   Meaning:
   - `true`: enable fan system
   - `false`: disable fan system

2. `/fan_a/pwm_percent`
   Type: `std_msgs/Float32`
   Range: `0.0 ~ 100.0`
   Meaning: fan A PWM percent

3. `/fan_b/pwm_percent`
   Type: `std_msgs/Float32`
   Range: `0.0 ~ 100.0`
   Meaning: fan B PWM percent

### Feedback outputs

1. `/fan_a/rpm`
   Type: `std_msgs/Float32`
   Meaning: aggregated RPM estimate for fan A

2. `/fan_b/rpm`
   Type: `std_msgs/Float32`
   Meaning: aggregated RPM estimate for fan B

### Debug outputs

1. `/fan_lid/state`
   Type: `std_msgs/Bool`
   Meaning:
   - `true`: lid open
   - `false`: lid closed

2. `/fans/state_summary`
   Type: `std_msgs/String`
   Meaning: compact summary for debugging and logs

3. `/fan_a/fg_in_rpm`
4. `/fan_a/fg_out_rpm`
5. `/fan_b/fg_in_rpm`
6. `/fan_b/fg_out_rpm`
   Type: `std_msgs/Float32`
   Meaning: raw FG-derived RPM channels for diagnostics

## Frozen behavior

Current fan bridge logic is interlocked:

1. On `/fans/enable = true`
   - open lid first
   - wait for settle
   - enable relay
   - then apply fan A/B PWM

2. On `/fans/enable = false`
   - set fan A/B PWM to 0 first
   - disable relay
   - close lid

This means backend should NOT expose relay or lid as separate user-facing manual toggles in this round.

## Backend API recommendation

Recommended minimal backend API surface:

1. `POST /device/fans/enable`
   Body:
   ```json
   {"enabled": true}
   ```

2. `POST /device/fans/pwm`
   Body:
   ```json
   {"fanA": 35.0, "fanB": 35.0}
   ```

3. `GET /device/fans/state`
   Response should include at least:
   ```json
   {
     "enabled": true,
     "fanA": {"pwm": 35.0, "rpm": 1200.0},
     "fanB": {"pwm": 35.0, "rpm": 1180.0},
     "lidOpen": true,
     "summary": "enabled=true lid_open=true relay=on fan_a_pwm=35.0 fan_b_pwm=35.0 fan_a_rpm=1200.0 fan_b_rpm=1180.0"
   }
   ```

## Edge relay integration direction

Current demo launch can expose both:

1. fan bridge
2. edge relay

Backend should prepare to aggregate these capabilities under one device profile instead of treating them as isolated demos.

Suggested capability groups:

1. `manual_control`
2. `fan_control`
3. `fan_feedback`

## What backend engineers should do now

1. Add fan enable command mapping to `/fans/enable`
2. Add dual PWM command mapping to `/fan_a/pwm_percent` and `/fan_b/pwm_percent`
3. Subscribe or bridge `/fan_a/rpm` and `/fan_b/rpm`
4. Optionally log `/fan_lid/state` and `/fans/state_summary`
5. Do not expose lid angle or relay toggle as independent business controls in this round

## What backend engineers should NOT assume

1. Do not assume lid servo is user-facing
2. Do not assume relay can be toggled independently of fans
3. Do not use raw FG channels as product-facing values before validation
4. Do not assume edge relay currently carries fan topics automatically; that requires a later explicit extension if desired

## Current V-line backend API freeze

The backend API surface is now frozen as:

1. `POST /api/device/fans/enable`
   Body:
   ```json
   {"enabled": true}
   ```

2. `POST /api/device/fans/pwm`
   Body:
   ```json
   {"fanA": 35.0, "fanB": 35.0}
   ```

3. `GET /api/device/fans/state`
   Response shape:
   ```json
   {
     "enabled": true,
     "fanA": {"pwm": 35.0, "rpm": 1200.0},
     "fanB": {"pwm": 35.0, "rpm": 1180.0},
     "lidOpen": true,
     "summary": "enabled=true lid_open=true relay=on ...",
     "lastUpdate": "2026-04-25T12:34:56.000Z"
   }
   ```

Frontend does not publish ROS topics directly. It only calls the backend APIs above.

## edge-relay extension freeze

If the current device path uses `edge-relay` instead of direct `rosbridge`, the relay should follow this first fan extension:

### Backend -> Pi

Enable or disable fan system:

```json
{
  "op": "fan_enable",
  "seq": 201,
  "enabled": true
}
```

Set dual fan PWM:

```json
{
  "op": "fan_pwm",
  "seq": 202,
  "fanA": 35.0,
  "fanB": 35.0
}
```

### Pi -> Backend

Recommended piggyback inside existing `telemetry` frame:

```json
{
  "op": "telemetry",
  "deviceId": "csrpi-001",
  "fans": {
    "enabled": true,
    "fanA": {"pwm": 35.0, "rpm": 1200.0},
    "fanB": {"pwm": 35.0, "rpm": 1180.0},
    "lidOpen": true,
    "summary": "enabled=true lid_open=true relay=on fan_a_pwm=35.0 fan_b_pwm=35.0 fan_a_rpm=1200.0 fan_b_rpm=1180.0"
  },
  "ts": 1710000000000
}
```

Dedicated fan-only telemetry is also accepted:

```json
{
  "op": "fan_telemetry",
  "deviceId": "csrpi-001",
  "enabled": true,
  "fanA": {"pwm": 35.0, "rpm": 1200.0},
  "fanB": {"pwm": 35.0, "rpm": 1180.0},
  "lidOpen": true,
  "summary": "enabled=true lid_open=true relay=on ...",
  "ts": 1710000000000
}
```

## Current integration rule

In this round:

1. Fan enable is user-facing
2. Dual PWM is user-facing
3. Dual RPM is user-facing read-only
4. Lid open state is read-only
5. Relay and servo angle are still not user-facing controls
