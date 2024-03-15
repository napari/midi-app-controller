from typing import Callable, List

# TODO Move style somewhere else in the future to make this class independent from napari.
from napari.qt import get_current_stylesheet
from qtpy.QtCore import Qt, QThread, QMutex, QMutexLocker
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
    QLayoutItem,
)

from midi_app_controller.gui.utils import SearchableQComboBox
from midi_app_controller.models.binds import ButtonBind, KnobBind, Binds
from midi_app_controller.models.controller import Controller, ControllerElement
from midi_app_controller.controller.connected_controller import ConnectedController


class LightUpQThread(QThread):
    def __init__(self, func, mutex, id, id_set):
        super().__init__()
        self.func = func
        self.mutex = mutex
        self.id = id
        self.id_set = id_set

    def run(self):
        flashing = False
        with QMutexLocker(self.mutex):
            if self.id in self.id_set:
                flashing = True
            else:
                self.id_set.add(self.id)

        if not flashing:
            self.func()

            with QMutexLocker(self.mutex):
                self.id_set.remove(self.id)


class ButtonBinds(QWidget):
    """Widget that allows to change actions bound to each button.

    Attributes
    ----------
    actions : List[str]
        List of all actions available to bind and an empty string (used when
        no action is bound).
    button_menus : Tuple[int, SearchableQComboBox]
        List of all pairs (button id, SearchableQComboBox used to set action).
    binds_dict : dict[int, ControllerElement]
        Dictionary that allows to get a controller's button by its id.
    """

    def __init__(
        self,
        buttons: List[ControllerElement],
        button_binds: List[ButtonBind],
        actions: List[str],
        connected_controller: ConnectedController,
    ):
        """Creates ButtonBinds widget.

        Parameters
        ----------
        buttons : List[ControllerElement]
            List of all available buttons.
        button_binds : List[ButtonBind]
            List of current binds.
        actions : List[str]
            List of all actions available to bind.
        """
        super().__init__()

        self.connected_controller = connected_controller

        self.actions = [""] + actions
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

        self.flashing_buttons = set([])
        self.thread_list = []
        self.buttons_mutex = QMutex()

    def _light_up_button(self, button_id: int):
        if self.connected_controller is None:
            raise Exception("No controller connected.")

        def light_up_func():
            self.connected_controller.flash_button(button_id)

        thread = LightUpQThread(
            light_up_func,
            self.buttons_mutex,
            button_id,
            self.flashing_buttons,
        )

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

        # SearchableQComboBox for action selection.
        action_combo = SearchableQComboBox(self.actions, action, self)
        self.button_combos.append((button_id, action_combo))

        # Button label
        button_label = QLabel(button_name)

        # Button for lighting up the controller element
        controller_disconnected = self.connected_controller is None
        light_up_button = QPushButton("Light up")
        light_up_button.setToolTip(f"Lights up the '{button_name}'")
        light_up_button.setCursor(Qt.PointingHandCursor)
        light_up_button.clicked.connect(lambda: self._light_up_button(button_id))

        sizes = [2, 2, 6, 10]
        elems = [
            button_label,
            light_up_button,
            QWidget(),
            action_combo,
        ]

        if controller_disconnected:
            sizes = [2, 8, 10]
            del elems[1]

        layout = QGridLayout()
        BindsEditor._add_elements_to_grid_layout(layout, elems, sizes)

        return layout

    def get_binds(self) -> List[ButtonBind]:
        """Returns list of all binds currently set in this widget."""
        result = []
        for button_id, combo in self.button_combos:
            action = combo.currentText() or None
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
    knob_combos : Tuple[int, SearchableQComboBox, SearchableQComboBox]
        List of all triples (knob id, SearchableQComboBox used to set increase action,
        SearchableQComboBox used to set decrease action).
    binds_dict : dict[int, ControllerElement]
        Dictionary that allows to get a controller's knob by its id.
    """

    def __init__(
        self,
        knobs: List[ControllerElement],
        knob_binds: List[KnobBind],
        actions: List[str],
        connected_controller: ConnectedController,
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

        self.connected_controller = connected_controller

        self.actions = [""] + actions
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

        self.flashing_knobs = set([])
        self.thread_list = []
        self.knobs_mutex = QMutex()

    def _light_up_knob(self, knob_id: int):
        if self.connected_controller is None:
            raise Exception("No controller connected.")

        def light_up_func():
            self.connected_controller.flash_knob(knob_id)

        thread = LightUpQThread(
            light_up_func,
            self.knobs_mutex,
            knob_id,
            self.flashing_knobs,
        )

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

        # SearchableQComboBox for action selection.
        increase_action_combo = SearchableQComboBox(self.actions, action_increase, self)
        decrease_action_combo = SearchableQComboBox(self.actions, action_decrease, self)
        self.knob_combos.append((knob_id, increase_action_combo, decrease_action_combo))

        # Button for lighting up the controller element
        controller_disconnected = self.connected_controller is None
        light_up_knob = QPushButton("Light up")
        light_up_knob.setToolTip(f"Lights up the '{knob_name}'")
        light_up_knob.setCursor(Qt.PointingHandCursor)
        light_up_knob.clicked.connect(lambda: self._light_up_knob(knob_id))

        sizes = [1, 1, 3, 5, 5]
        elems = [
            QLabel(knob_name),
            light_up_knob,
            QWidget(),
            increase_action_combo,
            decrease_action_combo,
        ]

        if controller_disconnected:
            sizes = [1, 4, 5, 5]
            del elems[1]

        # Layout.
        layout = QGridLayout()
        BindsEditor._add_elements_to_grid_layout(layout, elems, sizes)

        return layout

    def get_binds(self) -> List[KnobBind]:
        """Returns list of all binds currently set in this widget."""
        result = []
        for knob_id, increase_action_combo, decrease_action_combo in self.knob_combos:
            increase_action = increase_action_combo.currentText() or None
            decrease_action = decrease_action_combo.currentText() or None
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
        connected_controller: ConnectedController,
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
        layout.addLayout(radio_layout)
        layout.addLayout(buttons_layout)

        if connected_controller is None:
            layout.addWidget(QLabel("Connect controller to enable 'Light up' buttons."))

        layout.addWidget(self.knobs_widget)
        layout.addWidget(self.buttons_widget)

        self.setLayout(layout)
        self.setStyleSheet(get_current_stylesheet())
        self.knobs_radio.setChecked(True)
        self.setMinimumSize(830, 650)

    @staticmethod
    def _add_elements_to_grid_layout(
        layout: QGridLayout, elems: List[QLayoutItem], sizes: List[int]
    ) -> None:
        current_size = 0
        for elem, size in zip(elems, sizes):
            layout.addWidget(elem, 0, current_size, 1, size)
            current_size += size

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
