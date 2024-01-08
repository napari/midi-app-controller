import napari
import numpy as np
import rtmidi, time
import threading
from napari._app_model._app import get_app
from napari._app_model.constants._commands import CommandId

def on_midi_message(message, timestamp):
    get_app().commands.execute_command(CommandId.TOGGLE_FULLSCREEN)

def midi_thread():
    min = rtmidi.MidiIn()
    ports = min.get_ports()
    min.open_port(1)
    min.set_callback(on_midi_message)

    print("Waiting for MIDI messages...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        # Close the MIDI input port
        thread.join()
        min.close_port()
        print("MIDI input port closed.")


thread = threading.Thread(target=midi_thread)
thread.start()

# Create some example image data
image_data = np.random.random((10, 512, 512))
# Create a Napari viewer
viewer = napari.view_image(image_data)
# Run the Napari GUI
napari.run()

thread.join()



