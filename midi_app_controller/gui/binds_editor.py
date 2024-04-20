from typing import Callable, List

# TODO Move style somewhere else in the future to make this class independent from napari.
from napari.qt import get_current_stylesheet
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
)

from midi_app_controller.gui.utils import ActionsQComboBox
from midi_app_controller.models.binds import ButtonBind, KnobBind, Binds
from midi_app_controller.models.controller import Controller, ControllerElement


class ButtonBinds(QWidget):
    """Widget that allows to change actions bound to each button.

    Attributes
    ----------
    actions : List[CommandRule]
        List of all actions available to bind and an empty string (used when
        no action is bound).
    button_combos : Tuple[int, ActionsQComboBox]
        List of all pairs (button id, ActionsQComboBox used to set action).
    binds_dict : dict[int, ControllerElement]
        Dictionary that allows to get a controller's button by its id.
    """

    def __init__(
        self,
        buttons: List[ControllerElement],
        button_binds: List[ButtonBind],
        actions: List[CommandRule],
    ):
        """Creates ButtonBinds widget.

        Parameters
        ----------
        buttons : List[ControllerElement]
            List of all available buttons.
        button_binds : List[ButtonBind]
            List of current binds.
        actions : List[CommandRule]
            List of all actions available to bind.
        """
        super().__init__()

        self.actions = actions
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

    def _create_button_layout(self, button_id: int, button_name: str) -> QHBoxLayout:
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
        action_combo = ActionsQComboBox(self.actions, action, self)
        self.button_combos.append((button_id, action_combo))

        layout = QHBoxLayout()
        layout.addWidget(QLabel(button_name))
        layout.addWidget(action_combo)

        return layout

    def get_binds(self) -> List[ButtonBind]:
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
    actions_ : List[CommandRule]
        List of all actions available to bind and an empty string (used when
        no action is bound).
    knob_combos : Tuple[int, ActionsQComboBox, ActionsQComboBox]
        List of all triples (knob id, ActionsQComboBox used to set increase action,
        ActionsQComboBox used to set decrease action).
    binds_dict : dict[int, ControllerElement]
        Dictionary that allows to get a controller's knob by its id.
    """

    def __init__(
        self,
        knobs: list[ControllerElement],
        knob_binds: list[KnobBind],
        actions: list[CommandRule],
    ):
        """Creates KnobBinds widget.

        Parameters
        ----------
        knobs : List[ControllerElement]
            List of all available knobs.
        knob_binds : List[KnobBind]
            List of current binds.
        actions : List[CommandRule]
            List of all actions available to bind.
        """
        super().__init__()

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

        # Layout.
        layout = QHBoxLayout()
        layout.addWidget(QLabel(knob_name))
        layout.addWidget(increase_action_combo)
        layout.addWidget(decrease_action_combo)

        return layout

    def get_binds(self) -> List[KnobBind]:
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
    save_binds : Callable[[List[KnobBind], List[ButtonBind]], None]
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
        actions: List[CommandRule],
        save_binds: Callable[[List[KnobBind], List[ButtonBind]], None],
    ):
        """Creates BindsEditor widget.

        Parameters
        ---------
        controller : Controller
            Controller for which the binds are created.
        binds : Binds
            Current binds that the widget will be initialized with.
        actions : List[CommandRule]
            List of all actions available to bind.
        save_binds : Callable[[List[KnobBind], List[ButtonBind]], None]
            Function called after "Save and exit" button is clicked.
        """
        super().__init__()

        self.save_binds = save_binds

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
        )
        self.buttons_widget = ButtonBinds(
            controller.buttons,
            binds.button_binds,
            actions,
        )

        # Layout.
        layout = QVBoxLayout()
        layout.addLayout(radio_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.knobs_widget)
        layout.addWidget(self.buttons_widget)

        self.setLayout(layout)
        self.setStyleSheet(get_current_stylesheet())
        self.knobs_radio.setChecked(True)
        self.setMinimumSize(830, 650)

    def _switch_editors(self, checked):
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
        knob_binds = self.knobs_widget.get_binds()
        button_binds = self.buttons_widget.get_binds()
        self.save_binds(knob_binds, button_binds)
        self._exit()

    def _exit(self):
        """Closes the widget."""
        self.close()
