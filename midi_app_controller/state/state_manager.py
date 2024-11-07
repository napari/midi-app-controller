from importlib.metadata import version
from pathlib import Path
from typing import NamedTuple, Optional

import rtmidi
from app_model import Application
from app_model.registries import MenusRegistry
from app_model.types import CommandRule, MenuItem
from packaging.version import parse as parse_version

# TODO: This will be made public in some future napari version
if parse_version(version("napari")) >= parse_version("0.5.4"):
    from napari._app_model import get_app_model
else:
    from napari._app_model import get_app as get_app_model

from midi_app_controller.actions.actions_handler import ActionsHandler
from midi_app_controller.actions.bound_controller import BoundController
from midi_app_controller.actions.napari_actions import register_custom_napari_actions
from midi_app_controller.config import Config
from midi_app_controller.controller.connected_controller import ConnectedController
from midi_app_controller.gui.utils import is_subpath
from midi_app_controller.models.app_state import AppState
from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller
from midi_app_controller.utils import get_copy_name


class SelectedItem(NamedTuple):
    """Info about an item (controller or binds) backed by a file.

    Attributes
    ----------
    name : str
        Display name of the item.
    path: Path
        Path to the file containing the real data.
    """

    name: str
    path: Path


class StateManager:
    """Stores the state of the app (like selected controller, ports etc.) and
    allows to update it.

    Attributes
    ----------
    selected_controller : Optional[SelectedItem]
        Currently selected schema of a controller.
    selected_binds : Optional[SelectedItem]
        Currently selected binds set.
    recent_binds_for_controller: dict[Path, Path] = {}
        Mapping of controller schemas to the binds set most recently used
        with the schema.
    recent_midi_ports_for_controller: dict[Path, dict[str, str]]
        Mapping of controller schemas to the MIDI ports most
        recently used (precisely dict with keys "in" and "out")
        with the schema.
    selected_midi_in : Optional[str]
        Name of currently selected MIDI input.
    selected_midi_out : Optional[str]
        Name of currently selected MIDI output.
    app : Application
        Used to execute actions.
    connected_controller : ConnectedController
        Object that handles MIDI input and output.
    _app_name : str
        Name of the app we want to handle. Used to filter binds files.
    _midi_in : rtmidi.MidiIn
        MIDI input client interface.
    _midi_out : rtmidi.MidiOut
        MIDI output client interface.
    """

    def __init__(self, app: Application):
        self.selected_controller = None
        self.selected_binds = None
        self.recent_binds_for_controller = {}
        self.recent_midi_ports_for_controller = {}
        self.selected_midi_in = None
        self.selected_midi_out = None
        self.app = app
        self.connected_controller = None
        self._app_name = app.name
        self._midi_in = rtmidi.MidiIn()
        self._midi_out = rtmidi.MidiOut()

    def is_running(self) -> bool:
        """Checks if any controller is being handled now."""
        return self.connected_controller is not None

    def get_available_controllers(self) -> list[SelectedItem]:
        """Returns all available controller schemas."""
        controllers = Controller.load_all_from(Config.CONTROLLER_DIRS)
        assert len(controllers) > 0, "Builtin controllers missing"
        return [SelectedItem(c.name, path) for c, path in controllers]

    def get_available_binds(self) -> list[SelectedItem]:
        """Returns all binds sets suitable for current controller and app."""
        if self.selected_controller is None:
            return []

        all_binds = Binds.load_all_from(Config.BINDS_DIRS)
        assert len(all_binds) > 0, "Builtin binds missing"
        return [
            SelectedItem(b.name, path)
            for b, path in all_binds
            if b.controller_name == self.selected_controller.name
        ]

    def get_available_midi_in(self) -> list[str]:
        """Returns names of all available MIDI input ports."""
        return self._midi_in.get_ports()

    def get_available_midi_out(self) -> list[str]:
        """Returns names of all available MIDI output ports."""
        return self._midi_out.get_ports()

    def get_actions(self) -> list[CommandRule]:
        """Returns a list of all actions currently registered in app model
        (and available in the command pallette)."""
        return sorted(
            {
                item.command
                for item in self.app.menus.get_menu(MenusRegistry.COMMAND_PALETTE_ID)
                if isinstance(item, MenuItem)
            },
            key=lambda command: command.id,
        )

    def select_binds(self, binds: Optional[SelectedItem]) -> None:
        """Updates currently selected binds.

        Does not have any immediate effect except updating the value.
        """
        self.selected_binds = binds

        if self.selected_controller is not None:
            self.recent_binds_for_controller[self.selected_controller.path] = (
                binds.path if binds is not None else None
            )

    def select_binds_path(self, binds_path: Optional[Path]) -> None:
        """Updates currently selected binds.

        Does not have any immediate effect except updating the value
        and finding the name of the binds set.
        """
        self.select_binds(
            SelectedItem(Binds.load_from(binds_path).name, binds_path)
            if binds_path is not None
            else None
        )

    def select_recent_binds(self) -> None:
        """Select binds that were recently used with the current controller."""
        self.select_binds_path(
            self.recent_binds_for_controller.get(
                self.selected_controller.path
                if self.selected_controller is not None
                else None
            )
        )

    def copy_binds(self) -> Path:
        """Copies currently selected binds and returns the new path."""
        if self.selected_binds is None:
            raise Exception("No binds are currently selected.")

        binds = Binds.load_from(self.selected_binds.path)
        binds.name = get_copy_name(binds.name)
        return binds.save_copy_to(
            self.selected_binds.path.with_stem(binds.name),
            Config.BINDS_USER_DIR,
        )

    def delete_binds(self) -> Path:
        """Deleted currently selected binds."""
        if self.selected_binds is None:
            raise Exception("No binds are currently selected.")
        if not is_subpath(Config.BINDS_USER_DIR, self.selected_binds.path):
            raise PermissionError("The binds are read-only.")

        self.selected_binds.path.unlink()
        self.select_binds(None)

    def select_controller(self, controller: Optional[SelectedItem]) -> None:
        """Updates currently selected controller schema.

        Does not have any immediate effect except updating the value.
        """
        self.selected_controller = controller

    def select_controller_path(self, controller_path: Optional[Path]) -> None:
        """Updates currently selected controller schema.

        Does not have any immediate effect except updating the value
        and finding the name of the binds set.
        """
        self.select_controller(
            SelectedItem(
                Controller.load_from(controller_path).name,
                controller_path,
            )
            if controller_path is not None
            else None
        )

    def select_midi_in(self, port_name: Optional[str]) -> None:
        """Updates currently selected MIDI input port name.

        Does not have any immediate effect except updating the value.
        """
        self.selected_midi_in = port_name
        if self.selected_controller:
            self.recent_midi_ports_for_controller[self.selected_controller.path] = {
                "in": self.selected_midi_in,
                "out": self.selected_midi_out,
            }

    def select_midi_out(self, port_name: Optional[str]) -> None:
        """Updates currently selected MIDI output port name.

        Does not have any immediate effect except updating the value.
        """
        self.selected_midi_out = port_name
        if self.selected_controller:
            self.recent_midi_ports_for_controller[self.selected_controller.path] = {
                "in": self.selected_midi_in,
                "out": self.selected_midi_out,
            }

    def stop_handling(self) -> None:
        """Stops handling any MIDI signals."""
        if self.connected_controller is not None:
            self.connected_controller.stop()
        self._midi_in.close_port()
        self._midi_out.close_port()
        self.connected_controller = None

    def start_handling(self) -> None:
        """Starts handling MIDI input using current values of binds, controller, etc.

        Stops the previous handler first. If any error occurs in this method,
        the previous handler will NOT be restored.
        """
        self.stop_handling()

        # Check if all required field are not None.
        if self.selected_controller is None:
            raise Exception("No controller was selected.")
        if self.selected_binds is None:
            raise Exception("No binds were selected.")
        if self.selected_midi_in is None:
            raise Exception("No MIDI input port was selected.")
        if self.selected_midi_out is None:
            raise Exception("No MIDI output port was selected.")

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
            actions=self.get_actions(),
        )
        actions_handler = ActionsHandler(
            bound_controller=bound_controller,
            app=self.app,
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

    def select_default_midi_ports(self):
        """Selects default port for the controller."""
        if self.selected_controller:
            controller = Controller.load_from(self.selected_controller.path)
            if controller.preferred_midi_in in self.get_available_midi_in():
                self.selected_midi_in = controller.preferred_midi_in

            if controller.preferred_midi_out in self.get_available_midi_out():
                self.selected_midi_out = controller.preferred_midi_out

    def select_recent_midi_ports(self):
        """Select MIDI ports that were recently used with the current controller."""
        if (
            self.selected_controller
            and self.selected_controller.path in self.recent_midi_ports_for_controller
        ):
            ports = self.recent_midi_ports_for_controller[self.selected_controller.path]
            if ports["in"] in self.get_available_midi_in():
                self.selected_midi_in = ports["in"]
            if ports["out"] in self.get_available_midi_out():
                self.selected_midi_out = ports["out"]

    def save_state(self):
        """Saves the current settings to the disk."""
        AppState(
            selected_controller_path=(
                self.selected_controller.path if self.selected_controller else None
            ),
            selected_binds_path=(
                self.selected_binds.path if self.selected_binds else None
            ),
            selected_midi_in=self.selected_midi_in,
            selected_midi_out=self.selected_midi_out,
            recent_binds_for_controller=self.recent_binds_for_controller,
            recent_midi_ports_for_controller=self.recent_midi_ports_for_controller,
        ).save_to(Config.APP_STATE_FILE)

    def load_state(self):
        """Tries to load recent settings from the disk."""
        if not Config.APP_STATE_FILE.exists():
            return
        state = AppState.load_from(Config.APP_STATE_FILE)

        # If the app state was saved by a different instance of this package,
        # there may be references to files local to the package, and we don't
        # want to use them. So we make sure that all file paths are ok for us
        # to use.
        controller_file = state.selected_controller_path
        if controller_file is None or not controller_file.exists():
            return
        if not any(is_subpath(d, controller_file) for d in Config.CONTROLLER_DIRS):
            return

        binds_files = [
            state.selected_binds_path,
            *state.recent_binds_for_controller.values(),
        ]
        for file in binds_files:
            if file is None:
                continue
            if not file.exists():
                return
            if not any(d and is_subpath(d, file) for d in Config.BINDS_DIRS):
                return

        self.select_controller_path(state.selected_controller_path)
        self.select_binds_path(state.selected_binds_path)
        self.select_midi_in(state.selected_midi_in)
        self.select_midi_out(state.selected_midi_out)
        self.recent_binds_for_controller = state.recent_binds_for_controller
        self.recent_midi_ports_for_controller = state.recent_midi_ports_for_controller


_STATE_MANAGER = None


def get_state_manager() -> StateManager:
    """Returns the `StateManager` singleton."""
    global _STATE_MANAGER
    if _STATE_MANAGER is None:
        register_custom_napari_actions(get_app_model())
        _STATE_MANAGER = StateManager(get_app_model())
        _STATE_MANAGER.load_state()
    return _STATE_MANAGER
