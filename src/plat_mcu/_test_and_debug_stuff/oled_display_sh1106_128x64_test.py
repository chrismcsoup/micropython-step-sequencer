# Demo program for SH1106 OLED display 128x64 Pixel via I2C 0x3C.
# SH1106 has 132x64 internal RAM with column offset, different from SSD1306.
from machine import Pin, I2C
from lib.sh1106.sh1106 import SH1106_I2C
import time

# Initialize I2C and OLED display (default address: 0x3C)
i2c = I2C(0, scl=Pin(1), sda=Pin(2))

# Small delay to let I2C stabilize
time.sleep_ms(100)

display = SH1106_I2C(128, 64, i2c, addr=0x3c)

# Power cycle to clear
display.poweroff()
time.sleep_ms(100)
display.poweron()
time.sleep_ms(100)

# Clear display
display.fill(0)
display.show()
time.sleep_ms(50)

# Flip display (try True or False to fix orientation)
display.flip(True)

# Draw text on 4 lines
display.fill(0)
display.text('FRESH TEST OK!', 0, 0, 1)
display.text('ABCDEFGHIJK', 0, 16, 1)
display.text('1234567890', 0, 32, 1)
display.text('SUCCESS!', 0, 48, 1)
display.show()
print("Done")
