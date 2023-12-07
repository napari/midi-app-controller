import rtmidi
import time

def on_midi_message(message, timestamp):
    status_byte = message[0][0]
    channel = (status_byte & 0x0F) + 1  # Extract channel (1-16)
    data_bytes = message[0][1:]

    print(f"Status: {status_byte}, Channel: {channel}, Data: {data_bytes}")


min = rtmidi.MidiIn()

ports = min.get_ports()

print(ports)

min.open_port(1)

min.set_callback(on_midi_message)

# Wait for MIDI messages to be received (replace with your own logic)
print("Waiting for MIDI messages...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    # Close the MIDI input port
    min.close_port()
    print("MIDI input port closed.")
