import time
import rtmidi

def on_midi_message(message, timestamp):
    status_byte = message[0][0]
    command = (status_byte & 0xF0) / 0x10
    channel = (status_byte & 0x0F) + 1  # Extract channel (1-16)
    data_bytes = message[0][1:]

    print(f"Command: {command}, Channel: {channel}, Data: {data_bytes}")


midiout = rtmidi.MidiOut()
midiin = rtmidi.MidiIn()
available_ports = midiout.get_ports()

if available_ports:
    midiout.open_port(1)
    midiin.open_port(1)
    midiin.set_callback(on_midi_message)
else:
    print("Error")

with midiout:
    #note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112
    #note_off = [0x80, 60, 0]

    mc_mode_on = [0xB0, 127, 1]
    mc_mode_off = [0xB0, 127, 0]

    mc_knob_single = [0xB0, 1, 0] 
    mc_knob_on = [0xB0, 9, 27]
    mc_knob_off = [0xB0, 9, 12]

    knob_change_value = [0xBA, 1, 1]
    button_change_value = [0x9A, 8, 127]

    note_on = [0x90, 0, 1]
    note_off = [0x80, 0, 0]

    midiout.send_message(button_change_value)
    time.sleep(0.5)
    midiout.send_message(knob_change_value)
    time.sleep(0.5)
    print("done")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        # Close the MIDI input port
        midiin.close_port()
        midiout.close_port()

del midiout