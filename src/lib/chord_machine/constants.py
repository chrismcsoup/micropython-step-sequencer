"""
Constants for the Chord Machine application.
All magic strings and numbers are defined here for easy maintenance.
"""


# ============================================================================
# UI MODES
# ============================================================================
class Mode:
    """UI mode constants."""
    PLAY = "play"
    ROOT_SELECT = "root_select"
    SCALE_SELECT = "scale_select"
    
    # List of all modes in cycle order
    ALL = [PLAY, ROOT_SELECT, SCALE_SELECT]


# ============================================================================
# MODE DISPLAY INDICATORS
# ============================================================================
class ModeIndicator:
    """Characters shown on display for each mode."""
    PLAY = ">"
    ROOT_SELECT = "#"
    SCALE_SELECT = "*"
    UNKNOWN = "?"
    
    @classmethod
    def get(cls, mode):
        """Get indicator character for a mode."""
        indicators = {
            Mode.PLAY: cls.PLAY,
            Mode.ROOT_SELECT: cls.ROOT_SELECT,
            Mode.SCALE_SELECT: cls.SCALE_SELECT,
        }
        return indicators.get(mode, cls.UNKNOWN)


# ============================================================================
# COLORS (RGB tuples)
# ============================================================================
class Color:
    """RGB color constants for LEDs."""
    OFF = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 128, 0)
    
    # Application-specific colors
    CHORD_ACTIVE = GREEN
    MODE_PLAY = (0, 0, 50)       # Dim blue
    MODE_ROOT_SELECT = (50, 0, 50)   # Dim magenta
    MODE_SCALE_SELECT = (50, 50, 0)  # Dim yellow


# ============================================================================
# MIDI CONSTANTS
# ============================================================================
class Midi:
    """MIDI-related constants."""
    # Channel range
    CHANNEL_MIN = 0
    CHANNEL_MAX = 15
    
    # Velocity range
    VELOCITY_MIN = 0
    VELOCITY_MAX = 127
    VELOCITY_DEFAULT = 100
    
    # Note range
    NOTE_MIN = 0
    NOTE_MAX = 127
    
    # Default root note (C4)
    DEFAULT_ROOT_NOTE = 60
    DEFAULT_SCALE = "major"


# ============================================================================
# OCTAVE CONSTANTS
# ============================================================================
class Octave:
    """Octave-related constants."""
    MIN = 2   # C2 = MIDI 24
    MAX = 9   # C9 = MIDI 108
    REFERENCE = 4  # Octave 4 has no tick marks
    
    # Tick mark characters for octave display
    TICK_UP = "'"
    TICK_DOWN = ","


# ============================================================================
# HARDWARE CONSTANTS
# ============================================================================
class Hardware:
    """Hardware-related constants."""
    # Number of chord buttons
    NUM_CHORD_BUTTONS = 7
    TOTAL_BUTTONS = 8
    
    # Button index for special function
    SPECIAL_BUTTON_INDEX = 7
    
    # Encoder range
    ENCODER_MIN = -1000
    ENCODER_MAX = 1000
    ENCODER_START = 0
    
    # Encoder debounce
    ENCODER_DEBOUNCE_MS = 300
    
    # LED matrix size
    MATRIX_WIDTH = 8
    MATRIX_HEIGHT = 8
    MATRIX_LED_COUNT = 64
    
    # Display dimensions
    DISPLAY_WIDTH = 128
    DISPLAY_HEIGHT = 32
    DISPLAY_MAX_CHARS = 16
    
    # Touch strip (MPR121)
    TOUCH_PAD_COUNT = 12


# ============================================================================
# MUSIC CONSTANTS
# ============================================================================
class Music:
    """Music theory constants."""
    NOTES_PER_OCTAVE = 12
    SCALE_DEGREES = 7
