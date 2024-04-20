import datetime
import re
import sys
from typing import Optional

from app_model.types import Action
from napari.components import LayerList
from napari._app_model import get_app
from napari._app_model.actions._help_actions import HELP_ACTIONS
from napari._app_model.actions._layer_actions import LAYER_ACTIONS
from napari._app_model.actions._view_actions import VIEW_ACTIONS
from qtpy.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QMessageBox,
)

from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller
from midi_app_controller.gui.binds_editor import BindsEditor
from midi_app_controller.gui.utils import (
    DynamicQComboBox,
    is_subpath,
    reveal_in_explorer,
)
from midi_app_controller.state.state_manager import SelectedItem, StateManager
from midi_app_controller.config import Config


def decrease_opacity(ll: LayerList):
    for lay in ll.selection:
        lay.opacity = max(0, lay.opacity - 0.01)


def increase_opacity(ll: LayerList):
    for lay in ll.selection:
        lay.opacity = min(1, lay.opacity + 0.01)


# TODO Added only to allow testing slider actions until they are added to napari.
SLIDER_ACTIONS = [
    Action(
        id="napari:layer:increase_opacity",
        title="Increase opacity",
        callback=increase_opacity,
    ),
    Action(
        id="napari:layer:decrease_opacity",
        title="Decrease opacity",
        callback=decrease_opacity,
    ),
]
for action in SLIDER_ACTIONS:
    get_app().register_action(action)

# TODO Get actions directly from app-model when it's supported.
NAPARI_ACTIONS = HELP_ACTIONS + LAYER_ACTIONS + VIEW_ACTIONS + SLIDER_ACTIONS

state = StateManager(NAPARI_ACTIONS, get_app())


class MidiStatus(QWidget):
    """Widget that allows to select currently used controller, binds, MIDI ports,
    to edit binds and to start/stop handling MIDI messages.

    Attributes
    ----------
    current_binds : DynamicQComboBox
        Button that allows to select binds using its menu. Its text
        is set to currently selected binds.
    current_controller : DynamicQComboBox
        Button that allows to select controller using its menu. Its text
        is set to currently selected controller.
    current_midi_in : DynamicQComboBox
        Button that allows to select MIDI input port using its menu. Its
        text is set to currently selected port.
    current_midi_in : DynamicQComboBox
        Button that allows to select MIDI output port using its menu. Its
        text is set to currently selected port.
    status : QLabel
        Either "Running" or "Not running". Describes the status of MIDI
        messages handling.
    start_handling_button : QPushButton
        Starts handling MIDI messages using currently selected items.
    stop_handling_button : QPushButton
        Stops handling MIDI messages.
    """

    def __init__(self):
        super().__init__()

        # Controller selection.
        def select_controller(controller: Optional[SelectedItem]) -> None:
            controller_path = None if controller is None else controller.path
            state.select_controller(controller_path)
            state.select_binds(
                state.recent_binds_for_controller.get(controller_path, None)
            )
            self.refresh()

        selected_controller = state.selected_controller
        self.current_controller = DynamicQComboBox(
            selected_controller,
            state.get_available_controllers,
            select_controller,
            get_item_label=lambda x: x.name,
        )

        self.show_controllers_file_button = QPushButton("Reveal in explorer")
        self.show_controllers_file_button.clicked.connect(
            lambda: reveal_in_explorer(state.selected_controller.path)
        )

        def select_binds(binds: Optional[SelectedItem]) -> None:
            state.select_binds(None if binds is None else binds.path)
            self.refresh()

        # Binds selection.
        selected_binds = state.selected_binds
        self.current_binds = DynamicQComboBox(
            selected_binds,
            get_items=state.get_available_binds,
            select_item=select_binds,
            get_item_label=lambda x: x.name,
        )

        self.show_binds_file_button = QPushButton("Reveal in explorer")
        self.show_binds_file_button.clicked.connect(
            lambda: reveal_in_explorer(state.selected_binds.path)
        )

        # Edit, start and stop buttons.
        self.edit_binds_button = QPushButton("Edit binds")
        self.edit_binds_button.clicked.connect(self._edit_binds)

        self.copy_binds_button = QPushButton("Copy config file")
        self.copy_binds_button.clicked.connect(self._copy_binds)

        self.delete_binds_button = QPushButton("Delete config file")
        self.delete_binds_button.clicked.connect(self._delete_binds)

        # MIDI input and output selection.
        self.current_midi_in = DynamicQComboBox(
            state.selected_midi_in,
            state.get_available_midi_in,
            state.select_midi_in,
        )

        self.current_midi_out = DynamicQComboBox(
            state.selected_midi_out,
            state.get_available_midi_out,
            state.select_midi_out,
        )

        # Status.
        self.status = QLabel(None)
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status"))
        status_layout.addWidget(self.status)

        self.start_handling_button = QPushButton("Start handling")
        self.start_handling_button.clicked.connect(state.start_handling)
        self.start_handling_button.clicked.connect(self.refresh)

        self.stop_handling_button = QPushButton("Stop handling")
        self.stop_handling_button.clicked.connect(state.stop_handling)
        self.stop_handling_button.clicked.connect(self.refresh)

        # Layout.
        layout = QVBoxLayout()
        layout.addLayout(
            self._horizontal_layout("Controller:", self.current_controller)
        )
        layout.addWidget(self.show_controllers_file_button)
        layout.addLayout(self._horizontal_layout("Binds:", self.current_binds))
        layout.addWidget(self.show_binds_file_button)
        layout.addWidget(self.copy_binds_button)
        layout.addWidget(self.delete_binds_button)
        layout.addWidget(self.edit_binds_button)
        layout.addLayout(self._horizontal_layout("MIDI input:", self.current_midi_in))
        layout.addLayout(self._horizontal_layout("MIDI output:", self.current_midi_out))
        layout.addLayout(status_layout)
        layout.addWidget(self.start_handling_button)
        layout.addWidget(self.stop_handling_button)
        layout.addStretch()

        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        """Updates all widgets to ensure they match the data stored inside the StateManager."""

        self.current_controller.refresh_items()
        self.current_controller.set_current(state.selected_controller)
        self.show_controllers_file_button.setEnabled(
            state.selected_controller is not None
        )

        self.current_binds.refresh_items()
        self.current_binds.set_current(state.selected_binds)
        self.show_binds_file_button.setEnabled(state.selected_binds is not None)
        self.edit_binds_button.setEnabled(state.selected_binds is not None)
        self.delete_binds_button.setEnabled(state.selected_binds is not None)
        self.copy_binds_button.setEnabled(state.selected_binds is not None)

        self.status.setText("Running" if state.is_running() else "Not running")
        self.start_handling_button.setText(
            "Start handling" if not state.is_running() else "Restart handling"
        )
        self.stop_handling_button.setEnabled(state.is_running())

    def _horizontal_layout(self, label: str, widget: QWidget) -> QHBoxLayout:
        """Creates horizontal layout consisting of the `label` on the left half\
        and the `widget` on the right half."""
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        layout.addWidget(widget)
        return layout

    @staticmethod
    def _get_copy_name(current_name: str) -> str:
        """Finds a good name for a copy of a file.

        Currently adds "({timestamp} copy)" to the end of the name, or replaces the timestamp with current time if already present.
        """
        if m := re.fullmatch(r"(.*) \([0-9. -]* copy\)", current_name):
            current_name = m.group(1)
        timestamp = (
            datetime.datetime.now().isoformat().replace(":", "-").replace("T", " ")
        )
        return f"{current_name} ({timestamp} copy)"

    def _copy_binds(self):
        """Copies the currently selected binds to a new file, and selects that file."""
        assert state.selected_binds is not None, "No binds selected"

        binds = Binds.load_from(state.selected_binds.path)
        binds.name = self._get_copy_name(binds.name)
        new_file = binds.save_copy_to(
            state.selected_binds.path.with_stem(binds.name), Config.BINDS_USER_DIR
        )
        state.select_binds(new_file)
        self.refresh()

    def _delete_binds(self):
        """Deletes the file with currently selected binds setup."""
        assert state.selected_binds is not None, "No binds selected"
        if not is_subpath(Config.BINDS_USER_DIR, state.selected_binds.path):
            raise PermissionError("This config file is read-only")

        if (
            QMessageBox.question(
                self,
                "Confirm deletion",
                f"Are you sure you want to delete this config file?\n{state.selected_binds.path}",
                buttons=QMessageBox.Yes | QMessageBox.No,
                defaultButton=QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return

        state.selected_binds.path.unlink()
        state.select_binds(None)
        self.refresh()

    def _edit_binds(self):
        """Opens dialog that will allow to edit currently selected binds."""
        # Get selected controller and binds.
        selected_controller = state.selected_controller
        selected_binds = state.selected_binds

        if selected_controller is None:
            raise Exception("No controller selected.")
        if selected_binds is None:
            raise Exception("No binds selected.")

        # Load the configuration files from disk.
        controller = Controller.load_from(selected_controller.path)
        binds = Binds.load_from(selected_binds.path)

        def save(new_binds) -> None:
            """Saves updated binds in the original location or in a new file if the location was read-only."""

            if is_subpath(Config.BINDS_READONLY_DIR, selected_binds.path):
                if new_binds.name == binds.name:
                    new_binds.name = self._get_copy_name(new_binds.name)
                new_file = new_binds.save_copy_to(
                    selected_binds.path.with_stem(new_binds.name), Config.BINDS_USER_DIR
                )
                state.select_binds(new_file)
                self.refresh()
            else:
                new_binds.save_to(selected_binds.path)

        # Show the dialog.
        editor_dialog = BindsEditor(
            controller,
            binds,
            # TODO Get actions directly from app-model when it's supported.
            state.actions,
            save,
        )
        editor_dialog.exec_()


def main():
    app = QApplication(sys.argv)
    view = MidiStatus()
    view.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
