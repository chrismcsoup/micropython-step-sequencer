# Platform-independent MIDI routing logic
class PlatformEnv:
    """
    Platform-specific environment abstraction.
    Subclasses implement platform-specific MIDI sending and scheduling.
    """

    def send_midi_note_on(self, note: int, velocity: int = 100) -> None:
        raise NotImplementedError("Subclass must implement send_midi_note_on")

    def send_midi_note_off(self, note: int, velocity: int = 64) -> None:
        raise NotImplementedError("Subclass must implement send_midi_note_off")

    def schedule_note_off(self, note: int, velocity: int, delay_ms: int) -> None:
        """Schedule a Note Off after the given delay (ms)."""
        raise NotImplementedError("Subclass must implement schedule_note_off")


class MIDIRouter:
    """
    Platform-independent MIDI message routing logic.
    This module contains only the logic for routing MIDI events,
    with no browser/DOM or platform-specific code.
    """
    
    def __init__(self, platform_env: PlatformEnv, base_note: int = 60, channel: int = 2):
        """
        Initialize the MIDI router.
        
        Args:
            platform_env: Platform-specific environment for sending MIDI
            base_note: Base MIDI note number (0-127)
            channel: MIDI channel (0-15)
        """
        self.platform_env = platform_env
        self.base_note = max(0, min(127, base_note))
        self.channel = max(0, min(15, channel))
        self.transpose = 0
    
    def set_transpose(self, semitones: int) -> None:
        """Set the transpose offset in semitones."""
        self.transpose = int(semitones)
    
    def send_note(self, velocity_on: int = 100, velocity_off: int = 64, duration_ms: int = 300) -> None:
        """
        Send a MIDI note (on and off).
        
        Args:
            velocity_on: Velocity for note on (0-127)
            velocity_off: Velocity for note off (0-127)
            duration_ms: Duration in milliseconds before note off
        """
        note = max(0, min(127, self.base_note + self.transpose))
        
        # Send note on
        self.platform_env.send_midi_note_on(note, velocity_on)

        # Schedule note off via platform environment (no asyncio)
        self.platform_env.schedule_note_off(note, velocity_off, duration_ms)


# Pure logic module: no JS imports here to remain MicroPython-friendly.
