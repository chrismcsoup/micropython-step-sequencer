# Testing the midi input functionality of the TRS Type-A Midi perfboard

from machine import Pin, UART
from lib.midi import Midi, MIDI_SEQUENCE

# Raw UART test - no inversion worked better
MIDI_TX = Pin(39)
MIDI_RX = Pin(40)

UART_1 = 1
my_midi = Midi(UART_1, tx=MIDI_TX, rx=MIDI_RX)

print("MIDI Input Test - Waiting for MIDI messages...")

while True:
    if my_midi.any() > 0:
        raw_byte = my_midi.read(1)
        print("RX: {:02X}".format(raw_byte[0]), end=" ")
        
        my_midi.load_message(raw_byte)
        
        if my_midi.last_sequence == MIDI_SEQUENCE["NOTE_ON"]:
            channel = my_midi.channel
            note = my_midi.get_parameter("note_on", "note")
            velocity = my_midi.get_parameter("note_on", "velocity")
            print()  # newline after hex bytes
            print("  -> NOTE_ON  ch={} note={} vel={}".format(channel, note, velocity))

        elif my_midi.last_sequence == MIDI_SEQUENCE["NOTE_OFF"]:
            channel = my_midi.channel
            note = my_midi.get_parameter("note_off", "note")
            print()  # newline after hex bytes
            print("  -> NOTE_OFF ch={} note={}".format(channel, note))

        elif my_midi.last_sequence == MIDI_SEQUENCE.get("CONTROL_CHANGE"):
            channel = my_midi.channel
            cc = my_midi.get_parameter("control_change", "control")
            value = my_midi.get_parameter("control_change", "value")
            print()
            print("  -> CC       ch={} cc={} val={}".format(channel, cc, value))

        elif my_midi.last_sequence == MIDI_SEQUENCE.get("PROGRAM_CHANGE"):
            channel = my_midi.channel
            program = my_midi.get_parameter("program_change", "program")
            print()
            print("  -> PC       ch={} prog={}".format(channel, program))