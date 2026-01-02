from machine import Pin
import asyncio
from neopixel import NeoPixel
from utils import Button


led_pin = Pin(14, Pin.OUT)  # set GPIO0 to output to drive NeoPixels
np = NeoPixel(led_pin, 64)  # create NeoPixel driver on GPIO0 for 2 pixels

# button1 = Button(Pin(7, Pin.IN, Pin.PULL_UP)). # Pin is created outside Button class
button1 = Button(7) # pin is created inside Button class

brightness = 0.1


async def np_blink(cycles=4,interval_ms=50):
    for _ in range(cycles):
        np[0] = (int(255 * brightness), int(255 * brightness), int(255 * brightness))
        np.write()
        await asyncio.sleep_ms(interval_ms)
        np[0] = (0, 0, 0)
        np.write()
        await asyncio.sleep_ms(interval_ms)


async def main():
    while True:
        button1.update()

        # Time-critical MIDI sends would go here - executed immediately without await
        # Example: midi.send_note_on(channel, note, velocity)
        # This runs synchronously and doesn't yield to other tasks

        if button1.was_pressed():
            print("short press start")
            np[0] = (int(255 * brightness), int(255 * brightness), int(255 * brightness))
            np.write()

        if button1.was_long_pressed():
            print("LONG PRESS → change mode")
            asyncio.create_task(np_blink())  # Background task, non-blocking

        if button1.was_released():
            print("released")
            np[0] = (0, 0, 0)
            np.write()

        await asyncio.sleep_ms(1)  # Shorter sleep = tighter MIDI timing (1ms = ~1000Hz loop)


asyncio.run(main())
