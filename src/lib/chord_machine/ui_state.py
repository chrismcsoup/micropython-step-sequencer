"""
UI State management - platform independent.
Manages application state and provides event-driven architecture.
"""
from .constants import Mode


class Event:
    """Event type constants for state changes."""

    SCALE_CHANGED = "scale_changed"
    CHORD_TRIGGERED = "chord_triggered"
    CHORD_RELEASED = "chord_released"
    ENCODER_CHANGED = "encoder_changed"
    MODE_CHANGED = "mode_changed"
    ROOT_CHANGED = "root_changed"


class UIState:
    """
    Centralized UI state container.
    All UI-related state lives here, separate from business logic.
    """

    def __init__(self, chord_engine):
        """
        Args:
            chord_engine: ChordEngine instance for chord generation
        """
        self.chord_engine = chord_engine

        # Current state
        self.current_scale_index = chord_engine.scale_index
        self.active_chord_degree = None  # 0-6 or None
        self.encoder_value = 0
        self.mode = Mode.PLAY

        # Visual state
        self.led_states = [False] * 8  # 8 buttons worth of LED feedback
        self.display_dirty = True  # Flag to trigger display update

        # Event subscribers
        self._subscribers = {}

    def subscribe(self, event_type, callback):
        """
        Subscribe to an event type.

        Args:
            event_type: Event type constant from Event class
            callback: Function to call when event occurs, receives data dict
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type, callback):
        """Remove a callback from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    def emit(self, event_type, data=None):
        """Emit an event to all subscribers."""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(data)

    def set_scale(self, index):
        """Change the current scale."""
        self.current_scale_index = index
        self.chord_engine.scale_index = index
        self.display_dirty = True
        self.emit(
            Event.SCALE_CHANGED,
            {"index": index, "name": self.chord_engine.scale_name},
        )

    def trigger_chord(self, degree):
        """
        Trigger a chord (button pressed).

        Args:
            degree: Scale degree 0-6
        """
        self.active_chord_degree = degree
        self.led_states[degree] = True
        chord_notes, chord_name, numeral = self.chord_engine.get_chord(degree)
        self.display_dirty = True
        self.emit(
            Event.CHORD_TRIGGERED,
            {
                "degree": degree,
                "notes": chord_notes,
                "name": chord_name,
                "numeral": numeral,
            },
        )

    def release_chord(self, degree):
        """
        Release a chord (button released).

        Args:
            degree: Scale degree 0-6
        """
        if self.active_chord_degree == degree:
            self.active_chord_degree = None
        self.led_states[degree] = False
        self.emit(Event.CHORD_RELEASED, {"degree": degree})

    def update_encoder(self, delta):
        """
        Handle encoder rotation.

        Args:
            delta: Rotation amount (positive = clockwise)
        """
        self.encoder_value += delta
        self.emit(
            Event.ENCODER_CHANGED,
            {"value": self.encoder_value, "delta": delta},
        )

        # Behavior depends on current mode
        if self.mode == Mode.PLAY:
            # In play mode, encoder changes octave
            self.chord_engine.change_octave(delta)
            self.display_dirty = True
            self.emit(
                Event.ROOT_CHANGED,
                {"root_note": self.chord_engine.root_note,
                 "root_note_class": self.chord_engine.root_note_class,
                 "octave": self.chord_engine.octave},
            )

        elif self.mode == Mode.ROOT_SELECT:
            # In root select mode, encoder cycles through note names (C, C#, D, etc.)
            self.chord_engine.cycle_root_note(delta)
            self.display_dirty = True
            self.emit(
                Event.ROOT_CHANGED,
                {"root_note": self.chord_engine.root_note,
                 "root_note_class": self.chord_engine.root_note_class,
                 "octave": self.chord_engine.octave},
            )
        
        elif self.mode == Mode.SCALE_SELECT:
            # In scale select mode, encoder changes scale
            if delta > 0:
                self.chord_engine.next_scale()
            else:
                self.chord_engine.prev_scale()
            self.set_scale(self.chord_engine.scale_index)

    def toggle_mode(self):
        """Toggle between play, root_select, and scale_select modes."""
        current_idx = Mode.ALL.index(self.mode)
        self.mode = Mode.ALL[(current_idx + 1) % len(Mode.ALL)]
        self.display_dirty = True
        self.emit(Event.MODE_CHANGED, {"mode": self.mode})

    def set_mode(self, mode):
        """Set a specific mode."""
        if mode in Mode.ALL:
            self.mode = mode
            self.display_dirty = True
            self.emit(Event.MODE_CHANGED, {"mode": self.mode})

    def get_display_data(self):
        """
        Get data needed for display rendering.

        Returns:
            Dict with display information
        """
        chord_info = None
        if self.active_chord_degree is not None:
            _, name, numeral = self.chord_engine.get_chord(self.active_chord_degree)
            chord_info = {"name": name, "numeral": numeral}

        return {
            "scale_name": self.chord_engine.get_scale_display_name(),
            "active_chord": chord_info,
            "mode": self.mode,
            "root_note": self.chord_engine.root_note,
            "root_note_class": self.chord_engine.root_note_class,
            "octave": self.chord_engine.octave,
        }

    def clear_display_dirty(self):
        """Mark display as updated."""
        self.display_dirty = False
