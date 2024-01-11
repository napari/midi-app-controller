import sys
from pathlib import Path
from app_model.types import Action
import yaml
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMainWindow, QAction, QHBoxLayout, \
    QDial, QComboBox, QFormLayout, QMenuBar
from midi_app_controller.actions.bound_controller import BoundController, ButtonActions, KnobActions
from midi_app_controller.models.binds import ButtonBind, KnobBind, Binds


class MIDIControllerView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.loadSettings()

    def ui_action_to_model_action(self, action_name: str):
        """
        Converts an action name to a model Action.

        Parameters
        ----------
        action_name: str
            Name of the action.

        Returns
        -------
        Action
            An instance of Action with the given name.
        """

        if action_name == 'None':
            return None
        return Action(id=action_name, callback="", title=action_name)

    def setupUI(self):
        """
        Sets up the UI.
        """

        self.createCentralWidget()
        self.createMenuBar()
        self.layoutControls()
        self.setWindowTitle('MIDI Controller')

    def createCentralWidget(self):
        """
        Creates the central widget.
        """

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setStyleSheet("background-color: #2e2e2e;")

    def createMenuBar(self):
        """
        Creates the menu bar.
        """

        menubar = self.menuBar()
        self.addMenuAction(menubar, 'Save Settings', self.saveSettings)
        self.addMenuAction(menubar, 'Load Settings', self.loadSettings)

    def addMenuAction(self, menu: QMenuBar, title: str, method: callable):
        """
        Adds an action to the menu.

        Parameters
        ----------
        menu: QMenuBar
            Menu to add the action to.
        title: str
            Title of the action.
        method: callable
            Method to be called when the action is triggered.
        """

        action = QAction(title, self)
        action.triggered.connect(method)
        menu.addAction(action)

    def layoutControls(self):
        """
        Lays out the controls.
        """

        self.dials, self.buttons = [], []
        self.control_to_action, self.control_to_combo_box = {}, {}

        self.main_layout.addLayout(self.createDialsLayout(17, 24))
        self.main_layout.addLayout(self.createButtonsLayout(1, 8))
        self.main_layout.addLayout(self.createButtonsLayout(9, 16))
        self.createActionAssignmentForm()

    def createDialsLayout(self, start: int, end: int):
        """
        Creates the layout for the dials.

        Parameters
        ----------
        start: int
        end: int

        Returns
        -------
        QHBoxLayout
            An instance of QHBoxLayout containing the dials.
        """

        layout = QHBoxLayout()
        for i in range(start, end + 1):
            layout.addWidget(self.createDial(i))
        return layout

    def createDial(self, index: int):
        """
        Creates a dial.

        Parameters
        ----------
        index: int
            Index of the dial.

        Returns
        -------
        QDial
            An instance of QDial with the given index.
        """

        dial = QDial()
        dial.setObjectName(f"Dial_{index + 1}")
        dial.setNotchesVisible(True)
        dial.setStyleSheet(self.getDefaultStyle())
        self.dials.append(dial)
        return dial

    def createButtonsLayout(self, start: int, end: int):
        """
        Creates the layout for the buttons.

        Parameters
        ----------
        start: int
            Start index of the buttons.
        end: int
            End index of the buttons.

        Returns
        -------
        QHBoxLayout
            An instance of QHBoxLayout containing the buttons.
        """

        layout = QHBoxLayout()
        for i in range(start, end + 1):
            layout.addWidget(self.createButton(i))
        return layout

    def createButton(self, index: int):
        """
        Creates a button.

        Parameters
        ----------
        index: int
            Index of the button.
        Returns
        -------
        QPushButton
            An instance of QPushButton with the given index.
        """

        button = QPushButton(f"Button {index}")
        button.setObjectName(f"Button_{index}")
        button.setStyleSheet(self.getDefaultStyle())
        self.buttons.append(button)
        return button

    def createActionAssignmentForm(self):
        """
        Creates the form for assigning actions to controls.
        """

        layout = QFormLayout()
        self.actions = [f'Action {i + 1}' for i in range(16)]

        for control in self.dials + self.buttons:
            assignments = self.createActionAssignment(control)
            if isinstance(assignments[0], tuple):
                for assignment in assignments:
                    layout.addRow(*assignment)
            else:
                layout.addRow(*assignments)

        self.main_layout.addLayout(layout)

    def createActionAssignment(self, control: QWidget):
        """
        Creates an action assignment for a control.

        Parameters
        ----------
        control: QWidget
            Control to create the assignment for.

        Returns
        -------
            Action assignment tuple or a list of action assignment tuples.
        """

        if isinstance(control, QDial):
            return [self.createDialAssignment(control, action_type) for action_type in ['increase', 'decrease']]
        else:
            return self.createButtonAssignment(control)

    def createDialAssignment(self, dial: QDial, action_type: str):
        """
        Creates an action assignment for a dial.

        Parameters
        ----------
        dial: QDial
            Dial to create the assignment for.
        action_type:
            Type of the action (increase or decrease).
        Returns
        -------
        label, combo
            A label and the combo box.
        """

        label = QLabel(f'{dial.objectName()} {action_type}:')
        combo = self.createActionCombo(dial, action_type)
        return label, combo

    def createButtonAssignment(self, button: QPushButton):
        """
        Creates an action assignment for a button.

        Parameters
        ----------
        button: QPushButton

        Returns
        -------
        label, combo
            A label and the combo box.
        """

        label = QLabel(f'{button.objectName()}:')
        combo = self.createActionCombo(button)
        return label, combo

    def createActionCombo(self, control: QWidget, action_type: str = None):
        """
        Creates a combo box for assigning an action to a control.

        Parameters
        ----------
        control: QWidget
            Control to create the combo box for.
        action_type: str
            Type of the action (increase or decrease).
        Returns
        -------
        QComboBox
            An instance of QComboBox containing the actions.
        """

        combo = QComboBox()
        combo.addItems(['None'] + self.actions)
        combo.currentIndexChanged.connect(
            lambda index, c=control, cb=combo, at=action_type: self.assignAction(c, cb, at))
        self.control_to_combo_box[
            f'{control.objectName()}_{action_type}' if action_type else control.objectName()] = combo
        return combo

    def assignAction(self, control: QWidget, combo_box: QComboBox, action_type: str = None):
        """
        Assigns an action to a control.

        Parameters
        ----------
        control: QWidget
            Control to assign the action to.
        combo_box:
            Combo box containing the action.
        action_type:
            Type of the action (increase or decrease).
        """

        selected_action = combo_box.currentText()
        control_key = f'{control.objectName()}_{action_type}' if action_type else control.objectName()

        if selected_action != 'None':
            self.control_to_action[control_key] = selected_action
        elif control_key in self.control_to_action:
            del self.control_to_action[control_key]

        self.updateControlStyle(control)

    def updateControlStyle(self, control: QWidget):
        """
        Updates the style of a control.
        Parameters
        ----------
        control:
            Control to update the style of.
        """

        control_key = control.objectName()

        if isinstance(control, QDial):
            control_key_increase = f'{control_key}_increase'
            control_key_decrease = f'{control_key}_decrease'
            if control_key_increase in self.control_to_action or control_key_decrease in self.control_to_action:
                control.setStyleSheet(self.getHighlightedStyle())
            else:
                control.setStyleSheet(self.getDefaultStyle())
        else:
            if control_key in self.control_to_action:
                control.setStyleSheet(self.getHighlightedStyle())
            else:
                control.setStyleSheet(self.getDefaultStyle())

    @staticmethod
    def getDefaultStyle():
        return """
            QPushButton, QDial {
                background-color: #444;
                color: white;
                padding: 10px;
            }
        """

    @staticmethod
    def getHighlightedStyle():
        return """
            QPushButton, QDial {
                background-color: #ff8c00;
                color: white;
                padding: 10px;
            }
        """

    def saveSettings(self):
        """
        Saves the settings to a file.
        """

        button_binds = []

        bound_buttons = {}
        for button_id, action_name in self.control_to_action.items():
            if 'Button' in button_id:
                model_action = self.ui_action_to_model_action(action_name)
                if model_action is not None:
                    button_id_num = int(button_id.split('_')[1])
                    bound_buttons[button_id_num] = ButtonActions(action_press=model_action)
                    button_bind = ButtonBind(button_id=button_id_num, action_id=model_action.id)
                    button_binds.append(button_bind)

        bound_knobs = {}
        for knob_key, action_name in self.control_to_action.items():
            if 'Dial' in knob_key:
                _, knob_id, action_type = knob_key.split('_')
                knob_id = int(knob_id)
                model_action = self.ui_action_to_model_action(action_name)
                if model_action is not None:
                    if knob_id not in bound_knobs:
                        bound_knobs[knob_id] = KnobActions(action_increase=None, action_decrease=None)
                    if action_type == 'increase':
                        bound_knobs[knob_id].action_increase = model_action
                    elif action_type == 'decrease':
                        bound_knobs[knob_id].action_decrease = model_action

        knob_binds = [
            KnobBind(knob_id=k, action_id_increase=v.action_increase.id if v.action_increase else None,
                     action_id_decrease=v.action_decrease.id if v.action_decrease else None)
            for k, v in bound_knobs.items()]

        self.binds = Binds(name='Default', description='Default binds', app_name='Default', controller_name='Default',
                           button_binds=button_binds, knob_binds=knob_binds)
        self.binds.save_to(Path('settings.yaml'))

    def loadSettings(self):
        """
        Loads the settings from a file.
        """

        try:
            self.binds = Binds.load_from(Path('settings.yaml'))

            for button_bind in self.binds.button_binds:
                action = button_bind.action_id
                button_id = button_bind.button_id
                self.control_to_combo_box[f'Button_{button_id}'].setCurrentText(action)

            for knob_bind in self.binds.knob_binds:
                action_increase = knob_bind.action_id_increase if knob_bind.action_id_increase else 'None'
                action_decrease = knob_bind.action_id_decrease if knob_bind.action_id_decrease else 'None'
                knob_id = knob_bind.knob_id
                self.control_to_combo_box[f'Dial_{knob_id}_increase'].setCurrentText(action_increase)
                self.control_to_combo_box[f'Dial_{knob_id}_decrease'].setCurrentText(action_decrease)

        except FileNotFoundError:
            print("Settings file not found.")

        except yaml.YAMLError as e:
            print(f"Error reading settings: {e}")


def main():
    view = MIDIControllerView()
    view.show()

# def main():
#     app = QApplication(sys.argv)
#     view = MIDIControllerView()
#     view.show()
#     sys.exit(app.exec_())
#
#
# if __name__ == '__main__':
#     main()
