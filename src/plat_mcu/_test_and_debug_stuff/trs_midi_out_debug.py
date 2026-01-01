# TRS Type-A MIDI Out Debug Script

from machine import UART, Pin
import time

TX_PIN = 39  # <-- CHANGE ME to your wired TX GPIO

# UART(1) is usually free; baud 31250 is MIDI
midi = UART(1, baudrate=31250, bits=8, parity=None, stop=1, tx=Pin(TX_PIN))

def send_note_on(note=60, vel=100, ch=0):
    midi.write(bytes([0x90 | (ch & 0x0F), note & 0x7F, vel & 0x7F]))

def send_note_off(note=60, vel=0, ch=0):
    midi.write(bytes([0x80 | (ch & 0x0F), note & 0x7F, vel & 0x7F]))

def send_cc(cc=1, val=0, ch=0):
    midi.write(bytes([0xB0 | (ch & 0x0F), cc & 0x7F, val & 0x7F]))

# # Main test loop: 1s note + CC sweep
# while True:
#     channel = 0
#     send_note_on(60, 100, channel)
#     # quick CC sweep while note is on (makes analyzer capture easier)
#     for v in range(0, 128, 16):
#         send_cc(1, v, channel)   # Mod wheel
#         time.sleep_ms(30)
#     time.sleep_ms(400)
#     send_note_off(60, 0, channel)
#     time.sleep_ms(800)



while True:
    midi.write(b'\x90\x3C\x64')  # Note On
    time.sleep_ms(300)
    midi.write(b'\x80\x3C\x00')  # Note Off
    time.sleep_ms(700)


# Simple TX pin toggle test
# p = Pin(TX_PIN, Pin.OUT)
# while True:
#     p.value(1)
#     time.sleep(1)
#     p.value(0)
#     time.sleep(1)