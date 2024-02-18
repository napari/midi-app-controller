from typing import Callable, List

# TODO Move style somewhere else in the future to make this class independent from napari.
from napari.qt import get_current_stylesheet
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QMenu,
    QRadioButton,
    QDialog,
    QScrollArea,
)

from midi_app_controller.models.binds import ButtonBind, KnobBind, Binds
from midi_app_controller.models.controller import Controller, ControllerElement


class ButtonBinds(QWidget):
    """Widget that allows to change actions bound to each button.

    Attributes
    ----------
    actions : List[str]
        List of all actions available to bind and an empty string (used when
        no action is bound).
    button_menus : Tuple[int, QPushButton]
        List of all pairs (button id, QPushButton used to set action). Each
        QPushButton text is the currently selected action.
    binds_dict : dict[int, ControllerElement]
        Dictionary that allows to get a controller's button by its id.
    """

    def __init__(
        self,
        buttons: List[ControllerElement],
        button_binds: List[ButtonBind],
        actions: List[str],
    ):
        """Creates ButtonBinds widget.

        Parameters
        ----------
        buttons : List[ControllerElement]
            List of all available buttons.
        button_binds : List[ButtonBind]
            List of currentl binds.
        actions : List[str]
            List of all actions available to bind.
        """
        super().__init__()

        self.actions = [""] + actions
        self.button_menus = []
        self.binds_dict = {b.button_id: b for b in button_binds}

        # Description row.
        description_layout = QHBoxLayout()
        description_layout.addWidget(QLabel("Name:"))
        description_layout.addWidget(QLabel("Action when clicked:"))

        # All buttons available to bind.
        button_list = QWidget()
        button_layout = QVBoxLayout()
        for elem in buttons:
            button_layout.addLayout(self._create_button_layout(elem.id, elem.name))
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
        added to the `self.button_menus`.
        """
        # Check if there is an action bound to the button.
        if (bind := self.binds_dict.get(button_id)) is not None:
            action = bind.action_id
        else:
            action = None

        # QPushButton with menu.
        button_action = QPushButton(action)
        button_action.setMenu(self._create_action_menu(button_action))

        self.button_menus.append((button_id, button_action))

        layout = QHBoxLayout()
        layout.addWidget(QLabel(button_name))
        layout.addWidget(button_action)

        return layout

    def _create_action_menu(self, button: QPushButton) -> QMenu:
        """Creates a scrollable menu consisting of all `self.actions`.

        When an action is selected, the text of `button` is set its name.
        """
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { menu-scrollable: 1; }")
        for action in self.actions:
            menu.addAction(action, lambda action=action: button.setText(action))
        return menu

    def get_binds(self) -> List[ButtonBind]:
        """Returns list of all binds currently set in this widget."""
        result = []
        for button_id, button in self.button_menus:
            action = button.text() or None
            if action is not None:
                result.append(ButtonBind(button_id=button_id, action_id=action))
        return result


class KnobBinds(QWidget):
    """Widget that allows to change actions bound to each knob.

    Attributes
    ----------
    actions : List[str]
        List of all actions available to bind and an empty string (used when
        no action is bound).
    knob_menus : Tuple[int, QPushButton, QPushButton]
        List of all triples (knob id, QPushButton used to set increase action,
        QPushButton used to set decrease action). Each QPushButton text is
        the currently selected action.
    binds_dict : dict[int, ControllerElement]
        Dictionary that allows to get a controller's knob by its id.
    """

    def __init__(
        self,
        knobs: List[ControllerElement],
        knob_binds: List[KnobBind],
        actions: List[str],
    ):
        """Creates KnobBinds widget.

        Parameters
        ----------
        knobs : List[ControllerElement]
            List of all available knobs.
        knob_binds : List[KnobBind]
            List of current binds.
        actions : List[str]
            List of all actions available to bind.
        """
        super().__init__()

        self.actions = [""] + actions
        self.knob_menus = []
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

    def _create_action_menu(self, knob: QPushButton) -> QMenu:
        """Creates a scrollable menu consisting of all `self.actions`.

        When an action is selected, the text of `knob` is set its name.
        """
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { menu-scrollable: 1; }")
        for action in self.actions:
            menu.addAction(action, lambda action=action: knob.setText(action))
        return menu

    def _create_knob_layout(self, knob_id: int, knob_name: str) -> QHBoxLayout:
        """Creates layout for a knob.

        The layout consists of knob name and increase/decrease action selector.
        An entry is added to the `self.knob_menus`.
        """
        # Check if there are any actions bound to the knob.
        if (bind := self.binds_dict.get(knob_id)) is not None:
            action_increase = bind.action_id_increase
            action_decrease = bind.action_id_decrease
        else:
            action_increase = ""
            action_decrease = ""

        # QPushButton with menus.
        knob_increase = QPushButton(action_increase)
        knob_increase.setMenu(self._create_action_menu(knob_increase))
        knob_decrease = QPushButton(action_decrease)
        knob_decrease.setMenu(self._create_action_menu(knob_decrease))

        self.knob_menus.append((knob_id, knob_increase, knob_decrease))

        # Layout.
        layout = QHBoxLayout()
        layout.addWidget(QLabel(knob_name))
        layout.addWidget(knob_increase)
        layout.addWidget(knob_decrease)

        return layout

    def get_binds(self) -> List[KnobBind]:
        """Returns list of all binds currently set in this widget."""
        result = []
        for knob_id, knob_increase, knob_decrease in self.knob_menus:
            increase_action = knob_increase.text() or None
            decrease_action = knob_decrease.text() or None
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
        actions: List[str],
        save_binds: Callable[[List[KnobBind], List[ButtonBind]], None],
    ):
        """Creates BindsEditor widget.

        Parameters
        ---------
        controller : Controller
            Controller for which the binds are created.
        binds : Binds
            Current binds that the widget will be initialized with.
        actions : List[str]
            List of all actions available to bind.
        save_binds : Callable[[List[KnobBind], List[ButtonBind]], None]
            Function called after "Save and exit" button is clicked.
        """
        super().__init__()

        self.save_binds = save_binds

        # Save/exit buttons.
        save_and_exit_button = QPushButton("Save and exit")
        save_and_exit_button.clicked.connect(self._save_and_exit)
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self._exit)

        buttons_layout = QHBoxLayout()
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
        self.setMinimumSize(500, 550)

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

    def _save_and_exit(self):
        """Saves the binds and closes the widget."""
        knob_binds = self.knobs_widget.get_binds()
        button_binds = self.buttons_widget.get_binds()
        self.save_binds(knob_binds, button_binds)
        self._exit()

    def _exit(self):
        """Closes the widget."""
        self.close()
