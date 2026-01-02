"""
MicroPython entry point for Chord Machine.

Run this file on the ESP32-S3 to start the chord machine.
"""
import asyncio
from hal_mcu import create_mcu_hardware_port
from lib.chord_machine import ChordMachineApp


async def main():
    """Main async entry point."""
    print("Initializing Chord Machine...")

    # Create hardware port for this platform
    hardware = create_mcu_hardware_port()

    # Create application with MIDI channel 1 (index 0)
    app = ChordMachineApp(
        hardware,
        midi_channel=0,
        velocity=100,
        root_note=60,  # C4
    )

    print("========================================")
    print("  CHORD MACHINE READY")
    print("========================================")
    print("Buttons 1-7: Play chords I-VII")
    print("Button 8: Toggle mode / Reset (long)")
    print("Encoder: Change scale (play mode)")
    print("         Change root note (root mode)")
    print("Encoder button: Cycle modes")
    print("========================================")

    try:
        while True:
            app.update()
            await asyncio.sleep_ms(1)  # ~1000Hz update rate for responsive MIDI
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        app.cleanup()
        print("Chord Machine stopped.")


# Run the main loop
asyncio.run(main())
