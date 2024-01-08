import json
import sys

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMainWindow, QAction, QHBoxLayout, \
    QDial, QComboBox, QFormLayout, QToolBar


class OpeningScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        exitAction = QAction('&Exit', self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        button_option1 = QPushButton('Show View 1', self)
        button_option2 = QPushButton('Show View 2', self)

        button_option1.setStyleSheet("background-color: lightgray; font-size: 16px;")
        button_option2.setStyleSheet("background-color: lightgray; font-size: 16px;")

        button_option1.clicked.connect(self.showView1)
        button_option2.clicked.connect(self.showView2)

        layout = QVBoxLayout()
        layout.addWidget(button_option1)
        layout.addWidget(button_option2)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.setWindowTitle('Opening Screen')
        self.setGeometry(300, 300, 400, 200)

    def showView1(self):
        self.hide()
        view1 = View1()
        view1.show()

    def showView2(self):
        self.hide()
        view2 = View2()
        view2.show()


class View1(QMainWindow):
    def __init__(self):
        super().__init__()
        self.control_to_action = {}
        self.dials = []
        self.buttons = []
        self.action_controls = {}

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.initUI()
        self.selected_controls = set()

    def dial_used(self, dial):
        print(f"Dial {dial.objectName()} used with value {dial.value()}")

    def setupMenu(self):
        menubar = self.menuBar()

        save_action = QAction('Save Settings', self)
        save_action.triggered.connect(self.save_settings)
        menubar.addAction(save_action)

        load_action = QAction('Load Settings', self)
        load_action.triggered.connect(self.load_settings)
        menubar.addAction(load_action)

    def initUI(self):
        self.setStyleSheet("background-color: #2e2e2e;")
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setupMenu()

        dials_layout = QHBoxLayout()
        for i in range(8):
            dial = QDial()
            dial.setObjectName(f"Dial_{i + 1}")
            dial.setNotchesVisible(True)
            dial.setStyleSheet("""
                QDial { background-color: #333; }
                QDial::handle { background: #ff8c00; }
            """)
            dial.valueChanged.connect(lambda value, d=dial: self.dial_used(d))
            self.dials.append(dial)
            dials_layout.addWidget(dial)
        self.main_layout.addLayout(dials_layout)

        button_style = """
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                padding: 10px;
                min-height: 40px;
                border-radius: 5px;
            }
            QPushButton:pressed {
                background-color: #ff8c00;
            }
        """
        pressed_button_style = "QPushButton { background-color: #ff8c00; }"

        first_row_buttons_layout = QHBoxLayout()
        for i in range(8):
            button = QPushButton(f"Button {i + 1}")
            button.setObjectName(f"Button_{i + 1}")
            button.setStyleSheet(button_style)
            self.buttons.append(button)
            first_row_buttons_layout.addWidget(button)
        self.main_layout.addLayout(first_row_buttons_layout)

        second_row_buttons_layout = QHBoxLayout()
        for i in range(8):
            button = QPushButton(f"Button {i + 9}")
            button.setObjectName(f"Button_{i + 9}")
            button.setStyleSheet(button_style)
            self.buttons.append(button)
            second_row_buttons_layout.addWidget(button)
        self.main_layout.addLayout(second_row_buttons_layout)

        self.create_action_assignment_form()

        self.setLayout(self.main_layout)
        self.setWindowTitle('View 1')

    def create_action_assignment_form(self):
        action_assignment_layout = QFormLayout()
        self.actions = [f'Action {i + 1}' for i in range(5)]
        self.control_to_action = {}  # Maps control to its combo box

        for control in self.dials + self.buttons:
            control_label = QLabel(f'{control.objectName()}:')
            action_combo = QComboBox()
            action_combo.addItems(['None'] + self.actions)
            action_combo.currentIndexChanged.connect(
                lambda index, c=control, cb=action_combo: self.assign_action(c, cb))
            action_assignment_layout.addRow(control_label, action_combo)
            self.control_to_action[
                control.objectName()] = action_combo  # Store the combo box with control's name as key

        self.main_layout.addLayout(action_assignment_layout)

    def save_settings(self):
        settings = {}
        for control_name, combo_box in self.control_to_action.items():
            if isinstance(combo_box, QComboBox):  # Ensure it is a QComboBox
                action = combo_box.currentText()
                settings[control_name] = action

        with open('settings.json', 'w') as file:
            json.dump(settings, file)

    def load_settings(self):
        try:
            with open('settings.json', 'r') as file:
                settings = json.load(file)

            for control_name, action in settings.items():
                if control_name in self.control_to_action:
                    combo_box = self.control_to_action[control_name]
                    combo_box.setCurrentText(action)

        except FileNotFoundError:
            print("Settings file not found.")
        except json.JSONDecodeError:
            print("Error reading settings.")

    def assign_action(self, control, combo_box):
        selected_action = combo_box.currentText()
        self.control_to_action[control] = selected_action

        if selected_action != 'None':
            control.setStyleSheet(self.get_highlighted_style(control))
        else:
            control.setStyleSheet(self.get_default_style(control))

    def get_default_style(self, control):
        if isinstance(control, QPushButton):
            return """
                QPushButton {
                    background-color: #444;
                    color: white;
                    border: none;
                    padding: 10px;
                    min-height: 40px;
                    border-radius: 5px;
                }
            """
        elif isinstance(control, QDial):
            return """
                QDial { background-color: #333; }
                QDial::handle { background: #333; }
            """

    def get_highlighted_style(self, control):
        if isinstance(control, QPushButton):
            return """
                QPushButton {
                    background-color: #ff8c00;
                    color: white;
                    border: none;
                    padding: 10px;
                    min-height: 40px;
                    border-radius: 5px;
                }
            """
        elif isinstance(control, QDial):
            return """
                QDial { background-color: #ff8c00; }
                QDial::handle { background: #ff8c00; }
            """

    def highlight_control(self, combo_box):
        unpressed_button_style = """
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                padding: 10px;
                min-height: 40px;
                border-radius: 5px;
            }
        """
        pressed_button_style = """
            QPushButton {
                background-color: #ff8c00;
                color: white;
                border: none;
                padding: 10px;
                min-height: 40px;
                border-radius: 5px;
            }
        """
        unpressed_dial_style = "QDial { background-color: #333; } QDial::handle { background: #333; }"
        pressed_dial_style = "QDial { background-color: #ff8c00; border: 2px solid blue; } QDial::handle { background: #ff8c00; }"

        selected_control = combo_box.currentText()

        if self.action_controls[combo_box]:
            self.selected_controls.discard(self.action_controls[combo_box])

        if selected_control != 'None':
            self.selected_controls.add(selected_control)

        for i, button in enumerate(self.buttons):
            btn_name = button.getObjectName()
            button.setStyleSheet(pressed_button_style if btn_name in self.selected_controls else unpressed_button_style)

        for i, dial in enumerate(self.dials):
            dial_name = dial.getObjectName()
            dial.setStyleSheet(pressed_dial_style if dial_name in self.selected_controls else unpressed_dial_style)

        self.action_controls[combo_box] = selected_control


class View2(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        label = QLabel('View 2', self)
        layout.addWidget(label)

        self.setLayout(layout)
        self.setWindowTitle('View 2')


def main():
    app = QApplication(sys.argv)
    opening_screen = OpeningScreen()
    opening_screen.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
