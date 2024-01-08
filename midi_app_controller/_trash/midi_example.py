import rtmidi
import time

def on_midi_message(message, timestamp):
    status_byte = message[0][0]
    command = (status_byte & 0xF0) / 0x10
    channel = (status_byte & 0x0F) + 1  # Extract channel (1-16)
    data_bytes = message[0][1:]

    print(f"Command: {command}, Channel: {channel}, Data: {data_bytes}")


midi_in = rtmidi.MidiIn()

port_count = midi_in.get_port_count()
for i in range(port_count):
    print(f"Port {i}: {midi_in.get_port_name(i)}")

midi_in.open_port(1)

midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()

if available_ports:
    midiout.open_port(1)

# note_on = [0xB0, 127, 1]
# note_off = [0xB0, 127, 0]
# midiout.send_message(note_on)
# time.sleep(0.5)

midi_in.set_callback(on_midi_message)

# Wait for MIDI messages to be received (replace with your own logic)
print("Waiting for MIDI messages...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    # Close the MIDI input port
    midi_in.close_port()
    print("MIDI input port closed.")
