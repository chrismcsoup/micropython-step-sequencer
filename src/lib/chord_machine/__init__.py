"""
Chord Machine - Platform-independent chord generation and MIDI output.
"""

from .music_theory import (
    INTERVALS,
    SCALES,
    NOTE_NAMES,
    CHORD_TYPES,
    ROMAN_NUMERALS,
    get_scale_names,
    get_scale_degrees,
    note_name,
    get_chord_quality_in_scale,
)
from .chord_engine import ChordEngine
from .ui_state import UIState, Event
from .hal_protocol import (
    ButtonsHAL,
    EncoderHAL,
    DisplayHAL,
    LedMatrixHAL,
    MidiOutputHAL,
    HardwarePort,
)
from .chord_machine_app import ChordMachineApp

__all__ = [
    # Music Theory
    "INTERVALS",
    "SCALES",
    "NOTE_NAMES",
    "CHORD_TYPES",
    "ROMAN_NUMERALS",
    "get_scale_names",
    "get_scale_degrees",
    "note_name",
    "get_chord_quality_in_scale",
    # Engine
    "ChordEngine",
    # UI State
    "UIState",
    "Event",
    # HAL Protocol
    "ButtonsHAL",
    "EncoderHAL",
    "DisplayHAL",
    "LedMatrixHAL",
    "MidiOutputHAL",
    "HardwarePort",
    # Application
    "ChordMachineApp",
]
