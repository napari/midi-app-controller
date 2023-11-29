import rtmidi.midiutil
from superqt.utils import ensure_main_thread
from napari._app_model._app import get_app
from napari._app_model.constants._commands import CommandId


class MidiController:
    """A simple MIDI controller handler that executes `command_id` on any button press."""

    def __init__(self, command_id):
        self.command_id = command_id
        self.midi_in, _ = rtmidi.midiutil.open_midiinput(0)
        self.midi_in.set_callback(self.receive)

    @ensure_main_thread
    def receive(self, message, time):
        """Execute `command_id` if a button was pressed."""
        if message[0] == 154:
            get_app().commands.execute_command(self.command_id)


controller = MidiController(CommandId.TOGGLE_MENUBAR)


def activate_controller():
    """Just makes sure that the `controller` object above was initialized."""
    pass


def toggle_viewer_scale_bar():
    """An example showing how to execute commands."""
    command_id = CommandId.TOGGLE_VIEWER_SCALE_BAR

    # It is necessary to use `execute_command` to execute commands as it
    # automatically injects missing arguments into the callback function.
    get_app().commands.execute_command(command_id)
