import time
from pyb import Pin, Timer


SWEEP_DELAY_MS = 900
PWM_VALUES = (2.5, 5.0, 7.5, 10.0, 12.5)

tim = Timer(2, freq=50)
claw = tim.channel(3, Timer.PWM, pin=Pin("B10"), pulse_width_percent=7.5)


while True:
    for duty in PWM_VALUES:
        print("PWM_SWEEP -> {:.1f}".format(duty))
        claw.pulse_width_percent(duty)
        time.sleep_ms(SWEEP_DELAY_MS)
