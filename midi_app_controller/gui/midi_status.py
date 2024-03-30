import sys
from typing import List

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
)

from midi_app_controller.models.binds import ButtonBind, KnobBind, Binds
from midi_app_controller.models.controller import Controller
from midi_app_controller.gui.binds_editor import BindsEditor
from midi_app_controller.gui.utils import DynamicQComboBox, is_subpath, reveal_in_explorer
from midi_app_controller.state.state_manager import StateManager
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

state_manager = StateManager(NAPARI_ACTIONS, get_app())


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
        def select_controller(name: str) -> None:
            state_manager.select_controller(name)
            state_manager.selected_binds = None
            self.current_binds.setCurrentText(None)
            self.show_controllers_file_button.setEnabled(state_manager.selected_controller.path is not None)

        selected_controller = state_manager.selected_controller
        self.current_controller = DynamicQComboBox(
            selected_controller.name if selected_controller is not None else None,
            state_manager.get_available_controllers,
            select_controller,
        )

        self.show_controllers_file_button = QPushButton("Reveal in explorer")
        self.show_controllers_file_button.clicked.connect(lambda: reveal_in_explorer(state_manager.selected_controller.path))
        self.show_controllers_file_button.setEnabled(False)
        
        def select_binds(name: str) -> None:
            state_manager.select_binds(name)
            self.show_binds_file_button.setEnabled(state_manager.selected_binds.path is not None)
            self.edit_binds_button.setEnabled(state_manager.selected_binds.path is not None)
            self.copy_binds_button.setEnabled(state_manager.selected_binds.path is not None)

        # Binds selection.
        selected_binds = state_manager.selected_binds
        self.current_binds = DynamicQComboBox(
            selected_binds.name if selected_binds is not None else None,
            state_manager.get_available_binds,
            select_binds,
        )

        self.show_binds_file_button = QPushButton("Reveal in explorer")
        self.show_binds_file_button.clicked.connect(lambda: reveal_in_explorer(state_manager.selected_binds.path))
        self.show_binds_file_button.setEnabled(False)

        # MIDI input and output selection.
        self.current_midi_in = DynamicQComboBox(
            state_manager.selected_midi_in,
            state_manager.get_available_midi_in,
            state_manager.select_midi_in,
        )

        self.current_midi_out = DynamicQComboBox(
            state_manager.selected_midi_out,
            state_manager.get_available_midi_out,
            state_manager.select_midi_out,
        )

        # Status.
        self.status = QLabel(None)
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status"))
        status_layout.addWidget(self.status)

        def update_status():
            if state_manager.is_running():
                self.status.setText("Running")
            else:
                self.status.setText("Not running")

        update_status()

        # Edit, start and stop buttons.
        self.edit_binds_button = QPushButton("Edit binds")
        self.edit_binds_button.clicked.connect(self._edit_binds)
        self.edit_binds_button.setEnabled(False)

        self.copy_binds_button = QPushButton("Copy config file")
        self.copy_binds_button.clicked.connect(self._copy_binds)
        self.copy_binds_button.setEnabled(False)

        self.start_handling_button = QPushButton("Start handling")
        self.start_handling_button.clicked.connect(state_manager.start_handling)
        self.start_handling_button.clicked.connect(update_status)

        self.stop_handling_button = QPushButton("Stop handling")
        self.stop_handling_button.clicked.connect(state_manager.stop_handling)
        self.stop_handling_button.clicked.connect(update_status)

        # Layout.
        layout = QVBoxLayout()
        layout.addLayout(
            self._horizontal_layout("Controller:", self.current_controller)
        )
        layout.addWidget(self.show_controllers_file_button)
        layout.addLayout(self._horizontal_layout("Binds:", self.current_binds))
        layout.addWidget(self.show_binds_file_button)
        layout.addWidget(self.copy_binds_button)
        layout.addWidget(self.edit_binds_button)
        layout.addLayout(self._horizontal_layout("MIDI input:", self.current_midi_in))
        layout.addLayout(self._horizontal_layout("MIDI output:", self.current_midi_out))
        layout.addLayout(status_layout)
        layout.addWidget(self.start_handling_button)
        layout.addWidget(self.stop_handling_button)
        layout.addStretch()

        self.setLayout(layout)

    def _horizontal_layout(self, label: str, widget: QWidget) -> QHBoxLayout:
        """Creates horizontal layout consisting of the `label` on the left half\
        and the `widget` on the right half."""
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        layout.addWidget(widget)
        return layout
    
    def _copy_binds(self):
        if state_manager.selected_binds is None:
            raise Exception("No binds selected")
        
        binds = Binds.load_from(state_manager.selected_binds.path)
        binds.name += " (Copy)"
        binds.save_copy_to(state_manager.selected_binds.path, Config.BINDS_USER_DIR)

    def _edit_binds(self):
        """Opens dialog that will allow to edit currently selected binds."""
        # Get selected controller and binds.
        selected_controller = state_manager.selected_controller
        selected_binds = state_manager.selected_binds

        if selected_controller is None:
            raise Exception("No controller selected.")
        if selected_binds is None:
            raise Exception("No binds selected.")

        # Load the configuration files from disk.
        controller = Controller.load_from(selected_controller.path)
        binds = Binds.load_from(selected_binds.path)

        def save(knob_binds: List[KnobBind], button_binds: List[ButtonBind]) -> None:
            """Saves updated binds in the original location or in a new file if the location was read-only."""

            binds.knob_binds = knob_binds
            binds.button_binds = button_binds

            if is_subpath(Config.BINDS_READONLY_DIR, selected_binds.path):
                binds.name = binds.name + " (Copy)"
                binds.save_copy_to(selected_binds.path, Config.BINDS_USER_DIR)
            else:
              binds.save_to(selected_binds.path)

        # Show the dialog.
        editor_dialog = BindsEditor(
            controller,
            binds,
            # TODO Get actions directly from app-model when it's supported.
            state_manager.actions,
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
