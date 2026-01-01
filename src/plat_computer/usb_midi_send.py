#!/usr/bin/env python3
"""
Send MIDI test messages via USB MIDI interface.
"""

import mido
import time
import sys

# The raw MIDI bytes: Note On (0x90 0x3C 0x64) + Note Off (0x80 0x3C 0x00)
# 0x90 = Note On, channel 1
# 0x3C = Note 60 (Middle C)
# 0x64 = Velocity 100
# 0x80 = Note Off, channel 1
# 0x3C = Note 60
# 0x00 = Velocity 0

TEST = b"\x90\x3C\x64\x80\x3C\x00"


def list_outputs():
    """List all available MIDI output ports."""
    outputs = mido.get_output_names()
    if not outputs:
        print("No MIDI output ports found!")
        return []
    print("Available MIDI outputs:")
    for i, name in enumerate(outputs):
        print(f"  [{i}] {name}")
    return outputs


def send_test_message(port_name=None):
    """Send the test MIDI message."""
    outputs = list_outputs()
    if not outputs:
        sys.exit(1)

    # Use specified port or first available
    if port_name is None:
        port_name = outputs[0]
        print(f"\nUsing first available port: {port_name}")

    try:
        with mido.open_output(port_name) as outport:
            print(f"Opened port: {port_name}")
            print("Looping MIDI test data. Press Ctrl+C to stop.\n")

            # Parse raw bytes into MIDI messages
            # Note On: channel 1, note 60, velocity 100
            note_on = mido.Message("note_on", channel=0, note=0x3C, velocity=0x64)
            # Note Off: channel 1, note 60, velocity 0
            note_off = mido.Message("note_off", channel=0, note=0x3C, velocity=0x00)

            count = 0
            while True:
                count += 1
                print(f"[{count}] Sending: {note_on}")
                outport.send(note_on)

                time.sleep(0.5)  # Hold note for 500ms

                print(f"[{count}] Sending: {note_off}")
                outport.send(note_off)

                time.sleep(0.5)  # Wait before next loop

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Optional: pass port name as command line argument
    port = sys.argv[1] if len(sys.argv) > 1 else None
    send_test_message(port)
