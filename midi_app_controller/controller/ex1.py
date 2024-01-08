
import rtmidi

class MyMidiHandler:
    def __init__(self):
        # Create an instance of MidiIn as an attribute
        self.midi_in = rtmidi.MidiIn()

    def set_callback(self, callback_function):
        # Set the callback function
        self.midi_in.set_callback(callback_function)

# Define a callback function outside of the class
def my_callback(message, time_stamp):
    print(f"Received MIDI message: {message} at time {time_stamp}")

# Create an instance of MyMidiHandler
my_handler = MyMidiHandler()

# Set the callback function using set_callback()
my_handler.set_callback(my_callback)

# Start the MIDI input (you may need additional setup here)
my_handler.midi_in.open_port(1)

# Wait for MIDI input events (you may need a loop or event handling)
# Here, we'll just sleep to keep the program running
import time
time.sleep(10)

# Close the MIDI input when done
my_handler.midi_in.close_port()