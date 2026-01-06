"""
Hardware Abstraction Layer Protocol Definitions.
These are abstract base classes that each platform must implement.

This allows the same application code to run on:
- MicroPython on ESP32/RP2040
- PyScript in a web browser
- Desktop Python for testing
"""


class ButtonsHAL:
    """Abstract interface for button input (8 chord buttons)."""

    def update(self):
        """Poll button states. Call in main loop."""
        raise NotImplementedError

    def was_pressed(self, index):
        """
        Check if button was just pressed.

        Args:
            index: Button index 0-7

        Returns:
            True if button was pressed since last check
        """
        raise NotImplementedError

    def was_released(self, index):
        """
        Check if button was just released.

        Args:
            index: Button index 0-7

        Returns:
            True if button was released since last check
        """
        raise NotImplementedError

    def was_long_pressed(self, index):
        """
        Check if button was long-pressed.

        Args:
            index: Button index 0-7

        Returns:
            True if button long-press threshold was reached
        """
        raise NotImplementedError

    def is_pressed(self, index):
        """
        Check if button is currently pressed.

        Args:
            index: Button index 0-7

        Returns:
            True if button is currently held down
        """
        raise NotImplementedError


class EncoderHAL:
    """Abstract interface for rotary encoder."""

    def get_delta(self):
        """
        Get rotation delta since last call.

        Returns:
            Integer: Positive = clockwise, Negative = counter-clockwise
        """
        raise NotImplementedError

    def was_button_pressed(self):
        """
        Check if encoder button was pressed.

        Returns:
            True if encoder button was pressed since last check
        """
        raise NotImplementedError

    def get_value(self):
        """
        Get absolute encoder value.

        Returns:
            Current encoder position
        """
        raise NotImplementedError

    def set_value(self, value):
        """
        Set encoder value (e.g., for resetting).

        Args:
            value: New encoder position
        """
        raise NotImplementedError


class DisplayHAL:
    """Abstract interface for OLED display."""

    def clear(self):
        """Clear the display."""
        raise NotImplementedError

    def show_scale(self, scale_name, octave=None):
        """
        Display the current scale name.

        Args:
            scale_name: Scale name string (e.g., "C Major")
            octave: Optional octave number to display with tick marks
        """
        raise NotImplementedError

    def show_chord(self, chord_name, numeral):
        """
        Display the currently playing chord.

        Args:
            chord_name: Chord name (e.g., "Dm")
            numeral: Roman numeral (e.g., "ii")
        """
        raise NotImplementedError

    def show_message(self, message):
        """
        Display a status message.

        Args:
            message: Message string
        """
        raise NotImplementedError

    def show_mode(self, mode):
        """
        Display current mode indicator.

        Args:
            mode: Mode name ("play", "settings", etc.)
        """
        raise NotImplementedError

    def update(self):
        """Push changes to display hardware."""
        raise NotImplementedError


class LedMatrixHAL:
    """Abstract interface for LED matrix/strip (8x8 NeoPixel)."""

    def clear(self):
        """Turn off all LEDs."""
        raise NotImplementedError

    def set_button_led(self, index, color):
        """
        Set LED for a button (index 0-7).

        Args:
            index: Button index 0-7
            color: Tuple (R, G, B) with values 0-255
        """
        raise NotImplementedError

    def set_pixel(self, x, y, color):
        """
        Set a specific pixel in the matrix.

        Args:
            x: X coordinate 0-7
            y: Y coordinate 0-7
            color: Tuple (R, G, B) with values 0-255
        """
        raise NotImplementedError

    def show_chord_visualization(self, notes, root_note):
        """
        Visualize chord notes on the matrix.

        Args:
            notes: List of MIDI note numbers
            root_note: Root note for reference
        """
        raise NotImplementedError

    def show_scale_indicator(self, scale_index, total_scales):
        """
        Show which scale is selected.

        Args:
            scale_index: Current scale index
            total_scales: Total number of scales
        """
        raise NotImplementedError

    def update(self):
        """Push changes to LED hardware."""
        raise NotImplementedError


class TouchStripHAL:
    """Abstract interface for capacitive touch strip (MPR121 with 12 pads)."""

    def update(self):
        """Poll touch states. Call in main loop."""
        raise NotImplementedError

    def get_touched(self):
        """
        Get bitmask of currently touched pads.

        Returns:
            Integer bitmask where bit N is set if pad N is touched
        """
        raise NotImplementedError

    def was_touched(self, pad):
        """
        Check if pad was just touched (newly pressed).

        Args:
            pad: Pad index 0-11

        Returns:
            True if pad was touched since last update
        """
        raise NotImplementedError

    def was_released(self, pad):
        """
        Check if pad was just released.

        Args:
            pad: Pad index 0-11

        Returns:
            True if pad was released since last update
        """
        raise NotImplementedError

    def is_touched(self, pad):
        """
        Check if pad is currently touched.

        Args:
            pad: Pad index 0-11

        Returns:
            True if pad is currently touched
        """
        raise NotImplementedError


class MidiOutputHAL:
    """Abstract interface for MIDI output."""

    def send_note_on(self, channel, note, velocity):
        """
        Send MIDI Note On message.

        Args:
            channel: MIDI channel 0-15
            note: MIDI note number 0-127
            velocity: Note velocity 0-127
        """
        raise NotImplementedError

    def send_note_off(self, channel, note, velocity=0):
        """
        Send MIDI Note Off message.

        Args:
            channel: MIDI channel 0-15
            note: MIDI note number 0-127
            velocity: Release velocity 0-127
        """
        raise NotImplementedError

    def send_control_change(self, channel, control, value):
        """
        Send MIDI Control Change message.

        Args:
            channel: MIDI channel 0-15
            control: CC number 0-127
            value: CC value 0-127
        """
        raise NotImplementedError

    def send_chord_on(self, channel, notes, velocity):
        """
        Convenience: send Note On for multiple notes.

        Args:
            channel: MIDI channel 0-15
            notes: List of MIDI note numbers
            velocity: Note velocity 0-127
        """
        for note in notes:
            self.send_note_on(channel, note, velocity)

    def send_chord_off(self, channel, notes, velocity=0):
        """
        Convenience: send Note Off for multiple notes.

        Args:
            channel: MIDI channel 0-15
            notes: List of MIDI note numbers
            velocity: Release velocity 0-127
        """
        for note in notes:
            self.send_note_off(channel, note, velocity)


class HardwarePort:
    """
    Complete hardware port interface.
    A platform provides an instance of this with all HAL implementations.
    """

    def __init__(
        self,
        buttons,
        encoder,
        display,
        led_matrix,
        midi_output,
        touch_strip=None,
    ):
        """
        Args:
            buttons: ButtonsHAL implementation
            encoder: EncoderHAL implementation
            display: DisplayHAL implementation
            led_matrix: LedMatrixHAL implementation
            midi_output: MidiOutputHAL implementation
            touch_strip: Optional TouchStripHAL implementation
        """
        self.buttons = buttons
        self.encoder = encoder
        self.display = display
        self.led_matrix = led_matrix
        self.midi_output = midi_output
        self.touch_strip = touch_strip

    def update_inputs(self):
        """Poll all input devices."""
        self.buttons.update()
        if self.touch_strip:
            self.touch_strip.update()

    def update_outputs(self):
        """Push all output changes."""
        self.display.update()
        self.led_matrix.update()
