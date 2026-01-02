# Chord Machine Architecture

## Overview

This document describes a layered architecture for a **Chord Machine** that outputs diatonic chords (I-VII) via 8 buttons, with scale selection via rotary encoder, visual feedback on an 8x8 LED matrix, and display output on an OLED screen.

**Target Platform**: MicroPython (ESP32-S3, RP2040) with cross-platform compatibility.

The architecture cleanly separates:
1. **Business Logic** (music theory, chord generation) - Pure MicroPython, no hardware deps
2. **UI State Management** (application state, event handling) - Pure MicroPython
3. **Hardware Abstraction Layer** (platform-specific implementations)

This enables running the same core logic on:
- **MicroPython** on ESP32-S3 / RP2040 (primary target)
- **PyScript** in a web browser (using Web MIDI API)
- **CPython** for desktop testing

### MicroPython Compatibility Notes

All code follows MicroPython conventions:
- No type hints in function signatures (use docstrings instead)
- String concatenation with `+` instead of f-strings for maximum compatibility
- Avoid `os.path` module (use simple string paths)
- Memory-conscious design (avoid large temporary objects)
- `asyncio` for async operations (supported in MicroPython 1.19+)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        ChordMachineApp                                 │  │
│  │  - Main loop / event dispatch                                          │  │
│  │  - Coordinates UI state + business logic + HAL                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          ▼                          ▼                          ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────────┐
│   BUSINESS LOGIC    │  │  UI STATE MANAGER   │  │  HARDWARE ABSTRACTION   │
│                     │  │                     │  │        LAYER (HAL)      │
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │                         │
│  │  MusicTheory  │  │  │  │   UIState     │  │  │  ┌───────────────────┐  │
│  │  - scales     │  │  │  │  - current    │  │  │  │   HardwarePort    │  │
│  │  - intervals  │  │  │  │    scale      │  │  │  │   (Protocol)      │  │
│  │  - chord      │  │  │  │  - playing    │  │  │  └─────────┬─────────┘  │
│  │    building   │  │  │  │    chord      │  │  │            │            │
│  └───────────────┘  │  │  │  - encoder    │  │  │  ┌─────────▼─────────┐  │
│                     │  │  │    value      │  │  │  │  MCU Platform     │  │
│  ┌───────────────┐  │  │  └───────────────┘  │  │  │  - ButtonsHAL     │  │
│  │ ChordEngine   │  │  │                     │  │  │  - EncoderHAL     │  │
│  │ - get_chord() │  │  │  ┌───────────────┐  │  │  │  - DisplayHAL     │  │
│  │ - get_scale() │  │  │  │  EventBus     │  │  │  │  - LedMatrixHAL   │  │
│  │ - transpose() │  │  │  │  - subscribe  │  │  │  │  - MidiOutputHAL  │  │
│  └───────────────┘  │  │  │  - emit       │  │  │  └───────────────────┘  │
│                     │  │  └───────────────┘  │  │                         │
└─────────────────────┘  └─────────────────────┘  │  ┌───────────────────┐  │
                                                  │  │  Web Platform     │  │
                                                  │  │  - ButtonsHAL     │  │
                                                  │  │  - EncoderHAL     │  │
                                                  │  │  - DisplayHAL     │  │
                                                  │  │  - LedMatrixHAL   │  │
                                                  │  │  - MidiOutputHAL  │  │
                                                  │  └───────────────────┘  │
                                                  └─────────────────────────┘
```

---

## Layer Descriptions

### 1. Business Logic Layer (`src/lib/chord_machine/`)

Pure Python with **no hardware dependencies**. This layer contains all music theory and chord generation logic.

#### `music_theory.py`
```python
"""
Pure music theory calculations - no hardware dependencies.
"""

# Interval definitions (in semitones)
INTERVALS = {
    "unison": 0,
    "minor_second": 1,
    "major_second": 2,
    "minor_third": 3,
    "major_third": 4,
    "perfect_fourth": 5,
    "tritone": 6,
    "perfect_fifth": 7,
    "minor_sixth": 8,
    "major_sixth": 9,
    "minor_seventh": 10,
    "major_seventh": 11,
    "octave": 12,
}

# Scale definitions as interval patterns from root
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],          # W-W-H-W-W-W-H
    "natural_minor": [0, 2, 3, 5, 7, 8, 10],  # W-H-W-W-H-W-W
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11], # W-H-W-W-H-A2-H
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],  # W-H-W-W-W-W-H (ascending)
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
}

# Root note names
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Chord quality based on intervals
CHORD_TYPES = {
    "major": [0, 4, 7],           # root, major 3rd, perfect 5th
    "minor": [0, 3, 7],           # root, minor 3rd, perfect 5th
    "diminished": [0, 3, 6],      # root, minor 3rd, diminished 5th
    "augmented": [0, 4, 8],       # root, major 3rd, augmented 5th
    "major7": [0, 4, 7, 11],
    "minor7": [0, 3, 7, 10],
    "dominant7": [0, 4, 7, 10],
    "diminished7": [0, 3, 6, 9],
    "half_diminished7": [0, 3, 6, 10],
}

# Roman numeral labels
ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII"]


def get_scale_names() -> list:
    """Return list of available scale names."""
    return list(SCALES.keys())


def get_scale_degrees(scale_name: str) -> list:
    """Return the interval pattern for a scale."""
    return SCALES.get(scale_name, SCALES["major"])


def note_name(midi_note: int) -> str:
    """Convert MIDI note number to note name."""
    return NOTE_NAMES[midi_note % 12]


def get_chord_quality_in_scale(scale_name: str, degree: int) -> str:
    """
    Determine chord quality for a scale degree (0-6).
    Returns: 'major', 'minor', or 'diminished'
    """
    scale = SCALES.get(scale_name, SCALES["major"])
    
    # Get intervals for root, third, fifth of this chord
    root_interval = scale[degree]
    third_interval = scale[(degree + 2) % 7]
    fifth_interval = scale[(degree + 4) % 7]
    
    # Handle octave wrapping
    if third_interval < root_interval:
        third_interval += 12
    if fifth_interval < root_interval:
        fifth_interval += 12
    
    third_size = third_interval - root_interval
    fifth_size = fifth_interval - root_interval
    
    # Determine quality
    if third_size == 4 and fifth_size == 7:
        return "major"
    elif third_size == 3 and fifth_size == 7:
        return "minor"
    elif third_size == 3 and fifth_size == 6:
        return "diminished"
    elif third_size == 4 and fifth_size == 8:
        return "augmented"
    else:
        return "major"  # fallback
```

#### `chord_engine.py`
```python
"""
Chord generation engine - pure business logic.
"""
from .music_theory import (
    SCALES, CHORD_TYPES, ROMAN_NUMERALS, NOTE_NAMES,
    get_chord_quality_in_scale, get_scale_names
)


class ChordEngine:
    """
    Generates MIDI note numbers for diatonic chords.
    Pure logic - no hardware dependencies.
    """
    
    def __init__(self, root_note: int = 60, scale_name: str = "major"):
        """
        Args:
            root_note: MIDI note number for root (60 = C4)
            scale_name: Name of scale to use
        """
        self.root_note = root_note
        self._scale_name = scale_name
        self._scale_index = 0
        self._available_scales = get_scale_names()
    
    @property
    def scale_name(self) -> str:
        return self._scale_name
    
    @scale_name.setter
    def scale_name(self, name: str):
        if name in SCALES:
            self._scale_name = name
            self._scale_index = self._available_scales.index(name)
    
    @property
    def scale_index(self) -> int:
        return self._scale_index
    
    @scale_index.setter
    def scale_index(self, index: int):
        index = index % len(self._available_scales)
        self._scale_name = self._available_scales[index]
        self._scale_index = index
    
    def get_scale_display_name(self) -> str:
        """Return formatted scale name for display."""
        root_name = NOTE_NAMES[self.root_note % 12]
        return f"{root_name} {self._scale_name.replace('_', ' ').title()}"
    
    def get_chord(self, degree: int) -> tuple:
        """
        Get MIDI notes for a diatonic chord.
        
        Args:
            degree: Scale degree 0-6 (I-VII)
            
        Returns:
            Tuple of (chord_notes, chord_name, roman_numeral)
            - chord_notes: list of MIDI note numbers
            - chord_name: e.g., "Cm", "Ddim"
            - roman_numeral: e.g., "ii", "viio"
        """
        if not 0 <= degree <= 6:
            degree = degree % 7
        
        scale = SCALES[self._scale_name]
        quality = get_chord_quality_in_scale(self._scale_name, degree)
        chord_intervals = CHORD_TYPES[quality]
        
        # Calculate root note for this degree
        chord_root = self.root_note + scale[degree]
        
        # Build chord notes
        chord_notes = [chord_root + interval for interval in chord_intervals]
        
        # Build chord name
        root_name = NOTE_NAMES[chord_root % 12]
        quality_suffix = {
            "major": "",
            "minor": "m",
            "diminished": "dim",
            "augmented": "aug",
        }.get(quality, "")
        chord_name = f"{root_name}{quality_suffix}"
        
        # Build roman numeral (uppercase for major, lowercase for minor/dim)
        numeral = ROMAN_NUMERALS[degree]
        if quality in ["minor", "diminished"]:
            numeral = numeral.lower()
        if quality == "diminished":
            numeral += "°"
        
        return (chord_notes, chord_name, numeral)
    
    def get_all_chords_in_scale(self) -> list:
        """Return info for all 7 diatonic chords."""
        return [self.get_chord(i) for i in range(7)]
    
    def next_scale(self) -> str:
        """Cycle to next scale, return new scale name."""
        self.scale_index = (self._scale_index + 1) % len(self._available_scales)
        return self._scale_name
    
    def prev_scale(self) -> str:
        """Cycle to previous scale, return new scale name."""
        self.scale_index = (self._scale_index - 1) % len(self._available_scales)
        return self._scale_name
```

---

### 2. UI State Management Layer (`src/lib/chord_machine/`)

Manages application state and provides an event-driven architecture.

#### `ui_state.py`
```python
"""
UI State management - platform independent.
Manages application state and events.
"""
from .chord_engine import ChordEngine


class Event:
    """Simple event class for state changes."""
    SCALE_CHANGED = "scale_changed"
    CHORD_TRIGGERED = "chord_triggered"
    CHORD_RELEASED = "chord_released"
    ENCODER_CHANGED = "encoder_changed"
    MODE_CHANGED = "mode_changed"


class UIState:
    """
    Centralized UI state container.
    All UI-related state lives here.
    """
    
    def __init__(self, chord_engine: ChordEngine):
        self.chord_engine = chord_engine
        
        # Current state
        self.current_scale_index = 0
        self.active_chord_degree = None  # 0-6 or None
        self.encoder_value = 0
        self.mode = "play"  # "play" or "settings"
        
        # Visual state
        self.led_states = [False] * 8  # 8 buttons worth of LED feedback
        self.display_dirty = True  # Flag to trigger display update
        
        # Event subscribers
        self._subscribers = {}
    
    def subscribe(self, event_type: str, callback):
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def emit(self, event_type: str, data=None):
        """Emit an event to all subscribers."""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(data)
    
    def set_scale(self, index: int):
        """Change the current scale."""
        self.current_scale_index = index
        self.chord_engine.scale_index = index
        self.display_dirty = True
        self.emit(Event.SCALE_CHANGED, {
            "index": index,
            "name": self.chord_engine.scale_name
        })
    
    def trigger_chord(self, degree: int):
        """Trigger a chord (button pressed)."""
        self.active_chord_degree = degree
        self.led_states[degree] = True
        chord_notes, chord_name, numeral = self.chord_engine.get_chord(degree)
        self.display_dirty = True
        self.emit(Event.CHORD_TRIGGERED, {
            "degree": degree,
            "notes": chord_notes,
            "name": chord_name,
            "numeral": numeral
        })
    
    def release_chord(self, degree: int):
        """Release a chord (button released)."""
        if self.active_chord_degree == degree:
            self.active_chord_degree = None
        self.led_states[degree] = False
        self.emit(Event.CHORD_RELEASED, {
            "degree": degree
        })
    
    def update_encoder(self, delta: int):
        """Handle encoder rotation."""
        self.encoder_value += delta
        self.emit(Event.ENCODER_CHANGED, {
            "value": self.encoder_value,
            "delta": delta
        })
        
        # In play mode, encoder changes scale
        if self.mode == "play":
            if delta > 0:
                self.chord_engine.next_scale()
            else:
                self.chord_engine.prev_scale()
            self.set_scale(self.chord_engine.scale_index)
    
    def toggle_mode(self):
        """Toggle between play and settings mode."""
        self.mode = "settings" if self.mode == "play" else "play"
        self.display_dirty = True
        self.emit(Event.MODE_CHANGED, {"mode": self.mode})
    
    def get_display_data(self) -> dict:
        """Get data needed for display rendering."""
        chord_info = None
        if self.active_chord_degree is not None:
            _, name, numeral = self.chord_engine.get_chord(self.active_chord_degree)
            chord_info = {"name": name, "numeral": numeral}
        
        return {
            "scale_name": self.chord_engine.get_scale_display_name(),
            "active_chord": chord_info,
            "mode": self.mode,
        }
```

---

### 3. Hardware Abstraction Layer (HAL)

Defines protocols/interfaces that platform-specific implementations must follow.

#### `hal_protocol.py` - Abstract Interface Definitions
```python
"""
Hardware Abstraction Layer Protocol Definitions.
These are abstract base classes that each platform must implement.
"""


class ButtonsHAL:
    """Abstract interface for button input."""
    
    def update(self):
        """Poll button states. Call in main loop."""
        raise NotImplementedError
    
    def was_pressed(self, index: int) -> bool:
        """Check if button was just pressed."""
        raise NotImplementedError
    
    def was_released(self, index: int) -> bool:
        """Check if button was just released."""
        raise NotImplementedError
    
    def was_long_pressed(self, index: int) -> bool:
        """Check if button was long-pressed."""
        raise NotImplementedError
    
    def is_pressed(self, index: int) -> bool:
        """Check if button is currently pressed."""
        raise NotImplementedError


class EncoderHAL:
    """Abstract interface for rotary encoder."""
    
    def get_delta(self) -> int:
        """Get rotation delta since last call. Positive = clockwise."""
        raise NotImplementedError
    
    def was_button_pressed(self) -> bool:
        """Check if encoder button was pressed."""
        raise NotImplementedError
    
    def get_value(self) -> int:
        """Get absolute encoder value."""
        raise NotImplementedError
    
    def set_value(self, value: int):
        """Set encoder value (e.g., for resetting)."""
        raise NotImplementedError


class DisplayHAL:
    """Abstract interface for OLED display."""
    
    def clear(self):
        """Clear the display."""
        raise NotImplementedError
    
    def show_scale(self, scale_name: str):
        """Display the current scale name."""
        raise NotImplementedError
    
    def show_chord(self, chord_name: str, numeral: str):
        """Display the currently playing chord."""
        raise NotImplementedError
    
    def show_message(self, message: str):
        """Display a status message."""
        raise NotImplementedError
    
    def update(self):
        """Push changes to display hardware."""
        raise NotImplementedError


class LedMatrixHAL:
    """Abstract interface for LED matrix/strip."""
    
    def clear(self):
        """Turn off all LEDs."""
        raise NotImplementedError
    
    def set_button_led(self, index: int, color: tuple):
        """Set LED for a button (index 0-7)."""
        raise NotImplementedError
    
    def show_chord_visualization(self, notes: list, root_note: int):
        """Visualize chord notes on the matrix."""
        raise NotImplementedError
    
    def update(self):
        """Push changes to LED hardware."""
        raise NotImplementedError


class MidiOutputHAL:
    """Abstract interface for MIDI output."""
    
    def send_note_on(self, channel: int, note: int, velocity: int):
        """Send MIDI Note On message."""
        raise NotImplementedError
    
    def send_note_off(self, channel: int, note: int, velocity: int = 0):
        """Send MIDI Note Off message."""
        raise NotImplementedError
    
    def send_control_change(self, channel: int, control: int, value: int):
        """Send MIDI Control Change message."""
        raise NotImplementedError
    
    def send_chord_on(self, channel: int, notes: list, velocity: int):
        """Convenience: send Note On for multiple notes."""
        for note in notes:
            self.send_note_on(channel, note, velocity)
    
    def send_chord_off(self, channel: int, notes: list, velocity: int = 0):
        """Convenience: send Note Off for multiple notes."""
        for note in notes:
            self.send_note_off(channel, note, velocity)


class HardwarePort:
    """
    Complete hardware port interface.
    A platform provides an instance of this with all HAL implementations.
    """
    
    def __init__(
        self,
        buttons: ButtonsHAL,
        encoder: EncoderHAL,
        display: DisplayHAL,
        led_matrix: LedMatrixHAL,
        midi_output: MidiOutputHAL,
    ):
        self.buttons = buttons
        self.encoder = encoder
        self.display = display
        self.led_matrix = led_matrix
        self.midi_output = midi_output
    
    def update_inputs(self):
        """Poll all input devices."""
        self.buttons.update()
    
    def update_outputs(self):
        """Push all output changes."""
        self.display.update()
        self.led_matrix.update()
```

---

### 4. Platform Implementations

#### MCU Platform (`src/plat_mcu/hal_mcu.py`)

```python
"""
MicroPython MCU Hardware Implementation.
For ESP32-S3 with MCP23017 I/O expander.
"""
from machine import Pin, I2C
from neopixel import NeoPixel
from ssd1306 import SSD1306_I2C
from lib.midi import Midi, CHANNEL
from lib.mcp23017 import MCP23017, Rotary
from utils import Button

from lib.chord_machine.hal_protocol import (
    ButtonsHAL, EncoderHAL, DisplayHAL, LedMatrixHAL, MidiOutputHAL, HardwarePort
)


# ============================================================================
# PIN CONFIGURATION - Change these when hardware changes
# ============================================================================
class PinConfig:
    """Centralized pin assignments for the MCU."""
    # I2C for MCP23017 and OLED
    I2C_SCL = 6
    I2C_SDA = 5
    MCP_INTERRUPT = 4
    MCP_ADDRESS = 0x20
    
    # I2C for OLED (can be same bus)
    OLED_I2C_ID = 0
    OLED_SCL = 1
    OLED_SDA = 2
    OLED_WIDTH = 128
    OLED_HEIGHT = 32
    
    # NeoPixel LED Matrix
    NEOPIXEL_PIN = 14
    NEOPIXEL_COUNT = 64
    
    # MIDI UART
    MIDI_TX = 39
    MIDI_RX = 40
    MIDI_UART_ID = 1
    
    # MCP23017 pin assignments (encoder + buttons)
    ENCODER_CLK = 7
    ENCODER_DT = 6
    ENCODER_SW = 5
    BUTTON_PINS = [8, 9, 10, 11, 12, 13, 14, 15]  # 8 buttons on port B


# ============================================================================
# HAL IMPLEMENTATIONS
# ============================================================================

class MCUButtonsHAL(ButtonsHAL):
    """Button implementation using MCP23017."""
    
    def __init__(self, mcp: MCP23017, pin_numbers: list):
        self.buttons = []
        for pin_num in pin_numbers:
            mcp.pin(pin_num, mode=1, pullup=True)  # Input with pullup
            self.buttons.append(Button(mcp[pin_num]))
    
    def update(self):
        for btn in self.buttons:
            btn.update()
    
    def was_pressed(self, index: int) -> bool:
        return self.buttons[index].was_pressed()
    
    def was_released(self, index: int) -> bool:
        return self.buttons[index].was_released()
    
    def was_long_pressed(self, index: int) -> bool:
        return self.buttons[index].was_long_pressed()
    
    def is_pressed(self, index: int) -> bool:
        return self.buttons[index].is_pressed()


class MCUEncoderHAL(EncoderHAL):
    """Rotary encoder implementation using MCP23017."""
    
    def __init__(self, mcp: MCP23017, interrupt_pin: Pin, clk: int, dt: int, sw: int):
        self._value = 0
        self._last_value = 0
        self._button_pressed = False
        
        def callback(val, sw):
            self._value = val
            if sw:
                self._button_pressed = True
        
        self.rotary = Rotary(mcp.porta, interrupt_pin, clk, dt, sw, callback)
        self.rotary.start()
    
    def get_delta(self) -> int:
        delta = self._value - self._last_value
        self._last_value = self._value
        return delta
    
    def was_button_pressed(self) -> bool:
        if self._button_pressed:
            self._button_pressed = False
            return True
        return False
    
    def get_value(self) -> int:
        return self._value
    
    def set_value(self, value: int):
        self._value = value
        self._last_value = value
        self.rotary.value = value
    
    def stop(self):
        self.rotary.stop()


class MCUDisplayHAL(DisplayHAL):
    """OLED display implementation using SSD1306."""
    
    def __init__(self, i2c: I2C, width: int = 128, height: int = 32):
        self.oled = SSD1306_I2C(width, height, i2c)
        self.width = width
        self.height = height
        self._dirty = False
    
    def clear(self):
        self.oled.fill(0)
        self._dirty = True
    
    def show_scale(self, scale_name: str):
        self.oled.fill(0)
        self.oled.text("Scale:", 0, 0, 1)
        self.oled.text(scale_name[:16], 0, 12, 1)  # Truncate if too long
        self._dirty = True
    
    def show_chord(self, chord_name: str, numeral: str):
        # Show chord on right side, keep scale on left
        self.oled.fill_rect(64, 0, 64, 32, 0)  # Clear right half
        self.oled.text(numeral, 70, 0, 1)
        self.oled.text(chord_name, 70, 16, 1)
        self._dirty = True
    
    def show_message(self, message: str):
        self.oled.fill(0)
        self.oled.text(message[:16], 0, 12, 1)
        self._dirty = True
    
    def update(self):
        if self._dirty:
            self.oled.show()
            self._dirty = False


class MCULedMatrixHAL(LedMatrixHAL):
    """NeoPixel LED matrix implementation."""
    
    def __init__(self, pin: Pin, count: int = 64, brightness: float = 0.1):
        self.np = NeoPixel(pin, count)
        self.count = count
        self.brightness = brightness
        self._dirty = False
        
        # Color definitions
        self.COLORS = {
            "off": (0, 0, 0),
            "white": (255, 255, 255),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255),
        }
    
    def _apply_brightness(self, color: tuple) -> tuple:
        return tuple(int(c * self.brightness) for c in color)
    
    def clear(self):
        self.np.fill((0, 0, 0))
        self._dirty = True
    
    def set_button_led(self, index: int, color: tuple):
        """Set LED for button - maps to first row of matrix."""
        if 0 <= index < 8:
            self.np[index] = self._apply_brightness(color)
            self._dirty = True
    
    def show_chord_visualization(self, notes: list, root_note: int):
        """Visualize chord notes on matrix - each row = one octave."""
        self.clear()
        for note in notes:
            # Map MIDI note to matrix position
            octave = (note // 12) % 8  # Row
            pitch_class = note % 12
            col = int(pitch_class * 8 / 12)  # Scale 0-11 to 0-7
            
            led_index = octave * 8 + col
            if 0 <= led_index < self.count:
                self.np[led_index] = self._apply_brightness(self.COLORS["cyan"])
        self._dirty = True
    
    def update(self):
        if self._dirty:
            self.np.write()
            self._dirty = False


class MCUMidiOutputHAL(MidiOutputHAL):
    """TRS MIDI output implementation."""
    
    def __init__(self, uart_id: int, tx_pin: Pin, rx_pin: Pin):
        self.midi = Midi(uart_id, tx=tx_pin, rx=rx_pin)
    
    def send_note_on(self, channel: int, note: int, velocity: int):
        self.midi.send_note_on(channel, note, velocity=velocity)
    
    def send_note_off(self, channel: int, note: int, velocity: int = 0):
        self.midi.send_note_off(channel, note)
    
    def send_control_change(self, channel: int, control: int, value: int):
        self.midi.send_control_change(channel, control, value=value)


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_mcu_hardware_port() -> HardwarePort:
    """
    Factory function to create fully configured MCU hardware.
    """
    # Initialize I2C buses
    i2c_mcp = I2C(0, scl=Pin(PinConfig.I2C_SCL), sda=Pin(PinConfig.I2C_SDA))
    i2c_oled = I2C(PinConfig.OLED_I2C_ID, scl=Pin(PinConfig.OLED_SCL), sda=Pin(PinConfig.OLED_SDA))
    
    # Initialize MCP23017
    mcp = MCP23017(i2c_mcp, address=PinConfig.MCP_ADDRESS)
    
    # Configure MCP pins for encoder
    for pin_num in range(8):
        mcp.pin(pin_num, mode=0, value=0)  # Port A: outputs
    
    # Interrupt pin
    interrupt_pin = Pin(PinConfig.MCP_INTERRUPT, mode=Pin.IN)
    
    # Create HAL instances
    buttons = MCUButtonsHAL(mcp, PinConfig.BUTTON_PINS)
    encoder = MCUEncoderHAL(
        mcp, interrupt_pin,
        PinConfig.ENCODER_CLK, PinConfig.ENCODER_DT, PinConfig.ENCODER_SW
    )
    display = MCUDisplayHAL(i2c_oled, PinConfig.OLED_WIDTH, PinConfig.OLED_HEIGHT)
    led_matrix = MCULedMatrixHAL(Pin(PinConfig.NEOPIXEL_PIN, Pin.OUT), PinConfig.NEOPIXEL_COUNT)
    midi_output = MCUMidiOutputHAL(
        PinConfig.MIDI_UART_ID,
        Pin(PinConfig.MIDI_TX),
        Pin(PinConfig.MIDI_RX)
    )
    
    return HardwarePort(buttons, encoder, display, led_matrix, midi_output)
```

#### Web Platform (`src/plat_web/hal_web.py`)

```python
"""
Web/PyScript Hardware Implementation.
Uses Web MIDI API and HTML elements.
"""
from lib.chord_machine.hal_protocol import (
    ButtonsHAL, EncoderHAL, DisplayHAL, LedMatrixHAL, MidiOutputHAL, HardwarePort
)

# In PyScript, these would be imported from js
# from js import document, navigator
# from pyodide.ffi import create_proxy


class WebButtonsHAL(ButtonsHAL):
    """Button implementation using HTML buttons."""
    
    def __init__(self, button_ids: list):
        self.button_ids = button_ids
        self._pressed = [False] * len(button_ids)
        self._released = [False] * len(button_ids)
        self._current = [False] * len(button_ids)
        
        # In real implementation, attach event listeners to DOM elements
        # for i, btn_id in enumerate(button_ids):
        #     element = document.getElementById(btn_id)
        #     element.addEventListener("mousedown", create_proxy(lambda e, idx=i: self._on_press(idx)))
        #     element.addEventListener("mouseup", create_proxy(lambda e, idx=i: self._on_release(idx)))
    
    def _on_press(self, index: int):
        self._pressed[index] = True
        self._current[index] = True
    
    def _on_release(self, index: int):
        self._released[index] = True
        self._current[index] = False
    
    def update(self):
        pass  # Events are handled asynchronously in browser
    
    def was_pressed(self, index: int) -> bool:
        if self._pressed[index]:
            self._pressed[index] = False
            return True
        return False
    
    def was_released(self, index: int) -> bool:
        if self._released[index]:
            self._released[index] = False
            return True
        return False
    
    def was_long_pressed(self, index: int) -> bool:
        return False  # Simplified - no long press in web version
    
    def is_pressed(self, index: int) -> bool:
        return self._current[index]


class WebEncoderHAL(EncoderHAL):
    """Encoder implementation using HTML slider or mouse wheel."""
    
    def __init__(self, element_id: str):
        self._value = 0
        self._last_value = 0
        self._button_pressed = False
        
        # In real implementation:
        # element = document.getElementById(element_id)
        # element.addEventListener("input", create_proxy(self._on_change))
    
    def _on_change(self, event):
        self._value = int(event.target.value)
    
    def get_delta(self) -> int:
        delta = self._value - self._last_value
        self._last_value = self._value
        return delta
    
    def was_button_pressed(self) -> bool:
        if self._button_pressed:
            self._button_pressed = False
            return True
        return False
    
    def get_value(self) -> int:
        return self._value
    
    def set_value(self, value: int):
        self._value = value
        self._last_value = value


class WebDisplayHAL(DisplayHAL):
    """Display implementation using HTML elements."""
    
    def __init__(self, scale_element_id: str, chord_element_id: str):
        self.scale_id = scale_element_id
        self.chord_id = chord_element_id
    
    def clear(self):
        # document.getElementById(self.scale_id).textContent = ""
        # document.getElementById(self.chord_id).textContent = ""
        pass
    
    def show_scale(self, scale_name: str):
        # document.getElementById(self.scale_id).textContent = scale_name
        pass
    
    def show_chord(self, chord_name: str, numeral: str):
        # document.getElementById(self.chord_id).textContent = f"{numeral} - {chord_name}"
        pass
    
    def show_message(self, message: str):
        pass
    
    def update(self):
        pass  # DOM updates are immediate


class WebLedMatrixHAL(LedMatrixHAL):
    """LED matrix using CSS grid of divs."""
    
    def __init__(self, container_id: str, count: int = 64):
        self.container_id = container_id
        self.count = count
    
    def clear(self):
        # for i in range(self.count):
        #     led = document.getElementById(f"led-{i}")
        #     led.style.backgroundColor = "black"
        pass
    
    def set_button_led(self, index: int, color: tuple):
        # r, g, b = color
        # led = document.getElementById(f"led-{index}")
        # led.style.backgroundColor = f"rgb({r},{g},{b})"
        pass
    
    def show_chord_visualization(self, notes: list, root_note: int):
        pass
    
    def update(self):
        pass


class WebMidiOutputHAL(MidiOutputHAL):
    """MIDI output using Web MIDI API."""
    
    def __init__(self):
        self._output = None
        # In real implementation:
        # self._init_midi()
    
    async def _init_midi(self):
        # access = await navigator.requestMIDIAccess()
        # outputs = access.outputs.values()
        # self._output = next(outputs, None)
        pass
    
    def send_note_on(self, channel: int, note: int, velocity: int):
        if self._output:
            # Note On: 0x90 + channel, note, velocity
            # self._output.send([0x90 | channel, note, velocity])
            pass
    
    def send_note_off(self, channel: int, note: int, velocity: int = 0):
        if self._output:
            # Note Off: 0x80 + channel, note, velocity
            # self._output.send([0x80 | channel, note, velocity])
            pass
    
    def send_control_change(self, channel: int, control: int, value: int):
        if self._output:
            # CC: 0xB0 + channel, control, value
            # self._output.send([0xB0 | channel, control, value])
            pass


def create_web_hardware_port() -> HardwarePort:
    """Factory function to create web-based hardware port."""
    buttons = WebButtonsHAL([f"btn-{i}" for i in range(8)])
    encoder = WebEncoderHAL("scale-selector")
    display = WebDisplayHAL("scale-display", "chord-display")
    led_matrix = WebLedMatrixHAL("led-grid")
    midi_output = WebMidiOutputHAL()
    
    return HardwarePort(buttons, encoder, display, led_matrix, midi_output)
```

---

### 5. Main Application

#### `chord_machine_app.py`
```python
"""
Main Chord Machine Application.
Ties together business logic, UI state, and hardware.
"""
from lib.chord_machine.chord_engine import ChordEngine
from lib.chord_machine.ui_state import UIState, Event
from lib.chord_machine.hal_protocol import HardwarePort


class ChordMachineApp:
    """
    Main application class for the Chord Machine.
    Platform-independent - receives hardware through dependency injection.
    """
    
    def __init__(self, hardware: HardwarePort, midi_channel: int = 0):
        # Business logic
        self.chord_engine = ChordEngine(root_note=60, scale_name="major")
        
        # UI State
        self.ui_state = UIState(self.chord_engine)
        
        # Hardware (injected)
        self.hw = hardware
        
        # Config
        self.midi_channel = midi_channel
        self.velocity = 100
        
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
            self._active_notes = data["notes"]
            
            # Update LEDs
            self.hw.led_matrix.set_button_led(
                data["degree"], (0, 255, 0)  # Green
            )
            self.hw.led_matrix.show_chord_visualization(
                data["notes"], self.chord_engine.root_note
            )
            
            # Update display
            self.hw.display.show_chord(data["name"], data["numeral"])
        
        def on_chord_released(data):
            # Send MIDI note offs
            if self._active_notes:
                self.hw.midi_output.send_chord_off(
                    self.midi_channel, self._active_notes
                )
                self._active_notes = []
            
            # Update LEDs
            self.hw.led_matrix.set_button_led(data["degree"], (0, 0, 0))
            self.hw.led_matrix.clear()
        
        def on_scale_changed(data):
            self._update_display()
        
        def on_mode_changed(data):
            self._update_display()
        
        # Register handlers
        self.ui_state.subscribe(Event.CHORD_TRIGGERED, on_chord_triggered)
        self.ui_state.subscribe(Event.CHORD_RELEASED, on_chord_released)
        self.ui_state.subscribe(Event.SCALE_CHANGED, on_scale_changed)
        self.ui_state.subscribe(Event.MODE_CHANGED, on_mode_changed)
    
    def _update_display(self):
        """Update display with current state."""
        display_data = self.ui_state.get_display_data()
        self.hw.display.show_scale(display_data["scale_name"])
        if display_data["active_chord"]:
            self.hw.display.show_chord(
                display_data["active_chord"]["name"],
                display_data["active_chord"]["numeral"]
            )
    
    def update(self):
        """
        Main update loop - call this frequently.
        Polls inputs and processes state changes.
        """
        # Poll hardware inputs
        self.hw.update_inputs()
        
        # Check encoder
        encoder_delta = self.hw.encoder.get_delta()
        if encoder_delta != 0:
            self.ui_state.update_encoder(encoder_delta)
        
        # Check encoder button for mode toggle
        if self.hw.encoder.was_button_pressed():
            self.ui_state.toggle_mode()
            self.hw.encoder.set_value(0)
        
        # Check each button
        for i in range(8):
            if i < 7:  # Only 7 chord degrees (I-VII)
                if self.hw.buttons.was_pressed(i):
                    self.ui_state.trigger_chord(i)
                
                if self.hw.buttons.was_released(i):
                    self.ui_state.release_chord(i)
            else:
                # Button 8 could be used for special function
                if self.hw.buttons.was_long_pressed(i):
                    # e.g., Reset to default scale
                    self.chord_engine.scale_name = "major"
                    self.ui_state.set_scale(0)
        
        # Push output updates
        self.hw.update_outputs()
    
    def cleanup(self):
        """Clean shutdown - turn off all notes and LEDs."""
        if self._active_notes:
            self.hw.midi_output.send_chord_off(self.midi_channel, self._active_notes)
        self.hw.led_matrix.clear()
        self.hw.led_matrix.update()
        self.hw.display.clear()
        self.hw.display.update()
```

---

### 6. Platform Entry Points

#### MCU Entry Point (`src/plat_mcu/main.py`)
```python
"""
MicroPython entry point for Chord Machine.
"""
import asyncio
from hal_mcu import create_mcu_hardware_port
from lib.chord_machine.chord_machine_app import ChordMachineApp


async def main():
    # Create hardware port for this platform
    hardware = create_mcu_hardware_port()
    
    # Create application
    app = ChordMachineApp(hardware, midi_channel=0)
    
    print("Chord Machine started!")
    print("Use buttons 1-7 for chords I-VII")
    print("Rotate encoder to change scale")
    print("Press encoder to toggle mode")
    
    try:
        while True:
            app.update()
            await asyncio.sleep_ms(1)  # ~1000Hz update rate
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        app.cleanup()
        print("Done.")


asyncio.run(main())
```

#### Web Entry Point (`src/plat_web/app.py`)
```python
"""
PyScript entry point for Chord Machine.
"""
from hal_web import create_web_hardware_port
from lib.chord_machine.chord_machine_app import ChordMachineApp

# In PyScript, use js and pyodide imports
# from js import setInterval
# from pyodide.ffi import create_proxy


def main():
    # Create hardware port for web platform
    hardware = create_web_hardware_port()
    
    # Create application
    app = ChordMachineApp(hardware, midi_channel=0)
    
    # Set up update loop (60fps)
    def update_loop():
        app.update()
    
    # In real PyScript:
    # setInterval(create_proxy(update_loop), 16)  # ~60fps
    
    print("Web Chord Machine started!")


# Called when PyScript loads
main()
```

---

## Directory Structure

```
src/
├── lib/
│   └── chord_machine/
│       ├── __init__.py
│       ├── music_theory.py      # Pure music theory (no deps)
│       ├── chord_engine.py      # Chord generation logic
│       ├── ui_state.py          # State management
│       ├── hal_protocol.py      # Abstract HAL interfaces
│       └── chord_machine_app.py # Main application
│
├── plat_mcu/
│   ├── main.py                  # MCU entry point
│   ├── hal_mcu.py               # MCU HAL implementations
│   └── utils/
│       └── button.py            # Existing button utility
│
└── plat_web/
    ├── app.py                   # Web entry point
    ├── hal_web.py               # Web HAL implementations
    ├── index.html               # Web UI
    └── static/
        ├── css/styles.css
        └── js/main.js
```

---

## Key Design Principles

### 1. **Dependency Injection**
The `ChordMachineApp` receives its hardware through constructor injection, making it testable and platform-agnostic.

### 2. **Protocol-Based HAL**
Abstract base classes define the contract each platform must fulfill. Python's duck typing means we don't need formal interfaces.

### 3. **Event-Driven UI State**
The `UIState` class uses a simple pub/sub pattern to decouple state changes from their effects.

### 4. **Pure Business Logic**
`MusicTheory` and `ChordEngine` have zero hardware dependencies and can be unit tested on any Python.

### 5. **Factory Functions**
Each platform provides a factory function (`create_mcu_hardware_port()`, `create_web_hardware_port()`) that assembles and configures all hardware.

---

## Testing Strategy

```python
# test/test_chord_engine.py
"""Unit tests for business logic - runs on any Python."""

from lib.chord_machine.chord_engine import ChordEngine
from lib.chord_machine.music_theory import SCALES

def test_c_major_chord_i():
    engine = ChordEngine(root_note=60, scale_name="major")
    notes, name, numeral = engine.get_chord(0)
    assert notes == [60, 64, 67]  # C, E, G
    assert name == "C"
    assert numeral == "I"

def test_c_major_chord_ii():
    engine = ChordEngine(root_note=60, scale_name="major")
    notes, name, numeral = engine.get_chord(1)
    assert notes == [62, 65, 69]  # D, F, A
    assert name == "Dm"
    assert numeral == "ii"

def test_scale_cycling():
    engine = ChordEngine()
    initial = engine.scale_name
    engine.next_scale()
    assert engine.scale_name != initial
    for _ in range(len(SCALES)):
        engine.next_scale()
    assert engine.scale_name == initial  # Full cycle
```

### Mock HAL for Testing
```python
# test/mock_hal.py
"""Mock HAL implementations for testing."""

from lib.chord_machine.hal_protocol import (
    ButtonsHAL, EncoderHAL, DisplayHAL, LedMatrixHAL, MidiOutputHAL, HardwarePort
)


class MockButtonsHAL(ButtonsHAL):
    def __init__(self):
        self._pressed = [False] * 8
        self._released = [False] * 8
    
    def simulate_press(self, index):
        self._pressed[index] = True
    
    def simulate_release(self, index):
        self._released[index] = True
    
    def update(self):
        pass
    
    def was_pressed(self, index):
        if self._pressed[index]:
            self._pressed[index] = False
            return True
        return False
    
    def was_released(self, index):
        if self._released[index]:
            self._released[index] = False
            return True
        return False
    
    def was_long_pressed(self, index):
        return False
    
    def is_pressed(self, index):
        return False


class MockMidiOutputHAL(MidiOutputHAL):
    def __init__(self):
        self.sent_messages = []
    
    def send_note_on(self, channel, note, velocity):
        self.sent_messages.append(("note_on", channel, note, velocity))
    
    def send_note_off(self, channel, note, velocity=0):
        self.sent_messages.append(("note_off", channel, note, velocity))
    
    def send_control_change(self, channel, control, value):
        self.sent_messages.append(("cc", channel, control, value))


# ... similar mocks for other HAL classes
```

---

## Migration Checklist

When changing hardware (e.g., different MCU, different pin assignments):

1. **Update `PinConfig` class** in `hal_mcu.py`
2. **Implement any new HAL classes** if hardware differs significantly
3. **Update factory function** `create_mcu_hardware_port()`
4. **Test with mock HAL first**, then on real hardware

When adding a new platform:

1. Create new `hal_<platform>.py` with implementations of all HAL protocols
2. Create factory function `create_<platform>_hardware_port()`
3. Create platform entry point that uses the factory
4. Reuse all code in `src/lib/chord_machine/` unchanged

---

## Future Enhancements

- **MIDI Input**: Add `MidiInputHAL` protocol for receiving external MIDI
- **Persistence**: Add `StorageHAL` for saving/loading presets
- **USB MIDI**: Add USB MIDI HAL for direct computer connection
- **Chord Voicings**: Extend `ChordEngine` with inversions and voicings
- **Arpeggiator**: Add arpeggio patterns as a business logic module
