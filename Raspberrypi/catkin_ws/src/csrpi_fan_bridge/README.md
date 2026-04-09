# csrpi_fan_bridge

`csrpi_fan_bridge` is the Raspberry Pi side fan control bridge for `C-2.3.2B`.

## Frozen pins

- relay enable: `GPIO17` / pin 11
- fan A PWM: `GPIO18` / pin 12
- fan B PWM: `GPIO19` / pin 35
- fan A FG_in: `GPIO23`
- fan A FG_out: `GPIO24`
- fan B FG_in: `GPIO25`
- fan B FG_out: `GPIO16`

## Frozen behavior

- relay controls the shared 12V main enable for both fans
- PWM A controls fan A speed
- PWM B controls fan B speed
- stop order is always: PWM to 0, then relay off

## Current note

The active implementation currently uses `RPi.GPIO` for minimal verification on this Pi image.
The frozen target direction is still `25 kHz` PWM with a more robust hardware PWM route if needed in later rounds.

FG lines are open collector and should be externally pulled up to `3.3V` for reliable counting.
