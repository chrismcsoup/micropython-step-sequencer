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
    from chord_machine.constants import Mode
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
    from chord_machine.constants import Mode


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

    def test_get_scale_note_root(self):
        """Test getting root note from scale."""
        engine = ChordEngine(root_note=60, scale_name="major")
        # Pad 0 should be root note (C4 = 60)
        assert engine.get_scale_note(0) == 60

    def test_get_scale_note_degrees(self):
        """Test getting scale notes for all degrees in C major."""
        engine = ChordEngine(root_note=60, scale_name="major")
        # C major scale: C D E F G A B
        expected = [60, 62, 64, 65, 67, 69, 71]
        for degree in range(7):
            note = engine.get_scale_note(degree)
            assert note == expected[degree], "Degree " + str(degree) + ": expected " + str(expected[degree]) + ", got " + str(note)

    def test_get_scale_note_extended_degrees(self):
        """Test scale notes wrap to next octave for degrees 7-11."""
        engine = ChordEngine(root_note=60, scale_name="major")
        # Degrees 7-11 should wrap to next octave
        # Degree 7 = root + octave = 72
        assert engine.get_scale_note(7) == 72  # C5
        assert engine.get_scale_note(8) == 74  # D5
        assert engine.get_scale_note(9) == 76  # E5

    def test_get_scale_note_minor(self):
        """Test scale notes in natural minor."""
        engine = ChordEngine(root_note=60, scale_name="natural_minor")
        # C natural minor: C D Eb F G Ab Bb
        expected = [60, 62, 63, 65, 67, 68, 70]
        for degree in range(7):
            note = engine.get_scale_note(degree)
            assert note == expected[degree], "Degree " + str(degree) + ": expected " + str(expected[degree]) + ", got " + str(note)


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
        
        assert state.mode == Mode.PLAY
        
        state.toggle_mode()
        assert state.mode == Mode.ROOT_SELECT
        
        state.toggle_mode()
        assert state.mode == Mode.SCALE_SELECT
        
        state.toggle_mode()
        assert state.mode == Mode.PLAY

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

    def test_note_trigger_and_release(self):
        """Test touch strip note triggering and releasing."""
        engine = ChordEngine(root_note=60, scale_name="major")
        state = UIState(engine)
        
        triggered = []
        released = []
        
        state.subscribe(Event.NOTE_TRIGGERED, lambda d: triggered.append(d))
        state.subscribe(Event.NOTE_RELEASED, lambda d: released.append(d))
        
        # Trigger pad 0 (root note)
        state.trigger_note(0)
        assert len(triggered) == 1
        assert triggered[0]["pad"] == 0
        assert triggered[0]["note"] == 60  # C4
        assert triggered[0]["name"] == "C"
        
        # Release pad 0
        state.release_note(0)
        assert len(released) == 1
        assert released[0]["pad"] == 0
        assert released[0]["note"] == 60

    def test_note_trigger_different_pads(self):
        """Test triggering different touch pads."""
        engine = ChordEngine(root_note=60, scale_name="major")
        state = UIState(engine)
        
        notes = []
        state.subscribe(Event.NOTE_TRIGGERED, lambda d: notes.append(d["note"]))
        
        # Trigger pads 0, 2, 4 (C major triad: C, E, G)
        state.trigger_note(0)
        state.trigger_note(2)
        state.trigger_note(4)
        
        assert notes == [60, 64, 67]  # C, E, G

    def test_note_trigger_extended_range(self):
        """Test touch pads in extended range (7-11)."""
        engine = ChordEngine(root_note=60, scale_name="major")
        state = UIState(engine)
        
        notes = []
        state.subscribe(Event.NOTE_TRIGGERED, lambda d: notes.append(d["note"]))
        
        # Trigger pad 7 (octave above root)
        state.trigger_note(7)
        assert notes[0] == 72  # C5

    def test_chord_hold_toggle(self):
        """Test toggling chord hold mode."""
        engine = ChordEngine(root_note=60, scale_name="major")
        state = UIState(engine)
        
        assert state.chord_hold == False
        
        hold_events = []
        state.subscribe(Event.CHORD_HOLD_CHANGED, lambda d: hold_events.append(d))
        
        state.toggle_chord_hold()
        assert state.chord_hold == True
        assert len(hold_events) == 1
        assert hold_events[0]["chord_hold"] == True
        
        state.toggle_chord_hold()
        assert state.chord_hold == False

    def test_chord_hold_keeps_chord_on_release(self):
        """Test that chord stays held when button is released in hold mode."""
        engine = ChordEngine(root_note=60, scale_name="major")
        state = UIState(engine)
        
        released = []
        state.subscribe(Event.CHORD_RELEASED, lambda d: released.append(d))
        
        # Enable chord hold
        state.toggle_chord_hold()
        
        # Trigger and release chord
        state.trigger_chord(0)
        state.release_chord(0)
        
        # Should NOT have released the chord
        assert len(released) == 0
        assert state.held_chord_degree == 0

    def test_chord_hold_switches_chords(self):
        """Test that pressing new chord releases previous in hold mode."""
        engine = ChordEngine(root_note=60, scale_name="major")
        state = UIState(engine)
        
        triggered = []
        released = []
        state.subscribe(Event.CHORD_TRIGGERED, lambda d: triggered.append(d["degree"]))
        state.subscribe(Event.CHORD_RELEASED, lambda d: released.append(d["degree"]))
        
        # Enable chord hold
        state.toggle_chord_hold()
        
        # Trigger first chord
        state.trigger_chord(0)
        assert triggered == [0]
        assert released == []
        
        # Trigger second chord - should release first
        state.trigger_chord(2)
        assert triggered == [0, 2]
        assert released == [0]
        assert state.held_chord_degree == 2

    def test_chord_hold_deactivate_releases(self):
        """Test that deactivating hold mode releases held chord."""
        engine = ChordEngine(root_note=60, scale_name="major")
        state = UIState(engine)
        
        released = []
        state.subscribe(Event.CHORD_RELEASED, lambda d: released.append(d["degree"]))
        
        # Enable chord hold and trigger chord
        state.toggle_chord_hold()
        state.trigger_chord(3)
        state.release_chord(3)  # Button release, but chord stays held
        
        assert len(released) == 0
        
        # Disable chord hold - should release the held chord
        state.toggle_chord_hold()
        
        assert len(released) == 1
        assert released[0] == 3
        assert state.held_chord_degree is None

    def test_display_data_includes_chord_hold(self):
        """Test that display data includes chord hold state."""
        engine = ChordEngine(root_note=60, scale_name="major")
        state = UIState(engine)
        
        data = state.get_display_data()
        assert "chord_hold" in data
        assert data["chord_hold"] == False
        
        state.toggle_chord_hold()
        data = state.get_display_data()
        assert data["chord_hold"] == True


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
