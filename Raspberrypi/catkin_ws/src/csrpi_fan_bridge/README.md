# csrpi_fan_bridge

`csrpi_fan_bridge` is the Raspberry Pi side fan control bridge for `C-2.3.2B`.

## Frozen pins

- relay enable: `GPIO17` / pin 11
- PWM output: `GPIO18` / pin 12
- FG front: `GPIO23`
- FG rear: `GPIO24`

## Frozen behavior

- relay controls the 12V main enable
- PWM controls the fan speed
- stop order is always: PWM to 0, then relay off

## Current note

The Python scripts expect `pigpio` and `pigpiod` to be available on the Pi.
That is the frozen implementation direction for `25 kHz` PWM.
