from typing import List
from pathlib import Path

import rtmidi
from app_model import Application
from app_model.types import Action

from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller
from midi_app_controller.actions.bound_controller import BoundController
from midi_app_controller.actions.actions_handler import ActionsHandler
from midi_app_controller.controller.connected_controller import ConnectedController
from midi_app_controller.config import Config


class SelectedItem:
    """Info about an item (controller or binds) backed by a file.

    Attributes
    ----------
    name : str
        Display name of the item.
    path: Path
        Path to the file containing the real data.
    """

    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path


# TODO Add info about possible exceptions to docstrings of methods.
class StateManager:
    """Stores the state of the app (like selected controller, ports etc.) and
    allows to update it.

    Attributes
    ----------
    selected_controller : Optional[SelectedItem]
        Currently selected schema of a controller.
    selected_binds : Optional[SelectedItem]
        Currently selected binds set.
    selected_midi_in : Optional[str]
        Name of currently selected MIDI input.
    selected_midi_out : Optional[str]
        Name of currently selected MIDI output.
    actions : List[Action]
        List of app_model actions that are available in the app.
    _app_name : str
        Name of the app we want to handle. Used to filter binds files.
    _app : Application
        Used to execute actions.
    connected_controller : ConnectedController
        Object that handles MIDI input and output.
    _midi_in : rtmidi.MidiIn
        MIDI input client interface.
    _midi_out : rtmidi.MidiOut
        MIDI output client interface.
    """

    def __init__(self, actions: List[Action], app: Application):
        self.selected_controller = None
        self.selected_binds = None
        self.selected_midi_in = None
        self.selected_midi_out = None
        self.actions = actions
        self._app_name = app.name
        self._app = app
        self.connected_controller = None
        self._midi_in = rtmidi.MidiIn()
        self._midi_out = rtmidi.MidiOut()

    def is_running(self) -> bool:
        """Checks if any controller is being handled now."""
        return self.connected_controller is not None

    def get_available_binds(self) -> List[str]:
        """Returns names of all binds sets suitable for current controller and app."""
        # TODO Extract the loading logic to a separate file that will handle storage.
        if self.selected_controller is None:
            return []
        all_binds = Binds.load_all_from(Config.BINDS_DIRECTORY)
        return [
            b.name
            for b, _ in all_binds
            if b.app_name == self._app_name
            and b.controller_name == self.selected_controller.name
        ]

    def get_available_controllers(self) -> List[str]:
        """Returns names of all controller schemas."""
        # TODO Extract the loading logic to a separate file that will handle storage.
        controllers = Controller.load_all_from(Config.CONTROLLERS_DIRECTORY)
        return [c.name for c, _ in controllers]

    def get_available_midi_in(self) -> List[str]:
        """Returns names of all MIDI input ports."""
        return self._midi_in.get_ports()

    def get_available_midi_out(self) -> List[str]:
        """Returns names of all MIDI output ports."""
        return self._midi_out.get_ports()

    def select_binds(self, name: str) -> None:
        """Updates currently selected binds.

        Does not have any immediate effect except updating the value and
        finding path to the config file.
        """
        all_binds = Binds.load_all_from(Config.BINDS_DIRECTORY)
        for binds, path in all_binds:
            if binds.name == name:
                self.selected_binds = SelectedItem(name, path)
                return
        raise Exception("Config file of selected binds not found.")

    def select_controller(self, name: str) -> None:
        """Updates currently selected controller schema.

        Does not have any immediate effect except updating the value and
        finding path to the config file.
        """
        all_controllers = Controller.load_all_from(Config.CONTROLLERS_DIRECTORY)
        for controller, path in all_controllers:
            if controller.name == name:
                self.selected_controller = SelectedItem(name, path)
                return
        raise Exception("Config file of selected controller not found.")

    def select_midi_in(self, name: str) -> None:
        """Updates currently selected MIDI input port name.

        Does not have any immediate effect except updating the value.
        """
        self.selected_midi_in = name

    def select_midi_out(self, name: str) -> None:
        """Updates currently selected MIDI output port name.

        Does not have any immediate effect except updating the value.
        """
        self.selected_midi_out = name

    def stop_handling(self) -> None:
        """Stops handling any MIDI signals."""
        self._midi_in.cancel_callback()
        self.connected_controller = None
        self._midi_in.close_port()
        self._midi_out.close_port()

    def start_handling(self) -> None:
        """Starts handling MIDI input using current values of binds, controller, etc.

        Stops previous handler first. If any error occurs in this method, the
        previous handler will NOT be restored.
        """
        self.stop_handling()

        # Check if all required field are not None.
        if self.selected_controller is None:
            raise Exception("No controller was selected.")
        if self.selected_binds is None:
            raise Exception("No binds were selected.")
        if self.selected_midi_in is None:
            raise Exception("No midi in port was selected.")
        if self.selected_midi_out is None:
            raise Exception("No midi out port was selected.")

        # Find MIDI port numbers corresponding to selected names.
        midi_in_port = self._midi_in.get_ports().index(self.selected_midi_in)
        midi_out_port = self._midi_out.get_ports().index(self.selected_midi_out)

        # Load binds and controller from disk.
        binds = Binds.load_from(self.selected_binds.path)
        controller = Controller.load_from(self.selected_controller.path)

        # Validate the data.
        bound_controller = BoundController.create(
            binds=binds,
            controller=controller,
            actions=self.actions,
        )
        actions_handler = ActionsHandler(
            bound_controller=bound_controller, app=self._app
        )

        # Open ports.
        self._midi_in.open_port(midi_in_port)
        self._midi_out.open_port(midi_out_port)

        # Start handling MIDI messages.
        self.connected_controller = ConnectedController(
            actions_handler=actions_handler,
            controller=controller,
            midi_in=self._midi_in,
            midi_out=self._midi_out,
        )
