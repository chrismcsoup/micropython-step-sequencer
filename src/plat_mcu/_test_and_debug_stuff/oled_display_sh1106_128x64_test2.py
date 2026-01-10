# Demo program for SH1106 OLED display 128x64 Pixel via I2C 0x3C.
# SH1106 has 132x64 internal RAM with column offset, different from SSD1306.
from machine import Pin, I2C
from lib.sh1106.sh1106 import SH1106_I2C
import time

# Initialize I2C and OLED display (default address: 0x3C)
i2c = I2C(0, scl=Pin(1), sda=Pin(2))

# Small delay to let I2C stabilize
# time.sleep_ms(100)

display = SH1106_I2C(128, 64, i2c, addr=0x3c)
display.sleep(False)
display.fill(0)
display.text('Testing 1', 0, 0, 1)
display.show()