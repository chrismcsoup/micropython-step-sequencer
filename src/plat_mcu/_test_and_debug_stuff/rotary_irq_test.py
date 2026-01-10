import time
from machine import Pin
from lib.rotary.rotary_irq_esp import RotaryIRQ

r = RotaryIRQ(
    pin_num_clk=35,
    pin_num_dt=34,
    min_val=0,
    max_val=5,
    pull_up=True,
    reverse=False,
    range_mode=RotaryIRQ.RANGE_WRAP,
)

button = Pin(33, Pin.IN)

val_old = r.value()
val_old_button = button.value()
while True:
    val_new = r.value()
    val_new_button = button.value()
    if val_new_button != val_old_button:
        val_old_button = val_new_button
        print("button =", val_new_button)

    if val_old != val_new:
        val_old = val_new
        print("result =", val_new)

    time.sleep_ms(50)
