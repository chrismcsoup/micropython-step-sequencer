from machine import Pin
from utime import sleep
from neopixel import NeoPixel


led_pin = Pin(14, Pin.OUT)  # Pin 14 is the NeioPixel data pin for the ESP32-S3-MATRIX
np = NeoPixel(led_pin, 64)  # create NeoPixel driver on GPIO0 for 64 pixels


def color_all(r, g, b):
    for i in range(64):
            np[i] = (r, g, b)


color_all(r=0, g=0, b=0)
np.write()


def moving_dot(r, g, b, row, index, offset):
#offsetrange2
    np[((8*row)+(index+offset)%8)] = (r, g, b)

def wave(r, g, b, index, offset=0):
    for row in range(8):
        moving_dot(r=r, g=g, b=b, row=row, index=index, offset=row+offset)
    # moving_dot(r=0, g=0, b=10, row=1, index=i, offset=1)
    # moving_dot(r=0, g=0, b=10, row=2, index=i, offset=2)
    # moving_dot(r=0, g=0, b=10, row=3, index=i, offset=3)
    # moving_dot(r=0, g=0, b=10, row=4, index=i, offset=4)
    # moving_dot(r=0, g=0, b=10, row=5, index=i, offset=5)
    # moving_dot(r=0, g=0, b=10, row=6, index=i, offset=6)
    # moving_dot(r=0, g=0, b=10, row=7, index=i, offset=7)

distance = 9

while True:
    for i in range(8):
        # alles löschen 
        color_all(r=0, g=0, b=0)
        np.write()
        wave(r=0 ,g=15 ,b=0, index=i, offset=0)
        wave(r=0 ,g=15 ,b=0, index=i, offset=1)
        wave(r=0 ,g=15 ,b=0, index=i, offset=2)
        wave(r=0 ,g=15 ,b=0,index=i, offset=3)
        wave(r=5 ,g=5 ,b=5, index=i, offset=4)
        wave(r=5 ,g=5 ,b=5, index=i, offset=5)
        wave(r=5 ,g=5 ,b=5, index=i, offset=6)
        wave(r=5 ,g=5 ,b=5, index=i, offset=7)
        # moving_dot(r=0, g=0, b=10, row=0, index=i, offset=0)
        # moving_dot(r=0, g=0, b=10, row=1, index=i, offset=1)
        # moving_dot(r=0, g=0, b=10, row=2, index=i, offset=2)
        # moving_dot(r=0, g=0, b=10, row=3, index=i, offset=3)
        # moving_dot(r=0, g=0, b=10, row=4, index=i, offset=4)
        # moving_dot(r=0, g=0, b=10, row=5, index=i, offset=5)
        # moving_dot(r=0, g=0, b=10, row=6, index=i, offset=6)
        # moving_dot(r=0, g=0, b=10, row=7, index=i, offset=7)
       
        # moving_dot(r=0, g=10, b=0, row=0, index=i, offset=0+4)
        # moving_dot(r=0, g=10, b=0, row=1, index=i, offset=1+4)
        # moving_dot(r=0, g=10, b=0, row=2, index=i, offset=2+4)
        # moving_dot(r=0, g=10, b=0, row=3, index=i, offset=3+4)
        # moving_dot(r=0, g=10, b=0, row=4, index=i, offset=4+4)
        # moving_dot(r=0, g=10, b=0, row=5, index=i, offset=5+4)
        # moving_dot(r=0, g=10, b=0, row=6, index=i, offset=6+4)
        # moving_dot(r=0, g=10, b=0, row=7, index=i, offset=7+4)


        np.write()
        sleep(0.1)

