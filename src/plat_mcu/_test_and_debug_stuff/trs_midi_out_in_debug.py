# This is a test where you connect the trs midi in to midi out. And see if
# the sent bytes are received back. We can do this via 3.5mm stereo cable via the midi perfboard or
# by wiring TX->RX directly with a jumper cable.

from machine import UART, Pin
import time

TX_PIN = 39   # your TX
RX_PIN = 40   # your RX
UART_ID = 1

uart = UART(UART_ID, baudrate=31250, bits=8, parity=None, stop=1,
            tx=Pin(TX_PIN, Pin.OUT), rx=Pin(RX_PIN, Pin.IN))

# debug pin to see that code is actually sending
DBG = Pin(2, Pin.OUT)  # change to any LED pin you have, or ignore

TEST = b"\x90\x3C\x64\x80\x3C\x00"

def read_some(timeout_ms=200):
    deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
    buf = bytearray()
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if uart.any():
            chunk = uart.read()
            if chunk:
                buf.extend(chunk)
                break
        time.sleep_ms(1)
    return bytes(buf) if buf else None

print("Loopback: connect TX -> RX with a jumper!")

while True:
    DBG.value(1)
    uart.write(TEST)
    DBG.value(0)

    got = read_some(200)
    if got:
        print("RX:", " ".join(f"{b:02X}" for b in got))
    else:
        print("TIMEOUT (no bytes)")
    time.sleep_ms(500)
