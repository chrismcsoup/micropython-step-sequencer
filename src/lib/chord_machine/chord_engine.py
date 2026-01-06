"""
Chord generation engine - pure business logic.
No hardware dependencies.
"""
from .music_theory import (
    SCALES,
    CHORD_TYPES,
    ROMAN_NUMERALS,
    NOTE_NAMES,
    get_chord_quality_in_scale,
    get_scale_names,
)
from .constants import Octave, Music


class ChordEngine:
    """
    Generates MIDI note numbers for diatonic chords.
    Pure logic - no hardware dependencies.
    """

    def __init__(self, root_note=60, scale_name="major"):
        """
        Args:
            root_note: MIDI note number for root (60 = C4)
            scale_name: Name of scale to use
        """
        # Split root_note into note (0-11) and octave
        self._root_note_class = root_note % Music.NOTES_PER_OCTAVE  # 0=C, 1=C#, etc.
        self._octave = root_note // Music.NOTES_PER_OCTAVE  # MIDI octave number
        
        self._scale_name = scale_name
        self._scale_index = 0
        self._available_scales = get_scale_names()

        # Set initial scale index
        if scale_name in self._available_scales:
            self._scale_index = self._available_scales.index(scale_name)

    @property
    def root_note(self):
        """Get the root note as MIDI note number."""
        return self._octave * Music.NOTES_PER_OCTAVE + self._root_note_class
    
    @property
    def octave(self):
        """Get the current octave (0-10)."""
        return self._octave
    
    @property
    def root_note_class(self):
        """Get the root note class (0-11, where 0=C)."""
        return self._root_note_class

    @property
    def scale_name(self):
        return self._scale_name

    @scale_name.setter
    def scale_name(self, name):
        if name in SCALES:
            self._scale_name = name
            self._scale_index = self._available_scales.index(name)

    @property
    def scale_index(self):
        return self._scale_index

    @scale_index.setter
    def scale_index(self, index):
        index = index % len(self._available_scales)
        self._scale_name = self._available_scales[index]
        self._scale_index = index

    def get_available_scales(self):
        """Return list of available scale names."""
        return self._available_scales

    def get_scale_display_name(self):
        """Return formatted scale name for display."""
        root_name = NOTE_NAMES[self.root_note % Music.NOTES_PER_OCTAVE]
        # MicroPython: no .title() method, capitalize first letter of each word manually
        scale_words = self._scale_name.replace("_", " ").split(" ")
        capitalized = []
        for word in scale_words:
            if len(word) > 0:
                capitalized.append(word[0].upper() + word[1:])
            else:
                capitalized.append(word)
        scale_display = " ".join(capitalized)
        return root_name + " " + scale_display

    def get_chord(self, degree):
        """
        Get MIDI notes for a diatonic chord.

        Args:
            degree: Scale degree 0-6 (I-VII)

        Returns:
            Tuple of (chord_notes, chord_name, roman_numeral)
            - chord_notes: list of MIDI note numbers
            - chord_name: e.g., "Cm", "Ddim"
            - roman_numeral: e.g., "ii", "vii°"
        """
        if not 0 <= degree <= 6:
            degree = degree % Music.SCALE_DEGREES

        scale = SCALES[self._scale_name]
        quality = get_chord_quality_in_scale(self._scale_name, degree)
        chord_intervals = CHORD_TYPES[quality]

        # Calculate root note for this degree
        chord_root = self.root_note + scale[degree]

        # Build chord notes
        chord_notes = [chord_root + interval for interval in chord_intervals]

        # Build chord name
        root_name = NOTE_NAMES[chord_root % Music.NOTES_PER_OCTAVE]
        suffixes = {
            "major": "",
            "minor": "m",
            "diminished": "dim",
            "augmented": "aug",
        }
        quality_suffix = suffixes.get(quality, "")
        chord_name = root_name + quality_suffix

        # Build roman numeral (uppercase for major, lowercase for minor/dim)
        numeral = ROMAN_NUMERALS[degree]
        if quality in ["minor", "diminished"]:
            numeral = numeral.lower()
        if quality == "diminished":
            numeral += "°"

        return (chord_notes, chord_name, numeral)

    def get_all_chords_in_scale(self):
        """Return info for all 7 diatonic chords."""
        return [self.get_chord(i) for i in range(Music.SCALE_DEGREES)]

    def get_scale_note(self, degree):
        """
        Get MIDI note number for a scale degree.
        Supports extended degrees beyond the 7-note scale (wraps with octaves).

        Args:
            degree: Scale degree 0-11 (or higher)
                    0 = root note
                    7 = root note + 1 octave
                    etc.

        Returns:
            MIDI note number
        """
        scale = SCALES[self._scale_name]
        octave_offset = degree // Music.SCALE_DEGREES
        scale_degree = degree % Music.SCALE_DEGREES
        return self.root_note + scale[scale_degree] + (octave_offset * Music.NOTES_PER_OCTAVE)

    def next_scale(self):
        """Cycle to next scale, return new scale name."""
        self.scale_index = (self._scale_index + 1) % len(self._available_scales)
        return self._scale_name

    def prev_scale(self):
        """Cycle to previous scale, return new scale name."""
        self.scale_index = (self._scale_index - 1) % len(self._available_scales)
        return self._scale_name

    def set_root_note_class(self, note_class):
        """Set the root note class (0-11, where 0=C, 1=C#, etc.)."""
        self._root_note_class = note_class % Music.NOTES_PER_OCTAVE
    
    def cycle_root_note(self, delta):
        """Cycle root note within the octave."""
        self._root_note_class = (self._root_note_class + delta) % Music.NOTES_PER_OCTAVE
    
    def set_octave(self, octave):
        """Set the octave (clamped to safe range)."""
        self._octave = max(Octave.MIN, min(Octave.MAX, octave))
    
    def change_octave(self, delta):
        """Change octave by delta steps."""
        new_octave = self._octave + delta
        self._octave = max(Octave.MIN, min(Octave.MAX, new_octave))
