from machine import Pin
import time


class Button:
    def __init__(
        self,
        pin,
        *,
        pull=Pin.PULL_UP,
        debounce_ms=30,
        long_press_ms=600,
    ):
        # Support both direct pin numbers (ESP32) and pin objects (MCP23017)
        if isinstance(pin, int):
            # Direct ESP32 pin - create a Pin object
            self.pin = Pin(pin, Pin.IN, pull)
        else:
            # Pin-like object (e.g., MCP23017 VirtualPin)
            # Assume it's already configured externally
            self.pin = pin

        self.debounce_ms = debounce_ms
        self.long_press_ms = long_press_ms

        self._last_raw = self.pin.value()
        self._stable = self._last_raw
        self._last_change = time.ticks_ms()

        self._pressed_time = None

        self._pressed_event = False
        self._released_event = False
        self._long_press_event = False

    def update(self):
        """Call this frequently (e.g. every loop iteration)."""
        now = time.ticks_ms()
        raw = self.pin.value()

        # Debounce
        if raw != self._last_raw:
            self._last_change = now
            self._last_raw = raw

        if time.ticks_diff(now, self._last_change) >= self.debounce_ms:
            if raw != self._stable:
                self._stable = raw

                if self.is_pressed():
                    self._pressed_event = True
                    self._pressed_time = now
                else:
                    self._released_event = True
                    self._pressed_time = None

        # Long press detection
        if self.is_pressed() and self._pressed_time is not None:
            if time.ticks_diff(now, self._pressed_time) >= self.long_press_ms:
                self._long_press_event = True
                self._pressed_time = None  # fire once

    # ---- state helpers ----

    def is_pressed(self):
        """True while button is physically pressed."""
        return self._stable == 0  # pull-up logic

    def was_pressed(self):
        """True once when button becomes pressed."""
        if self._pressed_event:
            self._pressed_event = False
            return True
        return False

    def was_released(self):
        """True once when button is released."""
        if self._released_event:
            self._released_event = False
            return True
        return False

    def was_long_pressed(self):
        """True once when long-press threshold is reached."""
        if self._long_press_event:
            self._long_press_event = False
            return True
        return False
