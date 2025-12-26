# PyScript bootstrap to bridge Python MIDI router to WebMidi.js
from js import window

# Expect core classes to be defined by a prior <py-script src="app.py">.
# PyScript executes scripts in a shared interpreter, so we can reference
# names defined earlier without importing a module file.

try:
    PlatformEnv
    MIDIRouter
except NameError:
    print("PyScript bootstrap error: 'PlatformEnv'/'MIDIRouter' not found. Ensure app.py is loaded before bootstrap.py.")
else:
    class JSPlatformEnv(PlatformEnv):
        """Bridge MIDI calls from MicroPython to WebMidi.js via JS helpers."""
        def send_midi_note_on(self, note: int, velocity: int = 100) -> None:
            if hasattr(window, "js_midi_note_on"):
                window.js_midi_note_on(int(note), int(velocity))
        def send_midi_note_off(self, note: int, velocity: int = 64) -> None:
            if hasattr(window, "js_midi_note_off"):
                window.js_midi_note_off(int(note))
        def schedule_note_off(self, note: int, velocity: int, delay_ms: int) -> None:
            # Delegate scheduling to JS to avoid MicroPython async requirements
            if hasattr(window, "js_schedule_note_off"):
                window.js_schedule_note_off(int(note), int(delay_ms))

    # Initialize environment and router
    platform_env = JSPlatformEnv()
    router = MIDIRouter(platform_env, base_note=60, channel=2)

    # Expose router to JavaScript
    window.midiRouter = router

    print("PyScript bootstrap: MIDI router initialized with WebMidi.js bridge")
