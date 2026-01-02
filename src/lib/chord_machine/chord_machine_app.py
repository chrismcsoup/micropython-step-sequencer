"""
Main Chord Machine Application.
Ties together business logic, UI state, and hardware.
Platform-independent - receives hardware through dependency injection.
"""
from .chord_engine import ChordEngine
from .ui_state import UIState, Event


class ChordMachineApp:
    """
    Main application class for the Chord Machine.
    Platform-independent - receives hardware through dependency injection.
    """

    # Color constants for LED feedback
    COLOR_OFF = (0, 0, 0)
    COLOR_CHORD_ACTIVE = (0, 255, 0)  # Green when chord playing
    COLOR_MODE_PLAY = (0, 0, 50)  # Dim blue for play mode
    COLOR_MODE_SETTINGS = (50, 50, 0)  # Dim yellow for settings

    def __init__(self, hardware, midi_channel=0, velocity=100, root_note=60):
        """
        Initialize the Chord Machine.

        Args:
            hardware: HardwarePort instance with all HAL implementations
            midi_channel: MIDI channel 0-15
            velocity: Default note velocity 0-127
            root_note: Default root note (60 = C4)
        """
        # Business logic
        self.chord_engine = ChordEngine(root_note=root_note, scale_name="major")

        # UI State
        self.ui_state = UIState(self.chord_engine)

        # Hardware (injected)
        self.hw = hardware

        # Config
        self.midi_channel = midi_channel
        self.velocity = velocity

        # Track active notes for proper note-off
        self._active_notes = []

        # Subscribe to UI events
        self._setup_event_handlers()

        # Initial display update
        self._update_display()

    def _setup_event_handlers(self):
        """Connect UI state events to hardware actions."""

        def on_chord_triggered(data):
            # Send MIDI
            self.hw.midi_output.send_chord_on(
                self.midi_channel, data["notes"], self.velocity
            )
            self._active_notes = list(data["notes"])

            # Update LEDs
            self.hw.led_matrix.set_button_led(data["degree"], self.COLOR_CHORD_ACTIVE)
            self.hw.led_matrix.show_chord_visualization(
                data["notes"], self.chord_engine.root_note
            )

            # Update display
            self.hw.display.show_chord(data["name"], data["numeral"])

        def on_chord_released(data):
            # Send MIDI note offs
            if self._active_notes:
                self.hw.midi_output.send_chord_off(self.midi_channel, self._active_notes)
                self._active_notes = []

            # Update LEDs
            self.hw.led_matrix.set_button_led(data["degree"], self.COLOR_OFF)
            self.hw.led_matrix.clear()

        def on_scale_changed(data):
            self._update_display()

        def on_mode_changed(data):
            self._update_display()
            # Show mode indicator on LEDs
            mode_color = (
                self.COLOR_MODE_PLAY
                if data["mode"] == "play"
                else self.COLOR_MODE_SETTINGS
            )
            self.hw.led_matrix.set_button_led(7, mode_color)

        def on_root_changed(data):
            self._update_display()

        # Register handlers
        self.ui_state.subscribe(Event.CHORD_TRIGGERED, on_chord_triggered)
        self.ui_state.subscribe(Event.CHORD_RELEASED, on_chord_released)
        self.ui_state.subscribe(Event.SCALE_CHANGED, on_scale_changed)
        self.ui_state.subscribe(Event.MODE_CHANGED, on_mode_changed)
        self.ui_state.subscribe(Event.ROOT_CHANGED, on_root_changed)

    def _update_display(self):
        """Update display with current state."""
        display_data = self.ui_state.get_display_data()
        self.hw.display.show_scale(display_data["scale_name"], display_data["octave"])
        self.hw.display.show_mode(display_data["mode"])
        if display_data["active_chord"]:
            self.hw.display.show_chord(
                display_data["active_chord"]["name"],
                display_data["active_chord"]["numeral"],
            )
        self.ui_state.clear_display_dirty()

    def update(self):
        """
        Main update loop - call this frequently.
        Polls inputs and processes state changes.
        """
        # Poll hardware inputs
        self.hw.update_inputs()

        # Check encoder rotation
        encoder_delta = self.hw.encoder.get_delta()
        if encoder_delta != 0:
            self.ui_state.update_encoder(encoder_delta)

        # Check encoder button for mode toggle
        if self.hw.encoder.was_button_pressed():
            self.ui_state.toggle_mode()
            self.hw.encoder.set_value(0)

        # Check each button (0-6 for chords I-VII, 7 for special)
        for i in range(8):
            if i < 7:  # Chord buttons
                if self.hw.buttons.was_pressed(i):
                    self.ui_state.trigger_chord(i)

                if self.hw.buttons.was_released(i):
                    self.ui_state.release_chord(i)
            else:
                # Button 8 (index 7) for special functions
                if self.hw.buttons.was_long_pressed(i):
                    # Reset to default scale
                    self.chord_engine.scale_name = "major"
                    self.chord_engine.root_note = 60
                    self.ui_state.set_scale(0)

                if self.hw.buttons.was_pressed(i):
                    # Toggle mode on short press
                    self.ui_state.toggle_mode()

        # Update display if dirty
        if self.ui_state.display_dirty:
            self._update_display()

        # Push output updates
        self.hw.update_outputs()

    def cleanup(self):
        """Clean shutdown - turn off all notes and LEDs."""
        # Send note offs for any active notes
        if self._active_notes:
            self.hw.midi_output.send_chord_off(self.midi_channel, self._active_notes)
            self._active_notes = []

        # Clear all LEDs
        self.hw.led_matrix.clear()
        self.hw.led_matrix.update()

        # Clear display
        self.hw.display.clear()
        self.hw.display.update()

    def set_velocity(self, velocity):
        """Set the default velocity for notes."""
        self.velocity = max(0, min(127, velocity))

    def set_midi_channel(self, channel):
        """Set the MIDI channel."""
        self.midi_channel = max(0, min(15, channel))
