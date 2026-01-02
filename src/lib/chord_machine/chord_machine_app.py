"""
Main Chord Machine Application.
Ties together business logic, UI state, and hardware.
Platform-independent - receives hardware through dependency injection.
"""
from .chord_engine import ChordEngine
from .ui_state import UIState, Event
from .constants import Color, Mode, Midi as MidiConst, Hardware


class ChordMachineApp:
    """
    Main application class for the Chord Machine.
    Platform-independent - receives hardware through dependency injection.
    """

    def __init__(self, hardware, midi_channel=MidiConst.CHANNEL_MIN, 
                 velocity=MidiConst.VELOCITY_DEFAULT, 
                 root_note=MidiConst.DEFAULT_ROOT_NOTE):
        """
        Initialize the Chord Machine.

        Args:
            hardware: HardwarePort instance with all HAL implementations
            midi_channel: MIDI channel 0-15
            velocity: Default note velocity 0-127
            root_note: Default root note (60 = C4)
        """
        # Business logic
        self.chord_engine = ChordEngine(root_note=root_note, scale_name=MidiConst.DEFAULT_SCALE)

        # UI State
        self.ui_state = UIState(self.chord_engine)

        # Hardware (injected)
        self.hw = hardware

        # Config
        self.midi_channel = midi_channel
        self.velocity = velocity

        # Track active notes per chord degree for proper note-off
        # Key: degree (0-6), Value: list of MIDI note numbers
        self._active_notes_by_degree = {}

        # Subscribe to UI events
        self._setup_event_handlers()

        # Initial display update
        self._update_display()

    def _setup_event_handlers(self):
        """Connect UI state events to hardware actions."""

        def on_chord_triggered(data):
            degree = data["degree"]
            notes = data["notes"]
            
            # Send MIDI
            self.hw.midi_output.send_chord_on(
                self.midi_channel, notes, self.velocity
            )
            # Store notes for this specific degree
            self._active_notes_by_degree[degree] = list(notes)

            # Update LEDs
            self.hw.led_matrix.set_button_led(degree, Color.CHORD_ACTIVE)
            self.hw.led_matrix.show_chord_visualization(
                notes, self.chord_engine.root_note
            )

            # Update display
            self.hw.display.show_chord(data["name"], data["numeral"])

        def on_chord_released(data):
            degree = data["degree"]
            
            # Send MIDI note offs for this specific degree's notes
            if degree in self._active_notes_by_degree:
                self.hw.midi_output.send_chord_off(
                    self.midi_channel, self._active_notes_by_degree[degree]
                )
                del self._active_notes_by_degree[degree]

            # Update LEDs
            self.hw.led_matrix.set_button_led(degree, Color.OFF)
            
            # Always clear the note visualization first
            self.hw.led_matrix.clear()
            
            # Then re-draw remaining active chord notes if any
            if self._active_notes_by_degree:
                remaining_notes = []
                for notes in self._active_notes_by_degree.values():
                    remaining_notes.extend(notes)
                self.hw.led_matrix.show_chord_visualization(
                    remaining_notes, self.chord_engine.root_note
                )

        def on_scale_changed(data):
            self._update_display()

        def on_mode_changed(data):
            self._update_display()
            # Show mode indicator on LEDs
            mode_colors = {
                Mode.PLAY: Color.MODE_PLAY,
                Mode.ROOT_SELECT: Color.MODE_ROOT_SELECT,
                Mode.SCALE_SELECT: Color.MODE_SCALE_SELECT,
            }
            mode_color = mode_colors.get(data["mode"], Color.MODE_PLAY)
            self.hw.led_matrix.set_button_led(Hardware.SPECIAL_BUTTON_INDEX, mode_color)

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
            self.hw.encoder.set_value(Hardware.ENCODER_START)

        # Check each button (0-6 for chords I-VII, 7 for special)
        for i in range(Hardware.TOTAL_BUTTONS):
            if i < Hardware.NUM_CHORD_BUTTONS:  # Chord buttons
                if self.hw.buttons.was_pressed(i):
                    self.ui_state.trigger_chord(i)

                if self.hw.buttons.was_released(i):
                    self.ui_state.release_chord(i)
            else:
                # Button 8 (index 7) for special functions
                if self.hw.buttons.was_long_pressed(i):
                    # Reset to default scale
                    self.chord_engine.scale_name = MidiConst.DEFAULT_SCALE
                    self.chord_engine.set_octave(MidiConst.DEFAULT_ROOT_NOTE // 12)
                    self.chord_engine.set_root_note_class(MidiConst.DEFAULT_ROOT_NOTE % 12)
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
        # Send note offs for any active notes (all degrees)
        for degree, notes in self._active_notes_by_degree.items():
            self.hw.midi_output.send_chord_off(self.midi_channel, notes)
        self._active_notes_by_degree = {}

        # Clear all LEDs
        self.hw.led_matrix.clear()
        self.hw.led_matrix.update()

        # Clear display
        self.hw.display.clear()
        self.hw.display.update()

    def set_velocity(self, velocity):
        """Set the default velocity for notes."""
        self.velocity = max(MidiConst.VELOCITY_MIN, min(MidiConst.VELOCITY_MAX, velocity))

    def set_midi_channel(self, channel):
        """Set the MIDI channel."""
        self.midi_channel = max(MidiConst.CHANNEL_MIN, min(MidiConst.CHANNEL_MAX, channel))
