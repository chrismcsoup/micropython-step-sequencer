from machine import Pin, I2C
from lib.mpr121 import MPR121
import time

i2c = I2C(scl=Pin(1), sda=Pin(2))
mpr = MPR121(i2c, 0x5A)

while True:
	print(mpr.touched())
	time.sleep_ms(100)