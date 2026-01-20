from machine import Pin
import asyncio
from neopixel import NeoPixel
from utils import Button


led_pin = Pin(3, Pin.OUT)
np = NeoPixel(led_pin, 16)

brightness = 0.1

# White color scaled by brightness
def color(r, g, b):
    return (int(r * brightness), int(g * brightness), int(b * brightness))

COLOR_WHITE = color(255, 255, 255)
COLOR_OFF = (0, 0, 0)


def hsv_to_rgb(h, s, v):
    """Convert HSV color to RGB. h: 0-360, s: 0-1, v: 0-1"""
    if s == 0.0:
        return (int(v * 255), int(v * 255), int(v * 255))
    
    h = h / 60.0
    i = int(h)
    f = h - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    
    i = i % 6
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    
    return (int(r * 255 * brightness), int(g * 255 * brightness), int(b * 255 * brightness))


async def main():
    print("Rainbow wave animation...")
    
    offset = 0
    
    while True:
        # Update each LED with a rainbow color based on position + offset
        for i in range(16):
            # Calculate hue for this LED (0-360 degrees)
            # Spread the rainbow across the strip and add the offset for animation
            hue = ((i * 360 / 16) + offset) % 360
            np[i] = hsv_to_rgb(hue, 1.0, 1.0)
        
        np.write()
        
        # Increment offset to animate the wave
        offset = (offset + 2) % 360
        
        await asyncio.sleep_ms(20)


# # Blinking white test (commented out)
# async def main():
#     print("Blinking all 16 LEDs in white...")
#     
#     while True:
#         # Turn all LEDs on (white)
#         for i in range(16):
#             np[i] = COLOR_WHITE
#         np.write()
#         await asyncio.sleep_ms(500)
#         
#         # Turn all LEDs off
#         for i in range(16):
#             np[i] = COLOR_OFF
#         np.write()
#         await asyncio.sleep_ms(500)


asyncio.run(main())
