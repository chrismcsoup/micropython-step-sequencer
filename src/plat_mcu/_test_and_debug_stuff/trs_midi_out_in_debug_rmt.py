# Test script for RMT-based software MIDI TX with loopback verification
# Connect RMT MIDI OUT (TRS 3, GPIO 38) to MIDI IN (TRS, GPIO 1) via cable
# and verify the bytes sent are received correctly.

import sys
sys.path.insert(0, '/lib')  # For deployed libs
sys.path.insert(0, 'src/plat_mcu')  # For hal_mcu when running via mpremote

from machine import Pin, UART
import time

# Import the actual SoftwareMidiTx class from hal_mcu
from hal_mcu import SoftwareMidiTx

# Pin configuration (matches hal_mcu.py PinConfig)
TX_PIN = 37   # RMT MIDI TX (TRS 3)
RX_PIN = 1    # MIDI IN
UART_ID = 1   # Hardware UART for receiving


def read_some(uart, timeout_ms=200):
    """Read bytes from UART with timeout."""
    deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
    buf = bytearray()
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if uart.any():
            chunk = uart.read()
            if chunk:
                buf.extend(chunk)
                # Small delay to catch any remaining bytes
                time.sleep_ms(10)
        time.sleep_ms(1)
    return bytes(buf) if buf else None


def format_hex(data):
    """Format bytes as hex string."""
    return ' '.join('%02X' % b for b in data)


def main():
    print("=" * 50)
    print("RMT MIDI OUT -> MIDI IN Loopback Test")
    print("=" * 50)
    print(f"TX: GPIO {TX_PIN} (RMT software UART)")
    print(f"RX: GPIO {RX_PIN} (hardware UART{UART_ID})")
    print()
    print("Connect TRS MIDI OUT 3 to TRS MIDI IN with a cable!")
    print()
    
    # Create RMT MIDI TX (pass Pin object as hal_mcu.py expects)
    tx_pin = Pin(TX_PIN, Pin.OUT)
    midi_tx = SoftwareMidiTx(tx_pin)
    print("SoftwareMidiTx initialized")
    
    # Create hardware UART for receiving
    # Need a dummy TX pin since library requires it
    uart = UART(
        UART_ID,
        baudrate=31250,
        bits=8,
        parity=None,
        stop=1,
        tx=Pin(36),  # Dummy TX (MIDI OUT 1), we only use RX here
        rx=Pin(RX_PIN, Pin.IN)
    )
    print(f"UART{UART_ID} RX initialized")
    print()
    print("Sending MIDI test messages...")
    print("Press Ctrl+C to stop")
    print()
    
    # Test data: Note On (C4, velocity 100), Note Off (C4)
    TEST_NOTE_ON = bytes([0x90, 0x3C, 0x64])   # Channel 1 Note On, C4, vel 100
    TEST_NOTE_OFF = bytes([0x80, 0x3C, 0x00])  # Channel 1 Note Off, C4
    
    count = 0
    try:
        while True:
            count += 1
            
            # Clear any stale data in RX buffer
            uart.read()
            
            # Send Note On
            print(f"[{count}] TX: 90 3C 64 ... ", end="")
            midi_tx.write(TEST_NOTE_ON)
            time.sleep_ms(50)  # Let RMT finish
            
            got = read_some(uart, 100)
            if got == TEST_NOTE_ON:
                print("RX: " + format_hex(got) + " ✓")
            elif got:
                print("RX: " + format_hex(got) + " ✗ MISMATCH")
            else:
                print("TIMEOUT (no bytes received)")
            
            time.sleep_ms(200)
            
            # Send Note Off
            print(f"[{count}] TX: 80 3C 00 ... ", end="")
            midi_tx.write(TEST_NOTE_OFF)
            time.sleep_ms(50)  # Let RMT finish
            
            got = read_some(uart, 100)
            if got == TEST_NOTE_OFF:
                print("RX: " + format_hex(got) + " ✓")
            elif got:
                print("RX: " + format_hex(got) + " ✗ MISMATCH")
            else:
                print("TIMEOUT (no bytes received)")
            
            time.sleep_ms(300)
            
    except KeyboardInterrupt:
        print("\nStopped")


if __name__ == "__main__":
    main()
