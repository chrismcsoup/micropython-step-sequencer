"""
Unit tests for the Chord Machine business logic.
These tests run on both CPython and MicroPython as they test pure logic.

Run with: python test/test_chord_machine.py
     or: micropython test/test_chord_machine.py
"""
import sys

# Add the src/lib path for imports (works on both CPython and MicroPython)
sys.path.insert(0, "src/lib")

try:
    from chord_machine.music_theory import (
        SCALES,
        NOTE_NAMES,
        get_scale_names,
        get_chord_quality_in_scale,
        note_name,
    )
    from chord_machine.chord_engine import ChordEngine
    from chord_machine.ui_state import UIState, Event
except ImportError:
    # Try relative import for running from project root
    sys.path.insert(0, "../src/lib")
    from chord_machine.music_theory import (
        SCALES,
        NOTE_NAMES,
        get_scale_names,
        get_chord_quality_in_scale,
        note_name,
    )
    from chord_machine.chord_engine import ChordEngine
    from chord_machine.ui_state import UIState, Event


class TestMusicTheory:
    """Tests for music theory calculations."""

    def test_note_names(self):
        """Test MIDI note to name conversion."""
        assert note_name(60) == "C"  # C4
        assert note_name(61) == "C#"
        assert note_name(62) == "D"
        assert note_name(72) == "C"  # C5 (octave up)
        assert note_name(69) == "A"  # A4 (440Hz)

    def test_scale_names_available(self):
        """Test that we have expected scales."""
        scales = get_scale_names()
        assert "major" in scales
        assert "natural_minor" in scales
        assert "dorian" in scales
        assert len(scales) >= 7

    def test_major_scale_chord_qualities(self):
        """Test chord qualities in C major scale."""
        # C major: C Dm Em F G Am Bdim
        expected = ["major", "minor", "minor", "major", "major", "minor", "diminished"]
        for degree in range(len(expected)):
            expected_quality = expected[degree]
            quality = get_chord_quality_in_scale("major", degree)
            assert quality == expected_quality, "Degree " + str(degree) + ": expected " + expected_quality + ", got " + quality

    def test_minor_scale_chord_qualities(self):
        """Test chord qualities in natural minor scale."""
        # A minor: Am Bdim C Dm Em F G
        expected = ["minor", "diminished", "major", "minor", "minor", "major", "major"]
        for degree in range(len(expected)):
            expected_quality = expected[degree]
            quality = get_chord_quality_in_scale("natural_minor", degree)
            assert quality == expected_quality, "Degree " + str(degree) + ": expected " + expected_quality + ", got " + quality


class TestChordEngine:
    """Tests for chord generation."""

    def test_c_major_chord_i(self):
        """Test C major chord (I)."""
        engine = ChordEngine(root_note=60, scale_name="major")
        notes, name, numeral = engine.get_chord(0)
        assert notes == [60, 64, 67], "Expected C-E-G (60,64,67), got " + str(notes)
        assert name == "C"
        assert numeral == "I"

    def test_c_major_chord_ii(self):
        """Test D minor chord (ii) in C major."""
        engine = ChordEngine(root_note=60, scale_name="major")
        notes, name, numeral = engine.get_chord(1)
        assert notes == [62, 65, 69], "Expected D-F-A (62,65,69), got " + str(notes)
        assert name == "Dm"
        assert numeral == "ii"

    def test_c_major_chord_vii(self):
        """Test B diminished chord (vii°) in C major."""
        engine = ChordEngine(root_note=60, scale_name="major")
        notes, name, numeral = engine.get_chord(6)
        assert notes == [71, 74, 77], "Expected B-D-F (71,74,77), got " + str(notes)
        assert name == "Bdim"
        assert numeral == "vii°"

    def test_scale_cycling(self):
        """Test cycling through scales."""
        engine = ChordEngine(root_note=60, scale_name="major")
        initial = engine.scale_name
        
        # Cycle forward through all scales
        scale_count = len(engine.get_available_scales())
        for _ in range(scale_count):
            engine.next_scale()
        
        # Should be back to initial
        assert engine.scale_name == initial

    def test_scale_cycling_backwards(self):
        """Test reverse scale cycling."""
        engine = ChordEngine(root_note=60, scale_name="major")
        
        engine.prev_scale()
        assert engine.scale_name != "major"
        
        engine.next_scale()
        assert engine.scale_name == "major"

    def test_display_name(self):
        """Test scale display name formatting."""
        engine = ChordEngine(root_note=60, scale_name="major")
        assert engine.get_scale_display_name() == "C Major"
        
        engine.scale_name = "natural_minor"
        assert engine.get_scale_display_name() == "C Natural Minor"

    def test_transpose(self):
        """Test octave transposition."""
        engine = ChordEngine(root_note=60, scale_name="major")  # C4
        engine.change_octave(1)  # Up one octave
        assert engine.root_note == 72  # C5
        
        engine.change_octave(-2)  # Down two octaves
        assert engine.root_note == 48  # C3

    def test_all_chords_in_scale(self):
        """Test getting all 7 diatonic chords."""
        engine = ChordEngine(root_note=60, scale_name="major")
        chords = engine.get_all_chords_in_scale()
        assert len(chords) == 7
        
        # Verify structure
        for notes, name, numeral in chords:
            assert len(notes) == 3  # Triads
            assert isinstance(name, str)
            assert isinstance(numeral, str)


class TestUIState:
    """Tests for UI state management."""

    def test_event_subscription(self):
        """Test event subscription and emission."""
        engine = ChordEngine()
        state = UIState(engine)
        
        received_events = []
        
        def handler(data):
            received_events.append(data)
        
        state.subscribe(Event.SCALE_CHANGED, handler)
        state.set_scale(2)
        
        assert len(received_events) == 1
        assert "index" in received_events[0]

    def test_chord_trigger_and_release(self):
        """Test chord triggering and releasing."""
        engine = ChordEngine()
        state = UIState(engine)
        
        triggered = []
        released = []
        
        state.subscribe(Event.CHORD_TRIGGERED, lambda d: triggered.append(d))
        state.subscribe(Event.CHORD_RELEASED, lambda d: released.append(d))
        
        state.trigger_chord(3)
        assert len(triggered) == 1
        assert triggered[0]["degree"] == 3
        assert state.active_chord_degree == 3
        
        state.release_chord(3)
        assert len(released) == 1
        assert state.active_chord_degree is None

    def test_mode_cycling(self):
        """Test mode toggle."""
        engine = ChordEngine()
        state = UIState(engine)
        
        assert state.mode == "play"
        
        state.toggle_mode()
        assert state.mode == "root_select"
        
        state.toggle_mode()
        assert state.mode == "scale_select"
        
        state.toggle_mode()
        assert state.mode == "play"

    def test_display_data(self):
        """Test display data generation."""
        engine = ChordEngine(root_note=60, scale_name="major")
        state = UIState(engine)
        
        data = state.get_display_data()
        assert "scale_name" in data
        assert "active_chord" in data
        assert "mode" in data
        assert data["active_chord"] is None  # No chord playing
        
        state.trigger_chord(0)
        data = state.get_display_data()
        assert data["active_chord"] is not None
        assert data["active_chord"]["name"] == "C"


def run_tests():
    """Run all tests and report results."""
    test_classes = [TestMusicTheory, TestChordEngine, TestUIState]
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        instance = test_class()
        print("")
        print(test_class.__name__)
        print("-" * 40)
        
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    method = getattr(instance, method_name)
                    method()
                    print("  [OK] " + method_name)
                    passed += 1
                except AssertionError as e:
                    print("  [FAIL] " + method_name + ": " + str(e))
                    failed += 1
                except Exception as e:
                    print("  [ERROR] " + method_name + ": " + str(e))
                    failed += 1
    
    print("")
    print("=" * 40)
    print("Results: " + str(passed) + " passed, " + str(failed) + " failed")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
