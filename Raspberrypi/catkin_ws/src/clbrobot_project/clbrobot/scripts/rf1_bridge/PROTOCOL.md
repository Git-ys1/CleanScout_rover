# OpenRF1 Protocol Snapshot

## Pi to OpenRF1

- `W,a,b,c,d` : wheel speed targets in `m/s`
- `M,ch,pwm` : debug motor pwm command
- `E,ch` : debug encoder read command
- `STOP` : stop current action

## OpenRF1 to Pi

- `CSR_RF1_READY`
- `ACK:W`
- `ACK:M`
- `ACK:E`
- `ACK:STOP`
- `ERR:...`
- `VEL,rt1,rt2,rt3,rt4,tg1,tg2,tg3,tg4`
- `PWM,p1,p2,p3,p4`
- `ENC,...`
- `DBG,...`

## Current observed behavior

- telemetry (`VEL`, `PWM`) streams immediately after port open
- `CSR_RF1_READY` was not observed in the current smoke test window
- `ACK:E`, `ACK:M`, `ACK:STOP`, and `ACK:W` were observed
