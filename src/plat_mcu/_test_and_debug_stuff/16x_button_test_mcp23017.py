# This is the first test on the "real" hardware with MCP23017 I2C GPIO expander.
# Pins have changed compared to the breadboard setup.
# It sets up 16 buttons connected to the MCP23017 and lights up corresponding

from machine import Pin, I2C
import asyncio
from neopixel import NeoPixel
from utils import Button
from lib.mcp23017 import MCP23017


# NeoPixel matrix setup (8x8 = 64 LEDs)
led_pin = Pin(14, Pin.OUT)
np = NeoPixel(led_pin, 64)
brightness = 0.1

# Colors for pressed buttons (scaled by brightness)
def color(r, g, b):
    return (int(r * brightness), int(g * brightness), int(b * brightness))

COLOR_ON = color(0, 255, 0)   # Green when pressed
COLOR_OFF = (0, 0, 0)         # Off when not pressed

# MCP23017 setup - I2C on ESP32-S3
i2c = I2C(0, scl=Pin(39), sda=Pin(40))
mcp = MCP23017(i2c, address=0x20)

# Configure MCP23017 pins 0-15 as inputs with pullup
for pin_num in range(16):
    mcp.pin(pin_num, mode=1, pullup=True)  # Mode 1 = input

# Create 16 Button objects using MCP23017 virtual pins
buttons = [Button(mcp[i]) for i in range(16)]


def button_to_led_index(button_index):
    """Map button index (0-15) to NeoPixel LED index on 8x8 matrix.
    
    Maps buttons to first 2 rows of the matrix, mirrored:
    Buttons 0-7  -> Row 0 (LEDs 7-0, reversed)
    Buttons 8-15 -> Row 1 (LEDs 15-8, reversed)
    """
    row = button_index // 8
    col = button_index % 8
    return row * 8 + (7 - col)


def update_leds():
    """Update LED states based on button states."""
    for i, btn in enumerate(buttons):
        led_idx = button_to_led_index(i)
        if btn.is_pressed():
            np[led_idx] = COLOR_ON
        else:
            np[led_idx] = COLOR_OFF
    np.write()


async def button_poll_task():
    """Continuously poll all buttons and update LEDs."""
    print("Starting 16-button test...")
    print("Press buttons 0-15 on MCP23017 to light up corresponding LEDs")
    
    while True:
        # Update all button states
        for btn in buttons:
            btn.update()
        
        # Update LEDs to reflect button states
        update_leds()
        
        # Small delay to prevent busy-waiting
        await asyncio.sleep_ms(10)


async def main():
    # Clear all LEDs at startup
    for i in range(64):
        np[i] = COLOR_OFF
    np.write()
    
    # Run the button polling task
    await button_poll_task()


asyncio.run(main())
