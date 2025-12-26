# This is a test of two handsoldered SK6812-Mini-E RGB Leds which are compatible with the
# neopixel protocol. I got it from amazon.de (https://amzn.eu/d/14DKVMW)

# The soldering is tricky there is a youtube video explaining the handsoldering: https://www.youtube.com/watch?v=oL
# I am still strugeling, but for me it helped to use stranded wire and adding flux to the pads wire

# Connection
# SK6812 Mini-E VDD <-> PICO VBUS (=5V)
# SK6812 Mini-E DIN <-> PICO GP0
# SK6812 Mini-E GND <-> PICO GND
#
# NOTE: Connecting it like that runs the LED without the specs and I am surprised it works.
# Because based on the specs, the DIN HIGH must be at least 0.7*VDD which is 3.5V with 5 V VDD. The
# Pico IO HIGH provides 3.3V which is below 3.5V so it shouldn't work.

# The workaround I found from leoleosuper on reddit (https://www.reddit.com/r/fightsticks/comments/182vumd/comment/ku6b12a/)
# suggests that for the first (only for the first) LED you add a diode between the 5V from the PICO
# and the VDD. The diode has a voltage drop that is enough to get the 3.3V of the logic within the
# Specs and the VDD is also still high enough to be in the VDD Specs (>3.5V). The DOUT of the
# first LED is scaled upwards so that all further LEDS can be run with 5V without a diode.
# One potential disadvantage is, that the first LED might be not as bright as the others.


from machine import Pin
from utime import sleep
from neopixel import NeoPixel


led_pin = Pin(14, Pin.OUT)  # set GPIO0 to output to drive NeoPixels
np = NeoPixel(led_pin, 64)  # create NeoPixel driver on GPIO0 for 2 pixels


def wheel(pos, brightness=0.5):
    """Convert a number (0-255) to a color cycling through RGB with adjustable brightness."""
    pos = pos % 256  # Ensure the position is within 0-255
    brightness = max(0.0, min(1.0, brightness))  # Clamp brightness between 0.0 and 1.0

    if pos < 85:
        r, g, b = (255 - pos * 3, pos * 3, 0)
    elif pos < 170:
        pos -= 85
        r, g, b = (0, 255 - pos * 3, pos * 3)
    else:
        pos -= 170
        r, g, b = (pos * 3, 0, 255 - pos * 3)

    # Apply brightness scaling
    return (int(r * brightness), int(g * brightness), int(b * brightness))


brightness = (
    0.1  # looks like 0.05 is the smallest smooth tranistioning brightness for the SK6812 Mini-E
)
counter = 0
move = 0
while True:
    try:
#        move = 1 if move == 0 else 0
        for i in range(64):
            # if (i + move) % 2 == 0:
            #     np[i] = (0, 0, 0)
            # else:
            np[i] = wheel(counter, brightness)
        # np[0] = (255,0,0)    # type: ignore # set first pixel to red (Red=255, Green=0, Blue=0)
        # np[0] = wheel(counter, brightness)  # type: ignore # wheel through the colors
        # np[1] = wheel(255 - counter, brightness)  # type: ignore # wheel backwards through the colors
        np.write()  # write data to all pixels
        counter = counter + 1 if counter < 255 else 0  # limit counter range from 0 - 255
        print("counter: ", counter)
        sleep(0.1)
    except KeyboardInterrupt:
        break
np.fill((0, 0, 0))
np.write()
print("Finished.")
