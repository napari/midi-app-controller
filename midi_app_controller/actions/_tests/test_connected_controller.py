import rtmidi

midi_in = rtmidi.MidiIn()
midi_out = rtmidi.MidiOut()

# Listing available MIDI ports
available_ports_in = midi_in.get_ports()
available_ports_out = midi_out.get_ports()

available_ports = [port \
    for port in available_ports_in \
    if port in available_ports_out]

if available_ports:
    for i, port in enumerate(available_ports):
        name = port.split(":")[0]
        print(i)
else:
    raise IOError("No MIDI input ports available.")