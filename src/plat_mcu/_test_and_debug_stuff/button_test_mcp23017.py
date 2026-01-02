from machine import Pin, I2C
import asyncio
from neopixel import NeoPixel
from utils import Button
from lib.mcp23017 import MCP23017, Rotary


led_pin = Pin(14, Pin.OUT)  # set GPIO0 to output to drive NeoPixels
np = NeoPixel(led_pin, 64)  # create NeoPixel driver on GPIO0 for 2 pixels
brightness = 0.1


# mcp23017 setup pins on esp32
i2c = I2C(0,scl=Pin(6), sda=Pin(5))
# interrupt pin on esp32
p4 = Pin(4, mode=Pin.IN)
mcp = MCP23017(i2c, address=0x20)
# Configure MCP23017 pins
for pin_num in range(8):
    mcp.pin(pin_num, mode=0, value=0)  # Configure all pins as output with value 0
for pin_num in range(8, 16):
    mcp.pin(pin_num, mode=1, pullup=True)  # Configure pins 8-15 as input with pullup, Mode 1 = input, Mode 0 = output

button1 = Button(mcp[8])

# encoder pins on mcp23017 (NOT esp32 pins)
clk_pin = 7
dt_pin = 6
sw_pin = 5


async def np_blink(cycles=4,interval_ms=50):
    for _ in range(cycles):
        np[0] = (int(255 * brightness), int(255 * brightness), int(255 * brightness))
        np.write()
        await asyncio.sleep_ms(interval_ms)
        np[0] = (0, 0, 0)
        np.write()
        await asyncio.sleep_ms(interval_ms)

# simpler callback with just values
def cb(val, sw):
	print('value: {}, switch: {}'.format(val, sw))

# init
r = Rotary(mcp.porta, p4, clk_pin, dt_pin, sw_pin, cb)

# add irq
r.start()


async def main():
    last_gpio_state = 0xFFFF  # Initialize to an invalid state to ensure first read triggers update
    while True:
        # Debug: print all MCP pin states (single read)
        try:
            gpio_state = mcp.gpio
            if gpio_state != last_gpio_state:
                last_gpio_state = gpio_state
                print(f"MCP pins: {bin(gpio_state)}")
        except OSError as e:
            print(f"I2C error: {e}")
            await asyncio.sleep_ms(100)
            continue
            
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
            r.value = 0  # reset encoder value

        if button1.was_released():
            print("released")
            np[0] = (0, 0, 0)
            np.write()

        await asyncio.sleep_ms(1)  # Increase interval for I2C stability


asyncio.run(main())
# remove irq
r.stop()