"""
Pure music theory calculations - no hardware dependencies.
This module can run on any Python implementation (CPython, MicroPython, PyScript).
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
    "major": [0, 2, 4, 5, 7, 9, 11],  # W-W-H-W-W-W-H
    "natural_minor": [0, 2, 3, 5, 7, 8, 10],  # W-H-W-W-H-W-W
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],  # W-H-W-W-H-A2-H
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
    "major": [0, 4, 7],  # root, major 3rd, perfect 5th
    "minor": [0, 3, 7],  # root, minor 3rd, perfect 5th
    "diminished": [0, 3, 6],  # root, minor 3rd, diminished 5th
    "augmented": [0, 4, 8],  # root, major 3rd, augmented 5th
    "major7": [0, 4, 7, 11],
    "minor7": [0, 3, 7, 10],
    "dominant7": [0, 4, 7, 10],
    "diminished7": [0, 3, 6, 9],
    "half_diminished7": [0, 3, 6, 10],
}

# Roman numeral labels
ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII"]


def get_scale_names():
    """Return list of available scale names."""
    # Use list() for MicroPython dict_keys compatibility
    return list(SCALES.keys())


def get_scale_degrees(scale_name):
    """Return the interval pattern for a scale."""
    return SCALES.get(scale_name, SCALES["major"])


def note_name(midi_note):
    """Convert MIDI note number to note name."""
    return NOTE_NAMES[midi_note % 12]


def get_chord_quality_in_scale(scale_name, degree):
    """
    Determine chord quality for a scale degree (0-6).
    Returns: 'major', 'minor', 'diminished', or 'augmented'
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

    # Determine quality based on interval sizes
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


def get_scale_semitones(scale_name):
    """
    Get set of semitones (0-11) that are in the scale.
    
    Args:
        scale_name: Name of the scale
        
    Returns:
        Set of semitone values (0-11) in the scale
    """
    return set(SCALES.get(scale_name, SCALES["major"]))


def get_chord_semitones(scale_name, chord_degree):
    """
    Get set of semitones (0-11) that are in the chord for a given scale degree.
    
    Args:
        scale_name: Name of the scale
        chord_degree: Scale degree 0-6 (I-VII), or None for no chord
        
    Returns:
        Set of semitone values (0-11) in the chord
    """
    if chord_degree is None:
        return set()
    
    scale_intervals = SCALES.get(scale_name, SCALES["major"])
    quality = get_chord_quality_in_scale(scale_name, chord_degree)
    chord_type = CHORD_TYPES[quality]
    
    # Get the root note's semitone offset in the scale
    chord_root_semitone = scale_intervals[chord_degree]
    
    # Build chord semitones (mod 12 to stay in 0-11 range)
    chord_semitones = set()
    for interval in chord_type:
        chord_semitones.add((chord_root_semitone + interval) % 12)
    
    return chord_semitones
