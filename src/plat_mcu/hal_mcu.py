"""
MicroPython MCU Hardware Implementation.
For ESP32-S3 with MCP23017 I/O expander, SSD1306 OLED, NeoPixel matrix, and TRS MIDI.

This file contains all hardware-specific code. When changing hardware:
1. Update PinConfig class with new pin assignments
2. Modify HAL implementations if hardware interface differs
3. Update create_mcu_hardware_port() factory function
"""
from machine import Pin, I2C
from neopixel import NeoPixel
from lib.sh1106.sh1106 import SH1106_I2C
from lib.midi import Midi
from lib.mcp23017 import MCP23017, Rotary
from lib.mpr121 import MPR121
from utils import Button

from lib.chord_machine.hal_protocol import (
    ButtonsHAL,
    EncoderHAL,
    DisplayHAL,
    LedMatrixHAL,
    MidiOutputHAL,
    TouchStripHAL,
    TouchStripLedHAL,
    HardwarePort,
)
from lib.chord_machine.constants import (
    Mode,
    ModeIndicator,
    Color,
    Octave,
    Hardware,
    Midi as MidiConst,
)


# ============================================================================
# PIN CONFIGURATION - Change these when hardware changes
# ============================================================================
class PinConfig:
    """
    Centralized pin assignments for the MCU.
    Modify this class when changing hardware connections.
    """

    # ========================================================================
    # I2C BUS CONFIGURATION
    # ========================================================================
    
    # I2C Bus 0: All I2C devices share this bus
    # Pins: SCL=1, SDA=2
    I2C_BUS = 0
    I2C_SCL = 1
    I2C_SDA = 2

    # ========================================================================
    # I2C DEVICE: OLED Display (SH1106) - Bus 0
    # ========================================================================
    OLED_ADDRESS = 0x3C
    OLED_WIDTH = 128
    OLED_HEIGHT = 64

    # ========================================================================
    # I2C DEVICE: Touch Sensor (MPR121) - Bus 0
    # ========================================================================
    TOUCH_ADDRESS = 0x5A
    TOUCH_PAD_COUNT = 12

    # ========================================================================
    # I2C DEVICE: I/O Expander (MCP23017) - Bus 0
    # ========================================================================
    MCP_ADDRESS = 0x20
    MCP_INTERRUPT = 4

    # ========================================================================
    # OTHER PERIPHERALS
    # ========================================================================

    # NeoPixel LED Matrix (8x8 = 64 LEDs)
    NEOPIXEL_PIN = 14
    NEOPIXEL_COUNT = 64
    NEOPIXEL_BRIGHTNESS = 0.1

    # MIDI UART (TRS Type-A)
    MIDI_TX = 39
    MIDI_RX = 40
    MIDI_UART_ID = 1

    # Touch Strip LED (WS2812)
    TOUCH_STRIP_LED_PIN = 38
    TOUCH_STRIP_LED_COUNT = 25
    TOUCH_STRIP_LED_BRIGHTNESS = 0.1

    # MCP23017 pin assignments
    # Port A (pins 0-7): Encoder and outputs
    ENCODER_CLK = 7
    ENCODER_DT = 6
    ENCODER_SW = 5

    # Port B (pins 8-15): 8 Buttons with internal pullups
    BUTTON_PINS = [8, 9, 10, 11, 12, 13, 14, 15]


# ============================================================================
# HAL IMPLEMENTATIONS
# ============================================================================


class MCUButtonsHAL(ButtonsHAL):
    """Button implementation using MCP23017 GPIO expander."""

    def __init__(self, mcp, pin_numbers):
        """
        Args:
            mcp: MCP23017 instance
            pin_numbers: List of MCP23017 pin numbers for buttons
        """
        self.buttons = []
        for pin_num in pin_numbers:
            mcp.pin(pin_num, mode=1, pullup=True)  # Input with pullup
            self.buttons.append(Button(mcp[pin_num]))

    def update(self):
        for btn in self.buttons:
            btn.update()

    def was_pressed(self, index):
        if 0 <= index < len(self.buttons):
            return self.buttons[index].was_pressed()
        return False

    def was_released(self, index):
        if 0 <= index < len(self.buttons):
            return self.buttons[index].was_released()
        return False

    def was_long_pressed(self, index):
        if 0 <= index < len(self.buttons):
            return self.buttons[index].was_long_pressed()
        return False

    def is_pressed(self, index):
        if 0 <= index < len(self.buttons):
            return self.buttons[index].is_pressed()
        return False


class MCUEncoderHAL(EncoderHAL):
    """Rotary encoder implementation using MCP23017."""

    def __init__(self, mcp, interrupt_pin, clk, dt, sw):
        """
        Args:
            mcp: MCP23017 instance
            interrupt_pin: ESP32 pin for MCP interrupt
            clk: MCP23017 pin for encoder CLK
            dt: MCP23017 pin for encoder DT
            sw: MCP23017 pin for encoder switch
        """
        import time
        self._value = 0
        self._last_value = 0
        self._button_pressed = False
        self._last_button_time = 0
        self._last_sw_state = 0  # Track previous switch state
        self._debounce_ms = Hardware.ENCODER_DEBOUNCE_MS
        self._time = time
        self._invert_direction = True  # Invert rotation direction

        def callback(val, sw):
            self._value = val
            # Only trigger on rising edge (0 -> 1) of switch
            if sw == 1 and self._last_sw_state == 0:
                # Debounce the button
                now = self._time.ticks_ms()
                if self._time.ticks_diff(now, self._last_button_time) > self._debounce_ms:
                    self._button_pressed = True
                    self._last_button_time = now
            self._last_sw_state = sw

        # Set min_val and max_val to allow full range
        self.rotary = Rotary(mcp.porta, interrupt_pin, clk, dt, sw, callback,
                             start_val=Hardware.ENCODER_START, 
                             min_val=Hardware.ENCODER_MIN, 
                             max_val=Hardware.ENCODER_MAX)
        self.rotary.start()

    def get_delta(self):
        delta = self._value - self._last_value
        self._last_value = self._value
        # Invert direction if configured
        if self._invert_direction:
            delta = -delta
        return delta

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
        self.rotary.value = value

    def stop(self):
        """Stop the encoder interrupt handler."""
        self.rotary.stop()


class MCUDisplayHAL(DisplayHAL):
    """OLED display implementation using SH1106."""

    def __init__(self, i2c, width=128, height=64, addr=0x3C):
        """
        Args:
            i2c: I2C instance
            width: Display width in pixels
            height: Display height in pixels
            addr: I2C address (default 0x3C)
        """
        self.oled = SH1106_I2C(width, height, i2c, addr=addr)
        # Power cycle and flip for correct orientation
        self.oled.sleep(False)
        self.oled.flip(True)
        self.width = width
        self.height = height
        self._dirty = True
        self._current_mode = Mode.PLAY
        self._hold_active = False

    def clear(self):
        self.oled.fill(0)
        self._dirty = True

    def show_scale(self, scale_name, octave=None):
        # Clear the scale area completely (both lines)
        self.oled.fill_rect(0, 0, self.width, 20, 0)
        
        # Parse scale name to separate root note from scale type
        # e.g., "C Major" -> "C" and "Major"
        space_idx = scale_name.find(" ")
        if space_idx != -1:
            root_note = scale_name[:space_idx]
            scale_type = scale_name[space_idx + 1:]
        else:
            root_note = scale_name
            scale_type = ""
        
        # Add octave indicator with tick marks after the root note
        if octave is not None:
            if octave > Octave.REFERENCE:
                ticks = Octave.TICK_UP * (octave - Octave.REFERENCE)
            elif octave < Octave.REFERENCE:
                ticks = Octave.TICK_DOWN * (Octave.REFERENCE - octave)
            else:
                ticks = ""
            root_note = root_note + ticks
        
        # Line 1: "Scale: C'''''" (up to 16 chars total)
        line1 = "Scale: " + root_note
        if len(line1) > Hardware.DISPLAY_MAX_CHARS:
            line1 = line1[:Hardware.DISPLAY_MAX_CHARS]
        self.oled.text(line1, 0, 0, 1)
        
        # Line 2: Scale type (e.g., "Locrian") - leave room for mode indicator
        if len(scale_type) > 14:
            scale_type = scale_type[:14]
        self.oled.text(scale_type, 0, 10, 1)
        
        # Redraw mode indicator on line 2
        self._redraw_mode()
        self._dirty = True

    def show_chord(self, chord_name, numeral):
        # Show chord on bottom half - clear that area but leave room for hold indicator
        self.oled.fill_rect(0, 20, self.width - 12, 12, 0)
        chord_text = numeral + " (" + chord_name + ")"
        self.oled.text(chord_text, 0, 22, 1)
        self._dirty = True

    def show_message(self, message):
        self.oled.fill(0)
        # Center message vertically
        y = (self.height - 8) // 2
        if len(message) > 16:
            display_msg = message[:16]
        else:
            display_msg = message
        self.oled.text(display_msg, 0, y, 1)
        self._dirty = True

    def show_mode(self, mode):
        self._current_mode = mode
        self._redraw_mode()
        self._dirty = True
    
    def _redraw_mode(self):
        """Internal helper to redraw mode indicator."""
        # Show mode indicator in top right - clear that area first
        self.oled.fill_rect(self.width - 12, 0, 12, 10, 0)
        mode_char = ModeIndicator.get(self._current_mode)
        self.oled.text(mode_char, self.width - 10, 0, 1)

    def show_hold_indicator(self, is_holding):
        """Display chord hold mode indicator in bottom right."""
        self._hold_active = is_holding
        # Clear bottom right area
        self.oled.fill_rect(self.width - 12, self.height - 10, 12, 10, 0)
        if is_holding:
            self.oled.text("H", self.width - 10, self.height - 8, 1)
        self._dirty = True

    def update(self):
        if self._dirty:
            self.oled.show()
            self._dirty = False


class MCULedMatrixHAL(LedMatrixHAL):
    """NeoPixel 8x8 LED matrix implementation."""

    def __init__(self, pin, count=Hardware.MATRIX_LED_COUNT, brightness=0.1):
        """
        Args:
            pin: GPIO Pin for NeoPixel data
            count: Number of LEDs
            brightness: Brightness multiplier 0.0-1.0
        """
        self.np = NeoPixel(pin, count)
        self.count = count
        self.brightness = brightness
        self._dirty = False

    def _apply_brightness(self, color):
        """Apply brightness scaling to a color tuple."""
        return tuple(int(c * self.brightness) for c in color)

    def clear(self):
        self.np.fill(Color.OFF)
        self._dirty = True

    def set_button_led(self, index, color):
        """Set LED for button - maps to first row of matrix."""
        if 0 <= index < Hardware.MATRIX_WIDTH:
            self.np[index] = self._apply_brightness(color)
            self._dirty = True

    def set_pixel(self, x, y, color):
        """Set a specific pixel in the 8x8 matrix."""
        if 0 <= x < Hardware.MATRIX_WIDTH and 0 <= y < Hardware.MATRIX_HEIGHT:
            led_index = y * Hardware.MATRIX_WIDTH + x
            self.np[led_index] = self._apply_brightness(color)
            self._dirty = True

    def show_chord_visualization(self, notes, root_note):
        """
        Visualize chord notes on the matrix.
        Each row represents one octave, columns represent pitch classes.
        """
        # Don't clear - just add chord visualization
        for note in notes:
            # Map MIDI note to matrix position
            octave = (note // 12) % Hardware.MATRIX_HEIGHT  # Row (0-7)
            pitch_class = note % 12  # 0-11
            col = int(pitch_class * Hardware.MATRIX_WIDTH / 12)  # Scale 0-11 to 0-7

            led_index = octave * Hardware.MATRIX_WIDTH + col
            if 0 <= led_index < self.count:
                self.np[led_index] = self._apply_brightness(Color.CYAN)
        self._dirty = True

    def show_scale_indicator(self, scale_index, total_scales):
        """Show which scale is selected using row 7 (bottom)."""
        # Clear row 7
        row_start = (Hardware.MATRIX_HEIGHT - 1) * Hardware.MATRIX_WIDTH
        for x in range(Hardware.MATRIX_WIDTH):
            self.np[row_start + x] = Color.OFF

        # Light up LED corresponding to current scale
        if total_scales > 0:
            led_pos = int(scale_index * Hardware.MATRIX_WIDTH / total_scales)
            self.np[row_start + led_pos] = self._apply_brightness(Color.YELLOW)
        self._dirty = True

    def update(self):
        if self._dirty:
            self.np.write()
            self._dirty = False


class MCUMidiOutputHAL(MidiOutputHAL):
    """TRS MIDI output implementation using UART."""

    def __init__(self, uart_id, tx_pin, rx_pin):
        """
        Args:
            uart_id: UART peripheral ID
            tx_pin: GPIO Pin for MIDI TX
            rx_pin: GPIO Pin for MIDI RX
        """
        self.midi = Midi(uart_id, tx=tx_pin, rx=rx_pin)

    def send_note_on(self, channel, note, velocity):
        # Clamp note to valid MIDI range
        if note < MidiConst.NOTE_MIN or note > MidiConst.NOTE_MAX:
            return  # Skip invalid notes
        self.midi.send_note_on(channel, note, velocity=velocity)

    def send_note_off(self, channel, note, velocity=0):
        # Clamp note to valid MIDI range
        if note < MidiConst.NOTE_MIN or note > MidiConst.NOTE_MAX:
            return  # Skip invalid notes
        self.midi.send_note_off(channel, note)

    def send_control_change(self, channel, control, value):
        self.midi.send_control_change(channel, control, value)


class MCUTouchStripHAL(TouchStripHAL):
    """Capacitive touch strip implementation using MPR121."""

    def __init__(self, i2c, address=0x5A):
        """
        Args:
            i2c: I2C instance
            address: MPR121 I2C address (default 0x5A)
        """
        self.mpr = MPR121(i2c, address)
        self._last_touched = 0
        self._current_touched = 0
        self._just_touched = 0
        self._just_released = 0

    def update(self):
        """Poll touch sensor and update state."""
        self._last_touched = self._current_touched
        self._current_touched = self.mpr.touched()
        
        # Calculate edges
        self._just_touched = self._current_touched & ~self._last_touched
        self._just_released = self._last_touched & ~self._current_touched

    def get_touched(self):
        """Get bitmask of currently touched pads."""
        return self._current_touched

    def was_touched(self, pad):
        """Check if pad was just touched."""
        if 0 <= pad < 12:
            return bool(self._just_touched & (1 << pad))
        return False

    def was_released(self, pad):
        """Check if pad was just released."""
        if 0 <= pad < 12:
            return bool(self._just_released & (1 << pad))
        return False

    def is_touched(self, pad):
        """Check if pad is currently touched."""
        if 0 <= pad < 12:
            return bool(self._current_touched & (1 << pad))
        return False


class MCUTouchStripLedHAL(TouchStripLedHAL):
    """WS2812 LED strip above touch strip (24 LEDs, 2 per pad + 1 ignored)."""

    def __init__(self, pin, count=24, brightness=0.1):
        """
        Args:
            pin: GPIO Pin for NeoPixel data
            count: Number of LEDs (default 24)
            brightness: Brightness multiplier 0.0-1.0
        """
        self.np = NeoPixel(pin, count)
        self.count = count
        self.brightness = brightness
        self.num_pads = 12
        self._dirty = False

    def _apply_brightness(self, color):
        """Apply brightness scaling to a color tuple."""
        return tuple(int(c * self.brightness) for c in color)

    def clear(self):
        """Turn off all LEDs."""
        self.np.fill(Color.OFF)
        self._dirty = True

    def update_scale_and_chord(
        self, scale_semitones, chord_semitones, scale_color=(0, 0, 255), chord_color=(0, 255, 0)
    ):
        """
        Update LEDs to show scale notes and chord notes.

        Each touch pad (0-11) represents a chromatic semitone.
        - First LED (pad * 2): blue if semitone is in scale
        - Second LED (pad * 2 + 1): green if semitone is in active chord
        - LED 24 stays off (ignored)
        """
        for pad in range(self.num_pads):
            semitone = pad
            first_led_index = pad * 2
            second_led_index = pad * 2 + 1

            # First LED: scale indicator
            if semitone in scale_semitones:
                self.np[first_led_index] = self._apply_brightness(scale_color)
            else:
                self.np[first_led_index] = Color.OFF

            # Second LED: chord indicator
            if semitone in chord_semitones:
                self.np[second_led_index] = self._apply_brightness(chord_color)
            else:
                self.np[second_led_index] = Color.OFF

        # LED 24 stays off
        self.np[24] = Color.OFF
        self._dirty = True

    def update(self):
        """Push changes to LED hardware."""
        if self._dirty:
            self.np.write()
            self._dirty = False


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def create_mcu_hardware_port():
    """
    Factory function to create fully configured MCU hardware.

    Returns:
        HardwarePort instance with all HAL implementations configured
    """
    # Initialize I2C Bus 0: All I2C devices (OLED, Touch Sensor, MCP23017)
    i2c = I2C(
        PinConfig.I2C_BUS,
        scl=Pin(PinConfig.I2C_SCL),
        sda=Pin(PinConfig.I2C_SDA),
    )

    # Initialize MCP23017
    mcp = MCP23017(i2c, address=PinConfig.MCP_ADDRESS)

    # Configure MCP port A pins for encoder (outputs and inputs)
    for pin_num in range(8):
        if pin_num in [PinConfig.ENCODER_CLK, PinConfig.ENCODER_DT, PinConfig.ENCODER_SW]:
            mcp.pin(pin_num, mode=1, pullup=True)  # Input with pullup
        else:
            mcp.pin(pin_num, mode=0, value=0)  # Output

    # Interrupt pin for encoder
    interrupt_pin = Pin(PinConfig.MCP_INTERRUPT, mode=Pin.IN)

    # Create HAL instances
    buttons = MCUButtonsHAL(mcp, PinConfig.BUTTON_PINS)

    encoder = MCUEncoderHAL(
        mcp,
        interrupt_pin,
        PinConfig.ENCODER_CLK,
        PinConfig.ENCODER_DT,
        PinConfig.ENCODER_SW,
    )

    display = MCUDisplayHAL(
        i2c,
        PinConfig.OLED_WIDTH,
        PinConfig.OLED_HEIGHT,
        PinConfig.OLED_ADDRESS,
    )

    led_matrix = MCULedMatrixHAL(
        Pin(PinConfig.NEOPIXEL_PIN, Pin.OUT),
        PinConfig.NEOPIXEL_COUNT,
        PinConfig.NEOPIXEL_BRIGHTNESS,
    )

    midi_output = MCUMidiOutputHAL(
        PinConfig.MIDI_UART_ID,
        Pin(PinConfig.MIDI_TX),
        Pin(PinConfig.MIDI_RX),
    )

    # Touch strip uses same I2C bus
    touch_strip = MCUTouchStripHAL(
        i2c,
        PinConfig.TOUCH_ADDRESS,
    )

    # Touch strip LED (WS2812)
    touch_strip_led = MCUTouchStripLedHAL(
        Pin(PinConfig.TOUCH_STRIP_LED_PIN, Pin.OUT),
        PinConfig.TOUCH_STRIP_LED_COUNT,
        PinConfig.TOUCH_STRIP_LED_BRIGHTNESS,
    )

    return HardwarePort(buttons, encoder, display, led_matrix, midi_output, touch_strip, touch_strip_led)
