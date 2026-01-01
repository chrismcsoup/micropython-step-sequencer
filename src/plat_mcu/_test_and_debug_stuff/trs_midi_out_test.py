# This is a midi trs A test based on this blog post: https://barbarach.com/midi-control-pedal-the-beginning/
# We are using the micropython-midi-library from sensai7 https://github.com/sensai7/Micropython-midi-library


from machine import Pin
from utime import sleep
from lib.midi import Midi, CHANNEL, NOTE_CODE, CONTROL_CHANGE_CODE


MIDI_TX = Pin(39)             # MIDI output in general purpose pin
MIDI_RX = Pin(40)             # MIDI input in general purpose pin
UART_1 = 1
my_midi = Midi(UART_1, tx=MIDI_TX, rx=MIDI_RX)

START_NOTE= 60 # C4
note = START_NOTE

while True:
    try:
        my_midi.send_note_on(CHANNEL[1], note , velocity=100) # type: ignore
        my_midi.send_note_off(CHANNEL[1], note) # type: ignore
        my_midi.send_control_change(CHANNEL[1], CONTROL_CHANGE_CODE["MODULATION_WHEEL"], value=80) # type: ignore

        # increase note every loop
        note += 1
        if note >= 90: 
            note = START_NOTE
        sleep(1)
    except KeyboardInterrupt:
        break
print("Finished.")