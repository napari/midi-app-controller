import sys
from typing import Callable, List

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
    QMenu,
    QLabel,
    QHBoxLayout,
)

from midi_app_controller.models.binds import ButtonBind, KnobBind, Binds
from midi_app_controller.models.controller import Controller
from midi_app_controller.gui.binds_editor import BindsEditor
from midi_app_controller.state.state_manager import StateManager


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

# TODO I didn't find any better way to get all available actions.
NAPARI_ACTIONS = HELP_ACTIONS + LAYER_ACTIONS + VIEW_ACTIONS + SLIDER_ACTIONS

state_manager = StateManager(NAPARI_ACTIONS, get_app())


class MidiStatus(QWidget):
    """Widget that allows to select currently used controller, binds, MIDI ports,
    to edit binds and to start/stop handling MIDI messages.

    Attributes
    ----------
    current_binds : QPushButton
        Button that allows to select binds using its menu. Its text
        is set to currently selected binds.
    current_controller : QPushButton
        Button that allows to select controller using its menu. Its text
        is set to currently selected controller.
    current_midi_in : QPushButton
        Button that allows to select MIDI input port using its menu. Its
        text is set to currently selected port.
    current_midi_in : QPushButton
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

        # Binds selection.
        selected_binds = state_manager.selected_binds
        self.current_binds = QPushButton(
            selected_binds.name if selected_binds is not None else None
        )
        self.current_binds.setMenu(
            self._create_dynamic_menu(
                self.current_binds,
                state_manager.get_available_binds,
                state_manager.select_binds,
            )
        )

        # Controller selection.
        selected_controller = state_manager.selected_controller
        self.current_controller = QPushButton(
            selected_controller.name if selected_controller is not None else None
        )

        def select_controller(name: str) -> None:
            state_manager.select_controller(name)
            state_manager.selected_binds = None
            self.current_binds.setText(None)

        self.current_controller.setMenu(
            self._create_dynamic_menu(
                self.current_controller,
                state_manager.get_available_controllers,
                select_controller,
            )
        )

        # MIDI input and output selection.
        self.current_midi_in = QPushButton(state_manager.selected_midi_in)
        self.current_midi_in.setMenu(
            self._create_dynamic_menu(
                self.current_midi_in,
                state_manager.get_available_midi_in,
                state_manager.select_midi_in,
            )
        )

        self.current_midi_out = QPushButton(state_manager.selected_midi_out)
        self.current_midi_out.setMenu(
            self._create_dynamic_menu(
                self.current_midi_out,
                state_manager.get_available_midi_out,
                state_manager.select_midi_out,
            )
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

        self.start_handling_button = QPushButton("Start handling")
        self.start_handling_button.clicked.connect(state_manager.start_handling)
        self.start_handling_button.clicked.connect(update_status)

        self.stop_handling_button = QPushButton("Stop handling")
        self.stop_handling_button.clicked.connect(state_manager.stop_handling)
        self.stop_handling_button.clicked.connect(update_status)

        # Layout.
        layout = QVBoxLayout()
        layout.addLayout(
            self._create_label_button_layout("Controller:", self.current_controller)
        )
        layout.addLayout(self._create_label_button_layout("Binds:", self.current_binds))
        layout.addLayout(
            self._create_label_button_layout("MIDI input:", self.current_midi_in)
        )
        layout.addLayout(
            self._create_label_button_layout("MIDI output:", self.current_midi_out)
        )
        layout.addLayout(status_layout)
        layout.addWidget(self.edit_binds_button)
        layout.addWidget(self.start_handling_button)
        layout.addWidget(self.stop_handling_button)
        layout.addStretch()

        self.setLayout(layout)

    def _create_dynamic_menu(
        self,
        button: QPushButton,
        get_entries: Callable[[], List[str]],
        select_entry: Callable[[str], None],
    ) -> QMenu:
        """Creates a scrollable menu that will display entries from `get_entries()`
        each time it's opened.

        When an entry is selected:
        - the text of `button` is set to the entry,
        - `select_entry` is invoked with the entry as argument.
        """
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { menu-scrollable: 1; }")

        def add_actions():
            """Clears the menu and adds entries from `get_entries()`."""
            menu.clear()
            for elem in get_entries():

                def select(elem=elem):
                    """Update button's text and run `select_entry()`."""
                    button.setText(elem)
                    select_entry(elem)

                menu.addAction(elem, select)

        menu.aboutToShow.connect(add_actions)
        return menu

    def _create_label_button_layout(
        self, label: str, button: QPushButton
    ) -> QHBoxLayout:
        """Creates horizontal layout consisting of label on the left half and
        button on the right half."""
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        layout.addWidget(button)
        return layout

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
            """Saves updated binds in the original location."""
            binds.knob_binds = knob_binds
            binds.button_binds = button_binds
            binds.save_to(selected_binds.path)

        # Show the dialog.
        editor_dialog = BindsEditor(
            controller,
            binds,
            list(map(lambda a: a.id, state_manager.actions)),
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
