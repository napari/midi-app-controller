import sys
from typing import Optional

from qtpy.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from midi_app_controller.config import Config
from midi_app_controller.gui.binds_editor import BindsEditor
from midi_app_controller.gui.utils import (
    DynamicQComboBox,
    is_subpath,
    reveal_in_explorer,
    vertical_layout,
)
from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller
from midi_app_controller.state.state_manager import SelectedItem, get_state_manager
from midi_app_controller.utils import get_copy_name


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
    current_midi_out : DynamicQComboBox
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

        state = get_state_manager()

        self.current_controller = DynamicQComboBox(
            state.selected_controller,
            state.get_available_controllers,
            self._select_controller,
            get_item_label=lambda x: x.name,
        )

        self.show_controllers_file_button = QPushButton("Reveal in explorer")
        self.show_controllers_file_button.clicked.connect(
            lambda: reveal_in_explorer(state.selected_controller.path)
        )

        # Binds selection.
        selected_binds = state.selected_binds
        self.current_binds = DynamicQComboBox(
            selected_binds,
            get_items=state.get_available_binds,
            select_item=self._select_binds,
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
        status_layout.addWidget(QLabel("Status:"))
        status_layout.addWidget(self.status)

        # Edit, start and stop buttons.
        self.edit_binds_button = QPushButton("Edit binds")
        self.edit_binds_button.clicked.connect(self._edit_binds)

        self.start_handling_button = QPushButton("Start handling")
        self.start_handling_button.clicked.connect(
            lambda: (state.save_state(), state.start_handling())
        )
        self.start_handling_button.clicked.connect(self.refresh)

        self.stop_handling_button = QPushButton("Stop handling")
        self.stop_handling_button.clicked.connect(state.stop_handling)
        self.stop_handling_button.clicked.connect(self.refresh)

        # Layout.
        layout = QVBoxLayout()
        layout.addLayout(vertical_layout("Controller:", self.current_controller))
        layout.addWidget(self.show_controllers_file_button)
        layout.addLayout(vertical_layout("Binds:", self.current_binds))
        layout.addWidget(self.show_binds_file_button)
        layout.addWidget(self.copy_binds_button)
        layout.addWidget(self.delete_binds_button)
        layout.addWidget(self.edit_binds_button)
        layout.addLayout(vertical_layout("MIDI input:", self.current_midi_in))
        layout.addLayout(vertical_layout("MIDI output:", self.current_midi_out))
        layout.addLayout(status_layout)
        layout.addWidget(self.start_handling_button)
        layout.addWidget(self.stop_handling_button)
        layout.addStretch()

        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        """Updates all widgets to ensure they match the data stored inside
        the `StateManager`."""
        state = get_state_manager()

        self.current_controller.refresh_items()
        self.current_controller.set_current(state.selected_controller)
        self.show_controllers_file_button.setEnabled(
            state.selected_controller is not None
        )

        self.current_binds.refresh_items()
        self.current_binds.set_current(state.selected_binds)
        self.current_midi_in.refresh_items()
        self.current_midi_in.set_current(state.selected_midi_in)
        self.current_midi_out.refresh_items()
        self.current_midi_out.set_current(state.selected_midi_out)
        self.show_binds_file_button.setEnabled(state.selected_binds is not None)
        self.edit_binds_button.setEnabled(state.selected_binds is not None)
        self.delete_binds_button.setEnabled(state.selected_binds is not None)
        self.copy_binds_button.setEnabled(state.selected_binds is not None)

        self.status.setText("Running" if state.is_running() else "Not running")
        self.start_handling_button.setText(
            "Start handling" if not state.is_running() else "Restart handling"
        )
        self.stop_handling_button.setEnabled(state.is_running())

    def _select_binds(self, binds: Optional[SelectedItem]) -> None:
        """Selects the `binds` and refreshes the widget."""
        state = get_state_manager()
        state.select_binds(binds)
        self.refresh()

    def _select_controller(self, controller: Optional[SelectedItem]) -> None:
        """Selects the `controller`, tries to select recent binds,
        and refreshes the widget."""
        state = get_state_manager()
        state.select_controller(controller)
        state.select_recent_binds()
        state.select_default_midi_ports()
        state.select_recent_midi_ports()
        self.refresh()

    def _copy_binds(self) -> None:
        """Copies the currently selected binds to a new file, selects that file,
        and refreshes the widget."""
        state = get_state_manager()
        binds_path = state.copy_binds()
        state.select_binds_path(binds_path)
        self.refresh()

    def _delete_binds(self) -> None:
        """Deletes the file with currently selected binds setup, and refreshes
        the widget."""
        state = get_state_manager()
        if (
            QMessageBox.question(
                self,
                "Confirm deletion",
                "Are you sure you want to delete this config "
                f"file?\n{state.selected_binds.path}",
                buttons=QMessageBox.Yes | QMessageBox.No,
                defaultButton=QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            state.delete_binds()
            self.refresh()

    def _edit_binds(self):
        """Opens dialog that will allow to edit currently selected binds."""
        state = get_state_manager()

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
            """Saves updated binds in the original location or in a new file
            if the location was read-only."""

            if is_subpath(Config.BINDS_READONLY_DIR, selected_binds.path):
                if new_binds.name == binds.name:
                    new_binds.name = get_copy_name(new_binds.name)
                new_file = new_binds.save_copy_to(
                    selected_binds.path.with_stem(new_binds.name),
                    Config.BINDS_USER_DIR,
                )
                state.select_binds_path(new_file)
                self.refresh()
            else:
                new_binds.save_to(selected_binds.path)

        editor_dialog = BindsEditor(
            controller,
            binds,
            state.get_actions(),
            save,
            state.connected_controller,
        )

        # Pause values synchronization (which conflicts with the "Light up"
        # feature) and handling MIDI messages. Enables elements highlighting.
        if state.connected_controller is not None:
            state.connected_controller.pause(
                editor_dialog.buttons_widget.highlight_button,
                editor_dialog.knobs_widget.highlight_knob,
            )

        # Show the dialog
        editor_dialog.exec_()

        # Restore the controller to work.
        if state.connected_controller is not None:
            state.connected_controller.resume()


def main():
    app = QApplication(sys.argv)
    view = MidiStatus()
    view.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
