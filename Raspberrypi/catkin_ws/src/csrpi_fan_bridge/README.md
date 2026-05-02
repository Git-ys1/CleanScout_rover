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
- servo signal: `GPIO12` / pin 32

## Frozen behavior

- relay controls the shared 12V main enable for both fans
- PWM A controls fan A speed
- PWM B controls fan B speed
- lid servo must open before relay and PWM are allowed
- stop order is always: PWM to 0, then relay off
- lid close is executed after both PWM channels are zero and relay is off

## Current note

The active implementation currently uses `RPi.GPIO` for minimal verification on this Pi image.
The frozen target direction is still `25 kHz` PWM with a more robust hardware PWM route if needed in later rounds.

FG lines are open collector and should be externally pulled up to `3.3V` for reliable counting.

## Active ROS interface

Input topics:

- `/fans/enable` (`std_msgs/Bool`)
- `/fan_a/pwm_percent` (`std_msgs/Float32`)
- `/fan_b/pwm_percent` (`std_msgs/Float32`)

Output topics:

- `/fan_a/rpm` (`std_msgs/Float32`)
- `/fan_b/rpm` (`std_msgs/Float32`)
- `/fan_a/fg_in_rpm` (`std_msgs/Float32`)
- `/fan_a/fg_out_rpm` (`std_msgs/Float32`)
- `/fan_b/fg_in_rpm` (`std_msgs/Float32`)
- `/fan_b/fg_out_rpm` (`std_msgs/Float32`)
- `/fan_lid/state` (`std_msgs/Bool`)
- `/fans/state_summary` (`std_msgs/String`)
