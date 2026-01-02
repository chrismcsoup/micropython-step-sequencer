"""
Mock HAL implementations for testing the Chord Machine.
These mocks record all hardware interactions for verification in tests.
"""
from lib.chord_machine.hal_protocol import (
    ButtonsHAL,
    EncoderHAL,
    DisplayHAL,
    LedMatrixHAL,
    MidiOutputHAL,
    HardwarePort,
)


class MockButtonsHAL(ButtonsHAL):
    """Mock buttons that can be programmatically triggered."""

    def __init__(self, count=8):
        self.count = count
        self._pressed = [False] * count
        self._released = [False] * count
        self._long_pressed = [False] * count
        self._current = [False] * count

    def simulate_press(self, index):
        """Simulate a button press."""
        if 0 <= index < self.count:
            self._pressed[index] = True
            self._current[index] = True

    def simulate_release(self, index):
        """Simulate a button release."""
        if 0 <= index < self.count:
            self._released[index] = True
            self._current[index] = False

    def simulate_long_press(self, index):
        """Simulate a long press."""
        if 0 <= index < self.count:
            self._long_pressed[index] = True

    def update(self):
        pass

    def was_pressed(self, index):
        if 0 <= index < self.count and self._pressed[index]:
            self._pressed[index] = False
            return True
        return False

    def was_released(self, index):
        if 0 <= index < self.count and self._released[index]:
            self._released[index] = False
            return True
        return False

    def was_long_pressed(self, index):
        if 0 <= index < self.count and self._long_pressed[index]:
            self._long_pressed[index] = False
            return True
        return False

    def is_pressed(self, index):
        if 0 <= index < self.count:
            return self._current[index]
        return False


class MockEncoderHAL(EncoderHAL):
    """Mock encoder that can be programmatically controlled."""

    def __init__(self):
        self._value = 0
        self._last_value = 0
        self._button_pressed = False
        self._delta_queue = []

    def simulate_rotate(self, delta):
        """Simulate encoder rotation."""
        self._delta_queue.append(delta)
        self._value += delta

    def simulate_button_press(self):
        """Simulate encoder button press."""
        self._button_pressed = True

    def get_delta(self):
        if self._delta_queue:
            return self._delta_queue.pop(0)
        return 0

    def was_button_pressed(self):
        if self._button_pressed:
            self._button_pressed = False
            return True
        return False

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value
        self._last_value = value


class MockDisplayHAL(DisplayHAL):
    """Mock display that records all display operations."""

    def __init__(self):
        self.calls = []
        self.current_scale = ""
        self.current_chord = ""
        self.current_numeral = ""
        self.current_message = ""
        self.current_mode = ""

    def clear(self):
        self.calls.append(("clear",))
        self.current_scale = ""
        self.current_chord = ""
        self.current_numeral = ""

    def show_scale(self, scale_name):
        self.calls.append(("show_scale", scale_name))
        self.current_scale = scale_name

    def show_chord(self, chord_name, numeral):
        self.calls.append(("show_chord", chord_name, numeral))
        self.current_chord = chord_name
        self.current_numeral = numeral

    def show_message(self, message):
        self.calls.append(("show_message", message))
        self.current_message = message

    def show_mode(self, mode):
        self.calls.append(("show_mode", mode))
        self.current_mode = mode

    def update(self):
        self.calls.append(("update",))


class MockLedMatrixHAL(LedMatrixHAL):
    """Mock LED matrix that records all LED operations."""

    def __init__(self, count=64):
        self.count = count
        self.calls = []
        self.leds = [(0, 0, 0)] * count
        self.button_leds = [(0, 0, 0)] * 8

    def clear(self):
        self.calls.append(("clear",))
        self.leds = [(0, 0, 0)] * self.count
        self.button_leds = [(0, 0, 0)] * 8

    def set_button_led(self, index, color):
        self.calls.append(("set_button_led", index, color))
        if 0 <= index < 8:
            self.button_leds[index] = color

    def set_pixel(self, x, y, color):
        self.calls.append(("set_pixel", x, y, color))
        if 0 <= x < 8 and 0 <= y < 8:
            self.leds[y * 8 + x] = color

    def show_chord_visualization(self, notes, root_note):
        self.calls.append(("show_chord_visualization", notes, root_note))

    def show_scale_indicator(self, scale_index, total_scales):
        self.calls.append(("show_scale_indicator", scale_index, total_scales))

    def update(self):
        self.calls.append(("update",))


class MockMidiOutputHAL(MidiOutputHAL):
    """Mock MIDI output that records all MIDI messages."""

    def __init__(self):
        self.messages = []

    def send_note_on(self, channel, note, velocity):
        self.messages.append(("note_on", channel, note, velocity))

    def send_note_off(self, channel, note, velocity=0):
        self.messages.append(("note_off", channel, note, velocity))

    def send_control_change(self, channel, control, value):
        self.messages.append(("cc", channel, control, value))

    def get_last_notes_on(self):
        """Get the most recent note_on messages (for the last chord)."""
        result = []
        for msg in reversed(self.messages):
            if msg[0] == "note_on":
                result.append(msg)
            elif msg[0] == "note_off":
                break
        return list(reversed(result))

    def clear_messages(self):
        """Clear recorded messages."""
        self.messages = []


def create_mock_hardware_port():
    """
    Factory function to create a mock hardware port for testing.
    
    Returns:
        Tuple of (HardwarePort, dict of individual mocks)
    """
    buttons = MockButtonsHAL()
    encoder = MockEncoderHAL()
    display = MockDisplayHAL()
    led_matrix = MockLedMatrixHAL()
    midi_output = MockMidiOutputHAL()

    port = HardwarePort(buttons, encoder, display, led_matrix, midi_output)

    mocks = {
        "buttons": buttons,
        "encoder": encoder,
        "display": display,
        "led_matrix": led_matrix,
        "midi_output": midi_output,
    }

    return port, mocks
