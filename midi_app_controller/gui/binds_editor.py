# TODO Move style somewhere else in the future to make this class independent from napari.
from typing import Callable, Optional

from napari.qt import get_current_stylesheet
from qtpy.QtCore import QThread
from app_model.types import CommandRule
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QRadioButton,
    QDialog,
    QScrollArea,
    QGridLayout,
    QLineEdit,
)

from midi_app_controller.gui.utils import ActionsQComboBox
from midi_app_controller.models.binds import ButtonBind, KnobBind, Binds
from midi_app_controller.models.controller import Controller, ControllerElement
from midi_app_controller.controller.connected_controller import ConnectedController


class LightUpQThread(QThread):
    """Worker thread responsible for lighting up a controller element.

    Attributes
    ----------
    func : Callable[[], None]
        Function for lighting up the element.
    """

    def __init__(self, func: Callable[[], None]):
        super().__init__()
        self.func = func

    def run(self):
        """Runs the lighting up function."""
        self.func()


class ButtonBinds(QWidget):
    """Widget that allows to change actions bound to each button.

    Attributes
    ----------
    actions_ : list[CommandRule]
        List of all actions available to bind and an empty string (used when
        no action is bound).
    button_combos : Tuple[int, ActionsQComboBox]
        List of all pairs (button id, ActionsQComboBox used to set action).
    binds_dict : dict[int, ControllerElement]
        Dictionary that allows to get a controller's button by its id.
    thread_list : list[QThread]
        List of worker threads responsible for lighting up buttons.
    """

    def __init__(
        self,
        buttons: list[ControllerElement],
        button_binds: list[ButtonBind],
        actions: list[CommandRule],
        connected_controller: Optional[ConnectedController],
    ):
        """Creates ButtonBinds widget.

        Parameters
        ----------
        buttons : list[ControllerElement]
            List of all available buttons.
        button_binds : list[ButtonBind]
            List of current binds.
        actions : list[CommandRule]
            List of all actions available to bind.
        connected_controller : ConnectedController
            Object representing currently connected MIDI controller.
        """
        super().__init__()

        self.connected_controller = connected_controller

        self.actions_ = actions
        self.button_combos = []
        self.binds_dict = {b.button_id: b for b in button_binds}

        # Description row.
        description_layout = QHBoxLayout()
        description_layout.addWidget(QLabel("Name:"))
        description_layout.addWidget(QLabel("Action when clicked:"))

        # All buttons available to bind.
        button_list = QWidget()
        button_layout = QVBoxLayout()
        for button in buttons:
            button_layout.addLayout(self._create_button_layout(button.id, button.name))
        button_layout.addStretch()
        button_list.setLayout(button_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(button_list)

        # Layout.
        layout = QVBoxLayout()
        layout.addLayout(description_layout)
        layout.addWidget(scroll)
        layout.addStretch()

        self.setLayout(layout)

        self.thread_list = []

    def _light_up_button(self, button_id: int):
        """Creates a QThread responsible for lighting up a knob."""
        if self.connected_controller is None:
            raise Exception("No controller connected.")

        def light_up_func():
            self.connected_controller.flash_button(button_id)

        thread = LightUpQThread(light_up_func)

        self.thread_list.append(thread)
        thread.start()

    def _create_button_layout(self, button_id: int, button_name: str) -> QGridLayout:
        """Creates layout for a button.

        The layout consists of button name and action selector. An entry is
        added to the `self.button_combos`.
        """
        # Check if there is an action bound to the button.
        if (bind := self.binds_dict.get(button_id)) is not None:
            action = bind.action_id
        else:
            action = None

        # ActionsQComboBox for action selection.
        action_combo = ActionsQComboBox(self.actions_, action, self)
        self.button_combos.append((button_id, action_combo))

        # Button for lighting up the controller element.
        is_controller_connected = self.connected_controller is not None
        light_up_button = QPushButton("Light up")
        light_up_button.setToolTip(
            None
            if is_controller_connected
            else "Start handling a controller to enable this feature."
        )
        light_up_button.setEnabled(is_controller_connected)
        light_up_button.clicked.connect(lambda: self._light_up_button(button_id))

        # Layout.
        elems_and_sizes = [
            (QLabel(button_name), 2),
            (light_up_button, 2),
            (QWidget(), 6),
            (action_combo, 10),
        ]

        layout = QHBoxLayout()
        for elem, size in elems_and_sizes:
            layout.addWidget(elem, size)

        return layout

    def get_binds(self) -> list[ButtonBind]:
        """Returns list of all binds currently set in this widget."""
        result = []
        for button_id, combo in self.button_combos:
            action = combo.get_selected_action_id()
            if action is not None:
                result.append(ButtonBind(button_id=button_id, action_id=action))
        return result


class KnobBinds(QWidget):
    """Widget that allows to change actions bound to each knob.

    Attributes
    ----------
    actions_ : list[CommandRule]
        List of all actions available to bind and an empty string (used when
        no action is bound).
    knob_combos : Tuple[int, ActionsQComboBox, ActionsQComboBox]
        List of all triples (knob id, ActionsQComboBox used to set increase action,
        ActionsQComboBox used to set decrease action).
    binds_dict : dict[int, ControllerElement]
        Dictionary that allows to get a controller's knob by its id.
    thread_list : list[QThread]
        List of worker threads responsible for lighting up knobs.
    """

    def __init__(
        self,
        knobs: list[ControllerElement],
        knob_binds: list[KnobBind],
        actions: list[CommandRule],
        connected_controller: Optional[ConnectedController],
    ):
        """Creates KnobBinds widget.

        Parameters
        ----------
        knobs : list[ControllerElement]
            List of all available knobs.
        knob_binds : list[KnobBind]
            List of current binds.
        actions : list[CommandRule]
            List of all actions available to bind.
        connected_controller : ConnectedController
            Object representing currently connected MIDI controller.
        """
        super().__init__()

        self.connected_controller = connected_controller

        self.actions_ = actions
        self.knob_combos = []
        self.binds_dict = {b.knob_id: b for b in knob_binds}

        # Description row.
        description_layout = QHBoxLayout()
        description_layout.addWidget(QLabel("Name:"))
        description_layout.addWidget(QLabel("Action when increased:"))
        description_layout.addWidget(QLabel("Action when decreased:"))

        # All knobs available to bind.
        knob_list = QWidget()
        self.knob_layout = QVBoxLayout()
        for elem in knobs:
            self.knob_layout.addLayout(self._create_knob_layout(elem.id, elem.name))
        self.knob_layout.addStretch()
        knob_list.setLayout(self.knob_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(knob_list)

        # Layout.
        layout = QVBoxLayout()
        layout.addLayout(description_layout)
        layout.addWidget(scroll)
        layout.addStretch()

        self.setLayout(layout)

        self.thread_list = []

    def _light_up_knob(self, knob_id: int):
        """Creates a QThread responsible for lighting up a knob."""
        if self.connected_controller is None:
            raise Exception("No controller connected.")

        def light_up_func():
            self.connected_controller.flash_knob(knob_id)

        thread = LightUpQThread(light_up_func)

        self.thread_list.append(thread)
        thread.start()

    def _create_knob_layout(self, knob_id: int, knob_name: str) -> QHBoxLayout:
        """Creates layout for a knob.

        The layout consists of knob name and increase/decrease action selector.
        An entry is added to the `self.knob_combos`.
        """
        # Check if there are any actions bound to the knob.
        if (bind := self.binds_dict.get(knob_id)) is not None:
            action_increase = bind.action_id_increase
            action_decrease = bind.action_id_decrease
        else:
            action_increase = None
            action_decrease = None

        # ActionsQComboBox for action selection.
        increase_action_combo = ActionsQComboBox(self.actions_, action_increase, self)
        decrease_action_combo = ActionsQComboBox(self.actions_, action_decrease, self)
        self.knob_combos.append((knob_id, increase_action_combo, decrease_action_combo))

        # Button for lighting up the controller element.
        is_controller_connected = self.connected_controller is not None
        light_up_knob = QPushButton("Light up")
        light_up_knob.setToolTip(
            None
            if is_controller_connected
            else "Start handling a controller to enable this feature."
        )
        light_up_knob.setEnabled(is_controller_connected)
        light_up_knob.clicked.connect(lambda: self._light_up_knob(knob_id))

        # Layout.
        elems_and_sizes = [
            (QLabel(knob_name), 1),
            (light_up_knob, 1),
            (QWidget(), 3),
            (increase_action_combo, 5),
            (decrease_action_combo, 5),
        ]

        layout = QHBoxLayout()
        for elem, size in elems_and_sizes:
            layout.addWidget(elem, size)

        return layout

    def get_binds(self) -> list[KnobBind]:
        """Returns list of all binds currently set in this widget."""
        result = []
        for knob_id, increase_action_combo, decrease_action_combo in self.knob_combos:
            increase_action = increase_action_combo.get_selected_action_id()
            decrease_action = decrease_action_combo.get_selected_action_id()
            if increase_action is not None or decrease_action is not None:
                result.append(
                    KnobBind(
                        knob_id=knob_id,
                        action_id_increase=increase_action,
                        action_id_decrease=decrease_action,
                    )
                )
        return result


class BindsEditor(QDialog):
    """Widget that allows to change actions bound to each knob/button and
    save them (or exit without saving).

    Attributes
    ----------
    save_binds : Callable[[list[KnobBind], list[ButtonBind]], None]
        Function called after "Save and exit" button is clicked.
    knobs_radio : QRadioButton
        Button that allows to switch binds view to knobs.
    buttons_radio : QRadioButton
        Button that allows to switch binds view to buttons.
    knobs_widget : KnobBinds
        Widget with binds editor for knobs.
    buttons_widget : ButtonBinds
        Widget with binds editor for buttons.
    """

    def __init__(
        self,
        controller: Controller,
        binds: Binds,
        actions: list[CommandRule],
        save_binds: Callable[[Binds], None],
        connected_controller: Optional[ConnectedController],
    ):
        """Creates BindsEditor widget.

        Parameters
        ---------
        controller : Controller
            Controller for which the binds are created.
        binds : Binds
            Current binds that the widget will be initialized with.
        actions : list[CommandRule]
            List of all actions available to bind.
        save_binds : Callable[[Binds], None]
            Function called after "Save and exit" button is clicked.
        """
        super().__init__()

        self.binds = binds.copy(deep=True)
        self.save_binds = save_binds

        self.name_edit = QLineEdit(binds.name)

        # Save/exit buttons.
        toggle_names_mode_button = QPushButton("Toggle names mode")
        toggle_names_mode_button.clicked.connect(self._toggle_names_mode)
        save_and_exit_button = QPushButton("Save and exit")
        save_and_exit_button.clicked.connect(self._save_and_exit)
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self._exit)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(toggle_names_mode_button)
        buttons_layout.addWidget(save_and_exit_button)
        buttons_layout.addWidget(exit_button)

        # Radio buttons for switching knobs/buttons view.
        self.knobs_radio = QRadioButton("Knobs")
        self.buttons_radio = QRadioButton("Buttons")
        self.knobs_radio.toggled.connect(self._switch_editors)
        self.buttons_radio.toggled.connect(self._switch_editors)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.knobs_radio)
        radio_layout.addWidget(self.buttons_radio)

        # Bind editors.
        self.knobs_widget = KnobBinds(
            controller.knobs,
            binds.knob_binds,
            actions,
            connected_controller,
        )
        self.buttons_widget = ButtonBinds(
            controller.buttons,
            binds.button_binds,
            actions,
            connected_controller,
        )

        # Layout.
        layout = QVBoxLayout()
        layout.addWidget(self.name_edit)
        layout.addLayout(radio_layout)
        layout.addLayout(buttons_layout)

        if connected_controller is None:
            layout.addWidget(
                QLabel("Start handling a controller to enable 'Light up' buttons.")
            )

        layout.addWidget(self.knobs_widget)
        layout.addWidget(self.buttons_widget)

        self.setLayout(layout)
        self.setStyleSheet(get_current_stylesheet())
        self.knobs_radio.setChecked(True)
        self.setMinimumSize(830, 650)

    def _switch_editors(self, checked: bool):
        """Switches binds editor view for knobs/buttons based on checked radio."""
        if not checked:
            return
        if self.knobs_radio.isChecked():
            self.buttons_widget.hide()
            self.knobs_widget.show()
        else:
            self.knobs_widget.hide()
            self.buttons_widget.show()

    def _toggle_names_mode(self):
        """Toggles actions names mode: titles or ids."""
        for _, combo in self.buttons_widget.button_combos:
            combo.toggle_names_mode()
        for _, combo1, combo2 in self.knobs_widget.knob_combos:
            combo1.toggle_names_mode()
            combo2.toggle_names_mode()

    def _save_and_exit(self):
        """Saves the binds and closes the widget."""
        self.binds.knob_binds = self.knobs_widget.get_binds()
        self.binds.button_binds = self.buttons_widget.get_binds()
        self.binds.name = self.name_edit.text()

        self.save_binds(self.binds)
        self._wait_for_worker_threads()
        self._exit()

    def _wait_for_worker_threads(self):
        """Waits for the threads responsible for lighting up the controller elements."""
        for thread in self.buttons_widget.thread_list:
            thread.wait()

        for thread in self.knobs_widget.thread_list:
            thread.wait()

    def _exit(self):
        """Closes the widget."""
        self.close()
