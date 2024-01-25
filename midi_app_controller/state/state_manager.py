from typing import List
from pathlib import Path

import rtmidi
from app_model import Application
from app_model.types import Action

from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller
from midi_app_controller.actions.bound_controller import BoundController
from midi_app_controller.actions.action_handler import ActionsHandler
from midi_app_controller.controller.connected_controller import ConnectedController
from midi_app_controller.config import Config


# TODO Add info about possible exceptions to docstrings of methods.
class StateManager:
    """Class that stores the app state and allows to update it.

    Attributes
    ----------
    selected_controller_name : str
        Name of the controller in currently selected schema. None if there
        is no schema selected.
    selected_binds_name : str
        Name of currently selected binds set. None if there are no
        binds selected.
    selected_midi_in : str
        Name of currently selected MIDI input. None if it is not selected.
    selected_midi_out : str
        Name of currently selected MIDI output. None if it is not selected.
    _app_name : str
        Name of the app we want to handle. Used to filter binds files.
    _actions : List[Action]
        List of app_model actions that are available in the app.
    _app : Application
        Used to execute actions.
    _connected_controller : ConnectedController
        Object that handles MIDI input and output.
    _midi_in : rtmidi.MidiIn
        MIDI input client interface.
    _midi_out : rtmidi.MidiOut
        MIDI output client interface.
    """

    def __init__(self, app_name: str, actions: List[Action], app: Application):
        self.selected_controller_name = None
        self.selected_binds_name = None
        self.selected_midi_in = None
        self.selected_midi_out = None
        self._app_name = app_name
        self._actions = actions
        self._app = app
        self._connected_controller = None
        self._midi_in = rtmidi.MidiIn()
        self._midi_out = rtmidi.MidiOut()

    def get_available_binds(self) -> List[str]:
        """Returns names of all binds sets suitable for current controller and app."""
        all_binds = Binds.load_all_from(Config.BINDS_DIRECTORY)
        names = [
            b.name
            for b, _ in all_binds
            if b.app_name == self._app_name
            and b.controller_name == self.selected_controller_name
        ]
        return names

    def get_available_controllers(self) -> List[str]:
        """Returns names of all controller schemas."""
        controllers = Controller.load_all_from(Config.CONTROLLERS_DIRECTORY)
        names = [c.name for c, _ in controllers]
        return names

    def get_available_midi_in(self) -> List[str]:
        """Returns names of all MIDI input ports."""
        return self._midi_in.get_ports()

    def get_available_midi_out(self) -> List[str]:
        """Returns names of all MIDI output ports."""
        return self._midi_out.get_ports()

    def select_binds(self, name: str) -> None:
        """Updates currently selected binds.

        Does not have any immediate effect except updating the value.
        """
        self.selected_binds_name = name

    def select_controller(self, name: str) -> None:
        """Updates currently selected controller schema.

        Does not have any immediate effect except updating the value.
        """
        self.selected_controller_name = name

    def select_midi_in(self, name: str) -> None:
        """Updates currently selected MIDI input port name.

        Does not have any immediate effect except updating the value.
        """
        self.selected_midi_in = name

    def select_midi_out(self, name: str) -> None:
        """Updates currently selected MIDI output port name.

        Does not have any immediate effect except updating the value.
        """
        self.selected_midi_in = name

    def get_selected_binds_path(self) -> Path:
        """Returns path to configuration file of currently selected binds."""
        all_binds = Binds.load_all_from(Config.BINDS_DIRECTORY)
        for binds, path in all_binds:
            if binds.name == self.selected_binds_name:
                return path
        raise Exception("Config file of selected binds not found.")

    def get_selected_controller_path(self) -> Path:
        """Returns path to configuration file of currently selected controller."""
        all_controllers = Controller.load_all_from(Config.CONTROLLERS_DIRECTORY)
        for controller, path in all_controllers:
            if controller.name == self.selected_controller_name:
                return path
        raise Exception("Config file of selected controller not found.")

    def stop_handling(self) -> None:
        """Stops handling any MIDI signals."""
        self._midi_in.cancel_callback()
        self._midi_out.cancel_callback()
        # TODO Stop threads started by controller (there are not any yet but probably will be).
        self._connected_controller = None
        self._midi_in.close_port()
        self._midi_out.close_port()

    def start_handling(self) -> None:
        """Starts handling MIDI input using current values of binds, controller, etc.

        Stops previous handler first. If any error occurs in this method, the
        previous handler will NOT be restored.
        """
        self.stop_handling()

        if self.selected_controller_name is None:
            raise Exception("No controller was selected.")
        if self.selected_binds is None:
            raise Exception("No binds were selected.")
        if self.selected_midi_in is None:
            raise Exception("No midi in port was selected.")
        if self.selected_midi_out is None:
            raise Exception("No midi out port was selected.")

        midi_in_port = self._midi_in.get_ports().index(self.selected_midi_in)
        midi_out_port = self._midi_out.get_ports().index(self.selected_midi_out)

        binds = Binds.load_from(self.get_selected_binds_path())
        controller = Controller.load_from(self.get_selected_controller_path())

        bound_controller = BoundController.create(binds, controller, self._actions)
        actions_handler = ActionsHandler(bound_controller, self._app)

        self._midi_in.open_port(midi_in_port)
        self._midi_out.open_port(midi_out_port)

        self._connected_controller = ConnectedController(
            actions_handler, controller, self._midi_in, self._midi_out
        )
