from machine import Pin
import asyncio
from neopixel import NeoPixel
from utils import Button

NUM_LEDS = 25
led_pin = Pin(38, Pin.OUT) 
np = NeoPixel(led_pin, NUM_LEDS)  

brightness = 0.1 # we need to stay low (probably max 30%), otherwise the power supply (USB) can't cope


def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB. h: 0-360, s: 0-1, v: 0-1"""
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


def set_all_leds(color):
    color = tuple(int(c * brightness) for c in color)
    for i in range(NUM_LEDS):
        np[i] = color
    np.write()

async def main():
    hue = 0
    while True:
        color = hsv_to_rgb(hue, 1.0, 1.0)
        color = tuple(int(c * brightness) for c in color)
        
        # Set all LEDs to the same color
        for i in range(NUM_LEDS):
            np[i] = color
        np.write()
        
        await asyncio.sleep_ms(10)
        hue = (hue + 5) % 360  # Cycle through colors

asyncio.run(main())
