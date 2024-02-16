from typing import Callable, List

# TODO Move style somewhere else to make this class independent from napari.
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
    def __init__(
        self,
        buttons: List[ControllerElement],
        button_binds: List[ButtonBind],
        actions: List[str],
    ):
        super().__init__()

        self.actions = [""] + actions
        self.button_menus = []
        self.binds_dict = {b.button_id: b for b in button_binds}

        self.layout = QVBoxLayout()

        description_layout = QHBoxLayout()
        description_layout.addWidget(QLabel("Name:"))
        description_layout.addWidget(QLabel("Action when clicked:"))
        self.layout.addLayout(description_layout)

        button_list = QWidget()
        self.button_layout = QVBoxLayout()
        for elem in buttons:
            self._create_button_entry(elem.id, elem.name)
        self.button_layout.addStretch()
        button_list.setLayout(self.button_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(button_list)
        self.layout.addWidget(scroll)

        self.layout.addStretch()
        self.setLayout(self.layout)

    def _create_button_entry(self, button_id: int, button_name: str) -> None:
        if (bind := self.binds_dict.get(button_id)) is not None:
            action = bind.action_id
        else:
            action = None

        button_action = QPushButton(action)
        button_action.setMenu(self._create_action_menu(button_action))

        layout = QHBoxLayout()
        layout.addWidget(QLabel(button_name))
        layout.addWidget(button_action)
        self.button_layout.addLayout(layout)

        self.button_menus.append((button_id, button_action))

    def _create_action_menu(self, button: QPushButton) -> QMenu:
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { menu-scrollable: 1; }")
        for action in self.actions:
            menu.addAction(action, lambda action=action: button.setText(action))
        return menu

    def get_binds(self) -> List[ButtonBind]:
        result = []
        for button_id, button in self.button_menus:
            action = button.text() or None
            if action is not None:
                result.append(ButtonBind(button_id=button_id, action_id=action))
        return result


class KnobBinds(QWidget):
    def __init__(
        self,
        knobs: List[ControllerElement],
        knob_binds: List[KnobBind],
        actions: List[str],
    ):
        super().__init__()

        self.actions = [""] + actions
        self.knob_menus = []
        self.binds_dict = {b.knob_id: b for b in knob_binds}

        self.layout = QVBoxLayout()

        description_layout = QHBoxLayout()
        description_layout.addWidget(QLabel("Name:"))
        description_layout.addWidget(QLabel("Action when increased:"))
        description_layout.addWidget(QLabel("Action when decreased:"))
        self.layout.addLayout(description_layout)

        knob_list = QWidget()
        self.knob_layout = QVBoxLayout()
        for elem in knobs:
            self._create_knob_entry(elem.id, elem.name)
        self.knob_layout.addStretch()
        knob_list.setLayout(self.knob_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(knob_list)
        self.layout.addWidget(scroll)

        self.layout.addStretch()
        self.setLayout(self.layout)

    def _create_action_menu(self, knob: QPushButton) -> QMenu:
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { menu-scrollable: 1; }")
        for action in self.actions:
            menu.addAction(action, lambda action=action: knob.setText(action))
        return menu

    def _create_knob_entry(self, knob_id: int, knob_name: str) -> None:
        if (bind := self.binds_dict.get(knob_id)) is not None:
            action_increase = bind.action_id_increase
            action_decrease = bind.action_id_decrease
        else:
            action_increase = ""
            action_decrease = ""

        knob_increase = QPushButton(action_increase)
        knob_increase.setMenu(self._create_action_menu(knob_increase))
        knob_decrease = QPushButton(action_decrease)
        knob_decrease.setMenu(self._create_action_menu(knob_decrease))

        layout = QHBoxLayout()
        layout.addWidget(QLabel(knob_name))
        layout.addWidget(knob_increase)
        layout.addWidget(knob_decrease)

        self.knob_layout.addLayout(layout)
        self.knob_menus.append((knob_id, knob_increase, knob_decrease))

    def get_binds(self) -> List[KnobBind]:
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
    def __init__(
        self,
        controller: Controller,
        binds: Binds,
        actions: List[str],
        save_binds: Callable[[List[KnobBind], List[ButtonBind]], None],
    ):
        super().__init__()

        self.save_binds = save_binds

        self.save_and_exit_button = QPushButton("Save and exit")
        self.save_and_exit_button.clicked.connect(self._save_and_exit)
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self._exit)

        self.knobs_radio = QRadioButton("Knobs")
        self.buttons_radio = QRadioButton("Buttons")
        self.knobs_radio.toggled.connect(self._on_radio_toggled)
        self.buttons_radio.toggled.connect(self._on_radio_toggled)

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

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.knobs_radio)
        radio_layout.addWidget(self.buttons_radio)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.save_and_exit_button)
        buttons_layout.addWidget(self.exit_button)

        layout = QVBoxLayout()
        layout.addLayout(radio_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.knobs_widget)
        layout.addWidget(self.buttons_widget)

        self.setLayout(layout)
        self.setStyleSheet(get_current_stylesheet())
        self.knobs_radio.setChecked(True)

        self.setMinimumSize(500, 550)

    def _on_radio_toggled(self, checked):
        if not checked:
            return
        if self.knobs_radio.isChecked():
            self.buttons_widget.hide()
            self.knobs_widget.show()
        else:
            self.knobs_widget.hide()
            self.buttons_widget.show()

    def _save_and_exit(self):
        knob_binds = self.knobs_widget.get_binds()
        button_binds = self.buttons_widget.get_binds()
        self.save_binds(knob_binds, button_binds)
        self.close()

    def _exit(self):
        self.close()
