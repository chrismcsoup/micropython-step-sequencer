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
from lib.mcp23017 import MCP23017
from lib.mpr121 import MPR121
from lib.rotary.rotary_irq_esp import RotaryIRQ
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
    # Pins: SCL=39, SDA=40
    I2C_BUS = 0
    I2C_SCL = 39
    I2C_SDA = 40

    # ========================================================================
    # I2C DEVICE: OLED Display (SH1106) - Bus 0
    # ========================================================================
    OLED_ADDRESS = 0x3C
    OLED_WIDTH = 128
    OLED_HEIGHT = 64

    # ========================================================================
    # I2C DEVICE: Touch Sensor (MPR121) - Bus 0
    # ========================================================================
    TOUCH_ENABLED = True
    TOUCH_ADDRESS = 0x5A
    TOUCH_PAD_COUNT = 12
    # Set to True if pads are wired in reverse order (B on left, C on right)
    TOUCH_REVERSED = True

    # ========================================================================
    # I2C DEVICE: I/O Expander (MCP23017) - Bus 0
    # ========================================================================
    MCP_ADDRESS = 0x20

    # ========================================================================
    # OTHER PERIPHERALS
    # ========================================================================

    # NeoPixel LED Matrix (8x8 = 64 LEDs) - NOT USED IN CURRENT HARDWARE
    NEOPIXEL_PIN = 14
    NEOPIXEL_COUNT = 64
    NEOPIXEL_BRIGHTNESS = 0.1

    # MIDI UART (TRS Type-A) - 3 outputs
    # UART1 and UART2 for hardware MIDI, software UART for 3rd output
    MIDI_TX_1 = 36  # TRS 1 (hardware UART1)
    MIDI_TX_2 = 37  # TRS 2 (hardware UART2)
    MIDI_TX_3 = 38  # TRS 3 (software UART / bit-banged)
    MIDI_RX = 1  # MIDI IN
    # Dummy RX pin for MIDI 2 (not physically connected, but required by library)
    MIDI_RX_DUMMY_2 = 2   # Unused pin
    # UART IDs (UART0 is reserved, use 1 and 2)
    MIDI_UART_ID_1 = 1
    MIDI_UART_ID_2 = 2

    # Touch Strip LED (WS2812) - 24 LEDs for touch strip visualization
    TOUCH_STRIP_LED_PIN = 3
    TOUCH_STRIP_LED_COUNT = 24
    TOUCH_STRIP_LED_BRIGHTNESS = 0.1

    # Button LED Strip (WS2812) - 16 LEDs for button indicators
    BUTTON_LED_PIN = 4
    BUTTON_LED_COUNT = 16
    BUTTON_LED_BRIGHTNESS = 0.1

    # Left Rotary Encoder (direct ESP32 GPIO)
    LEFT_ENCODER_CLK = 6
    LEFT_ENCODER_DT = 7
    LEFT_ENCODER_SW = 5

    # Right Rotary Encoder (direct ESP32 GPIO)
    RIGHT_ENCODER_CLK = 34
    RIGHT_ENCODER_DT = 33
    RIGHT_ENCODER_SW = 35

    # MCP23017 pin assignments
    # All 16 pins (0-15): 16 Buttons with internal pullups
    # Logically split into two groups of 8
    BUTTON_PINS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]


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
    """Rotary encoder implementation using direct ESP32 GPIO with RotaryIRQ."""

    def __init__(self, clk_pin, dt_pin, sw_pin):
        """
        Args:
            clk_pin: ESP32 GPIO pin number for encoder CLK
            dt_pin: ESP32 GPIO pin number for encoder DT
            sw_pin: ESP32 GPIO pin number for encoder switch
        """
        import time
        self._last_value = 0
        self._button_pressed = False
        self._last_button_time = 0
        self._last_sw_state = 1  # Pull-up means default high
        self._debounce_ms = Hardware.ENCODER_DEBOUNCE_MS
        self._time = time
        self._invert_direction = True  # Invert rotation direction

        # Initialize RotaryIRQ with direct GPIO pins
        self.rotary = RotaryIRQ(
            pin_num_clk=clk_pin,
            pin_num_dt=dt_pin,
            min_val=Hardware.ENCODER_MIN,
            max_val=Hardware.ENCODER_MAX,
            pull_up=True,
            reverse=self._invert_direction,
            range_mode=RotaryIRQ.RANGE_BOUNDED,
        )
        self.rotary.set(value=Hardware.ENCODER_START)
        self._last_value = self.rotary.value()

        # Button pin with pull-up
        self._button = Pin(sw_pin, Pin.IN, Pin.PULL_UP)

    def get_delta(self):
        current_value = self.rotary.value()
        delta = current_value - self._last_value
        self._last_value = current_value
        return delta

    def was_button_pressed(self):
        # Poll button and detect falling edge (pressed = low with pull-up)
        current_sw = self._button.value()
        if current_sw == 0 and self._last_sw_state == 1:
            # Debounce
            now = self._time.ticks_ms()
            if self._time.ticks_diff(now, self._last_button_time) > self._debounce_ms:
                self._last_button_time = now
                self._last_sw_state = current_sw
                return True
        self._last_sw_state = current_sw
        return False

    def get_value(self):
        return self.rotary.value()

    def set_value(self, value):
        self.rotary.set(value=value)
        self._last_value = value

    def stop(self):
        """Stop the encoder interrupt handler."""
        self.rotary.close()


class MCUDualEncoderHAL(EncoderHAL):
    """Dual encoder implementation - combines two encoders to act as one."""

    def __init__(self, left_clk, left_dt, left_sw, right_clk, right_dt, right_sw):
        """
        Args:
            left_clk: Left encoder CLK pin
            left_dt: Left encoder DT pin
            left_sw: Left encoder SW pin
            right_clk: Right encoder CLK pin
            right_dt: Right encoder DT pin
            right_sw: Right encoder SW pin
        """
        self.left_encoder = MCUEncoderHAL(left_clk, left_dt, left_sw)
        self.right_encoder = MCUEncoderHAL(right_clk, right_dt, right_sw)

    def get_delta(self):
        """Get combined rotation delta from both encoders."""
        left_delta = self.left_encoder.get_delta()
        right_delta = self.right_encoder.get_delta()
        return left_delta + right_delta

    def was_button_pressed(self):
        """Check if either encoder button was pressed."""
        return self.left_encoder.was_button_pressed() or self.right_encoder.was_button_pressed()

    def get_value(self):
        """Get value from left encoder (primary)."""
        return self.left_encoder.get_value()

    def set_value(self, value):
        """Set value on both encoders."""
        self.left_encoder.set_value(value)
        self.right_encoder.set_value(value)

    def stop(self):
        """Stop both encoders."""
        self.left_encoder.stop()
        self.right_encoder.stop()


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


class SoftwareMidiTx:
    """RMT-based MIDI TX for when hardware UARTs are exhausted.
    
    Uses ESP32 RMT (Remote Control) peripheral to generate UART-like
    signals in hardware without CPU involvement.
    MIDI uses 31250 baud, 8N1 format (8 data bits, no parity, 1 stop bit).
    Bit time = 1/31250 = 32 microseconds
    """
    
    def __init__(self, tx_pin):
        """
        Args:
            tx_pin: GPIO Pin object for TX output
        """
        from esp32 import RMT
        
        # RMT resolution: 1 tick = 1 microsecond (1MHz)
        # MIDI bit time = 32us at 31250 baud
        self._bit_ticks = 32
        
        # Initialize RMT channel
        # idle_level=1 because UART idle state is high
        self._rmt = RMT(0, pin=tx_pin, clock_div=80, idle_level=1)
        # clock_div=80 gives 1MHz (80MHz / 80 = 1MHz), so 1 tick = 1us
    
    def _byte_to_pulses(self, byte):
        """Convert a byte to duration/level pairs for UART 8N1 format.
        
        Returns (durations, levels) lists for RMT Mode 3.
        UART frame: start bit (low) + 8 data bits (LSB first) + stop bit (high)
        """
        durations = []
        levels = []
        
        # Start bit (low for 32us)
        durations.append(self._bit_ticks)
        levels.append(False)  # Low
        
        # 8 Data bits (LSB first)
        for i in range(8):
            bit_level = (byte >> i) & 1
            durations.append(self._bit_ticks)
            levels.append(bool(bit_level))
        
        # Stop bit (high for 32us)
        durations.append(self._bit_ticks)
        levels.append(True)  # High
        
        return durations, levels
    
    def write(self, data):
        """Write bytes to MIDI output using RMT (non-blocking after setup)."""
        if not data:
            return
            
        # Wait for any previous transmission to complete first
        self._rmt.wait_done()
        
        # Build complete pulse sequence for all bytes
        all_durations = []
        all_levels = []
        for byte in data:
            durations, levels = self._byte_to_pulses(byte)
            all_durations.extend(durations)
            all_levels.extend(levels)
        
        # Use Mode 3: write_pulses(durations, levels) - equal length lists
        # This lets us specify exact duration and level for each pulse
        self._rmt.write_pulses(all_durations, all_levels)
    
    def send_note_on(self, channel, note, velocity=127):
        """Send MIDI Note On message."""
        status = 0x90 | (channel & 0x0F)
        self.write(bytes([status, note & 0x7F, velocity & 0x7F]))
    
    def send_note_off(self, channel, note, velocity=0):
        """Send MIDI Note Off message."""
        status = 0x80 | (channel & 0x0F)
        self.write(bytes([status, note & 0x7F, velocity & 0x7F]))
    
    def send_control_change(self, channel, control, value):
        """Send MIDI Control Change message."""
        status = 0xB0 | (channel & 0x0F)
        self.write(bytes([status, control & 0x7F, value & 0x7F]))


class MCUTripleMidiOutputHAL(MidiOutputHAL):
    """Triple TRS MIDI output - 2 hardware UARTs + 1 software UART."""

    def __init__(self, uart_id_1, tx_pin_1, rx_pin_1, uart_id_2, tx_pin_2, rx_pin_2, tx_pin_3):
        """
        Args:
            uart_id_1: UART peripheral ID for MIDI 1
            tx_pin_1: GPIO Pin for MIDI TX 1
            rx_pin_1: GPIO Pin for MIDI RX 1
            uart_id_2: UART peripheral ID for MIDI 2
            tx_pin_2: GPIO Pin for MIDI TX 2
            rx_pin_2: GPIO Pin for MIDI RX 2 (dummy)
            tx_pin_3: GPIO Pin for MIDI TX 3 (software UART)
        """
        print("Starting MIDI 1 (hardware UART)...")
        self.midi1 = Midi(uart_id_1, tx=tx_pin_1, rx=rx_pin_1)
        print("Starting MIDI 2 (hardware UART)...")
        self.midi2 = Midi(uart_id_2, tx=tx_pin_2, rx=rx_pin_2)
        print("Starting MIDI 3 (software UART)...")
        self.midi3 = SoftwareMidiTx(tx_pin_3)

    def send_note_on(self, channel, note, velocity):
        # Clamp note to valid MIDI range
        if note < MidiConst.NOTE_MIN or note > MidiConst.NOTE_MAX:
            return  # Skip invalid notes
        self.midi1.send_note_on(channel, note, velocity=velocity)
        self.midi2.send_note_on(channel, note, velocity=velocity)
        self.midi3.send_note_on(channel, note, velocity=velocity)

    def send_note_off(self, channel, note, velocity=0):
        # Clamp note to valid MIDI range
        if note < MidiConst.NOTE_MIN or note > MidiConst.NOTE_MAX:
            return  # Skip invalid notes
        self.midi1.send_note_off(channel, note)
        self.midi2.send_note_off(channel, note)
        self.midi3.send_note_off(channel, note)

    def send_control_change(self, channel, control, value):
        self.midi1.send_control_change(channel, control, value)
        self.midi2.send_control_change(channel, control, value)
        self.midi3.send_control_change(channel, control, value)
        self.midi2.send_control_change(channel, control, value)


class MCUDummyTouchStripHAL(TouchStripHAL):
    """Dummy touch strip implementation - touch sensor not connected."""

    def __init__(self):
        """Initialize dummy touch strip."""
        pass

    def update(self):
        """Do nothing - no sensor connected."""
        pass

    def get_touched(self):
        """Return 0 - nothing touched."""
        return 0

    def was_touched(self, pad):
        """Return False - nothing touched."""
        return False

    def was_released(self, pad):
        """Return False - nothing released."""
        return False

    def is_touched(self, pad):
        """Return False - nothing touched."""
        return False


class MCUTouchStripHAL(TouchStripHAL):
    """Capacitive touch strip implementation using MPR121."""

    def __init__(self, i2c, address=0x5A, reversed=False):
        """
        Args:
            i2c: I2C instance
            address: MPR121 I2C address (default 0x5A)
            reversed: If True, reverse pad order (pad 0 becomes pad 11, etc.)
        """
        self.mpr = MPR121(i2c, address)
        self._reversed = reversed
        self._last_touched = 0
        self._current_touched = 0
        self._just_touched = 0
        self._just_released = 0

    def _reverse_bits(self, value):
        """Reverse the lower 12 bits of a bitmask."""
        result = 0
        for i in range(12):
            if value & (1 << i):
                result |= (1 << (11 - i))
        return result

    def update(self):
        """Poll touch sensor and update state."""
        self._last_touched = self._current_touched
        raw_touched = self.mpr.touched()
        
        # Apply reversal if configured
        if self._reversed:
            self._current_touched = self._reverse_bits(raw_touched)
        else:
            self._current_touched = raw_touched
        
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


class MCUButtonLedStripHAL:
    """WS2812 LED strip for button indicators (16 LEDs)."""

    def __init__(self, pin, count=16, brightness=0.1):
        """
        Args:
            pin: GPIO Pin for NeoPixel data
            count: Number of LEDs (default 16)
            brightness: Brightness multiplier 0.0-1.0
        """
        self.np = NeoPixel(pin, count)
        self.count = count
        self.brightness = brightness
        self._dirty = False
        self._button_states = [False] * count

    def _apply_brightness(self, color):
        """Apply brightness scaling to a color tuple."""
        return tuple(int(c * self.brightness) for c in color)

    def clear(self):
        """Turn off all LEDs."""
        self.np.fill(Color.OFF)
        self._dirty = True

    def set_button_state(self, button_index, is_pressed):
        """Update button LED based on button state."""
        if 0 <= button_index < self.count:
            self._button_states[button_index] = is_pressed
            if is_pressed:
                # White at 10% brightness
                self.np[button_index] = self._apply_brightness((255, 255, 255))
            else:
                self.np[button_index] = Color.OFF
            self._dirty = True

    def update(self):
        """Push changes to LED hardware."""
        if self._dirty:
            self.np.write()
            self._dirty = False


class MCUTouchStripLedHAL(TouchStripLedHAL):
    """WS2812 LED strip above touch strip (24 LEDs, 2 per pad)."""

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
        self.brightness_highlight = 0.15  # Brighter when touched
        self.brightness_non_scale = 0.10  # White for non-scale touched keys
        self.num_pads = 12
        self._dirty = False
        # Store current state for touch highlight updates
        self._scale_semitones = set()
        self._chord_semitones = set()
        self._scale_color = (0, 0, 255)
        self._chord_color = (0, 255, 0)
        self._touched_pads = 0  # Bitmask of touched pads

    def _apply_brightness(self, color, brightness=None):
        """Apply brightness scaling to a color tuple."""
        if brightness is None:
            brightness = self.brightness
        return tuple(int(c * brightness) for c in color)

    def clear(self):
        """Turn off all LEDs."""
        self.np.fill(Color.OFF)
        self._dirty = True

    def set_touched_pads(self, touched_bitmask):
        """
        Set which pads are currently touched and update LEDs.
        
        Args:
            touched_bitmask: Bitmask of touched pads (bit N = pad N)
        """
        if self._touched_pads != touched_bitmask:
            self._touched_pads = touched_bitmask
            self._redraw_leds()

    def update_scale_and_chord(
        self, scale_semitones, chord_semitones, scale_color=(0, 0, 255), chord_color=(0, 255, 0)
    ):
        """
        Update LEDs to show scale notes and chord notes.

        Each touch pad (0-11) represents a chromatic semitone.
        - First LED (pad * 2): blue if semitone is in scale (brighter if touched)
        - Second LED (pad * 2 + 1): green if semitone is in active chord
        """
        self._scale_semitones = scale_semitones
        self._chord_semitones = chord_semitones
        self._scale_color = scale_color
        self._chord_color = chord_color
        self._redraw_leds()

    def _redraw_leds(self):
        """Internal: redraw all LEDs based on current state."""
        for pad in range(self.num_pads):
            semitone = pad
            first_led_index = pad * 2
            second_led_index = pad * 2 + 1
            is_touched = bool(self._touched_pads & (1 << pad))
            is_in_scale = semitone in self._scale_semitones

            # First LED: scale indicator (with touch highlight)
            if is_touched:
                if is_in_scale:
                    # Scale note touched: brighter scale color (15%)
                    self.np[first_led_index] = self._apply_brightness(
                        self._scale_color, self.brightness_highlight
                    )
                else:
                    # Non-scale note touched: white at 10%
                    self.np[first_led_index] = self._apply_brightness(
                        Color.WHITE, self.brightness_non_scale
                    )
            elif is_in_scale:
                # Scale note not touched: normal brightness
                self.np[first_led_index] = self._apply_brightness(self._scale_color)
            else:
                self.np[first_led_index] = Color.OFF

            # Second LED: chord indicator
            if semitone in self._chord_semitones:
                self.np[second_led_index] = self._apply_brightness(self._chord_color)
            else:
                self.np[second_led_index] = Color.OFF

        self._dirty = True

    def update(self):
        """Push changes to LED hardware."""
        if self._dirty:
            self.np.write()
            self._dirty = False


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


class ButtonLedStripAsMatrixAdapter(LedMatrixHAL):
    """Adapter to make button LED strip work as LedMatrixHAL interface."""

    def __init__(self, button_led_strip, buttons_hal):
        """
        Args:
            button_led_strip: MCUButtonLedStripHAL instance
            buttons_hal: MCUButtonsHAL instance to monitor button states
        """
        self.led_strip = button_led_strip
        self.buttons = buttons_hal

    def clear(self):
        """Turn off all LEDs."""
        self.led_strip.clear()

    def set_button_led(self, index, color):
        """Set LED for button - ignores color, just lights white when pressed."""
        # We update based on actual button state in update()
        pass

    def set_pixel(self, x, y, color):
        """Not implemented - button strip is 1D."""
        pass

    def show_chord_visualization(self, notes, root_note):
        """Not implemented - button strip doesn't show chords."""
        pass

    def show_scale_indicator(self, scale_index, total_scales):
        """Not implemented - button strip doesn't show scale."""
        pass

    def update(self):
        """Update LEDs based on button states."""
        # Update each button LED based on button press state
        for i in range(min(16, len(self.buttons.buttons))):
            is_pressed = self.buttons.is_pressed(i)
            self.led_strip.set_button_state(i, is_pressed)
        self.led_strip.update()


def create_mcu_hardware_port():
    """
    Factory function to create fully configured MCU hardware.

    Returns:
        HardwarePort instance with all HAL implementations configured
    """
    # Initialize I2C Bus 0: All I2C devices (OLED, MCP23017)
    i2c = I2C(
        PinConfig.I2C_BUS,
        scl=Pin(PinConfig.I2C_SCL),
        sda=Pin(PinConfig.I2C_SDA),
    )

    # Initialize MCP23017 for 16 buttons
    mcp = MCP23017(i2c, address=PinConfig.MCP_ADDRESS)

    # Create HAL instances
    buttons = MCUButtonsHAL(mcp, PinConfig.BUTTON_PINS)

    # Dual encoder uses both left and right encoders
    encoder = MCUDualEncoderHAL(
        PinConfig.LEFT_ENCODER_CLK,
        PinConfig.LEFT_ENCODER_DT,
        PinConfig.LEFT_ENCODER_SW,
        PinConfig.RIGHT_ENCODER_CLK,
        PinConfig.RIGHT_ENCODER_DT,
        PinConfig.RIGHT_ENCODER_SW,
    )

    display = MCUDisplayHAL(
        i2c,
        PinConfig.OLED_WIDTH,
        PinConfig.OLED_HEIGHT,
        PinConfig.OLED_ADDRESS,
    )

    # Use button LED strip instead of matrix for current hardware
    button_led_strip = MCUButtonLedStripHAL(
        Pin(PinConfig.BUTTON_LED_PIN, Pin.OUT),
        PinConfig.BUTTON_LED_COUNT,
        PinConfig.BUTTON_LED_BRIGHTNESS,
    )
    # Wrap button LED strip to provide LedMatrixHAL interface
    led_matrix = ButtonLedStripAsMatrixAdapter(button_led_strip, buttons)

    # Triple MIDI output - 2 hardware UARTs + 1 software UART
    midi_output = MCUTripleMidiOutputHAL(
        PinConfig.MIDI_UART_ID_1,
        Pin(PinConfig.MIDI_TX_1),
        Pin(PinConfig.MIDI_RX),
        PinConfig.MIDI_UART_ID_2,
        Pin(PinConfig.MIDI_TX_2),
        Pin(PinConfig.MIDI_RX_DUMMY_2),
        Pin(PinConfig.MIDI_TX_3),  # Software UART for 3rd output
    )

    # Touch strip using MPR121 capacitive touch sensor
    if PinConfig.TOUCH_ENABLED:
        touch_strip = MCUTouchStripHAL(
            i2c, PinConfig.TOUCH_ADDRESS, reversed=PinConfig.TOUCH_REVERSED
        )
    else:
        touch_strip = MCUDummyTouchStripHAL()

    # Touch strip LED (WS2812) - 12 LEDs for visualization
    touch_strip_led = MCUTouchStripLedHAL(
        Pin(PinConfig.TOUCH_STRIP_LED_PIN, Pin.OUT),
        PinConfig.TOUCH_STRIP_LED_COUNT,
        PinConfig.TOUCH_STRIP_LED_BRIGHTNESS,
    )

    return HardwarePort(buttons, encoder, display, led_matrix, midi_output, touch_strip, touch_strip_led)
