import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QMenu, QAction, QMainWindow, QFileDialog, QPushButton, QDialog, QDialogButtonBox
from PyQt5.QtGui import QPixmap
import yaml

class OpeningScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        button_option1 = QPushButton('X Touch Mini', self)
        button_option2 = QPushButton('<some other controller>', self)
        button_option3 = QPushButton('Load from file...', self)

        button_option1.clicked.connect(self.showXTouchMini)
        button_option2.clicked.connect(self.showOtherController)
        button_option3.clicked.connect(self.loadConfig)

        layout.addWidget(button_option1)
        layout.addWidget(button_option2)
        layout.addWidget(button_option3)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: gray;")

        fileMenu = menubar.addMenu('File')
        fileMenu.setStyleSheet("background-color: darkgrey;")

        saveAction = QAction('Save', self)
        saveConfigAction = QAction('Save Configuration to a File', self)
        loadConfigAction = QAction('Load Configuration', self)
        createConfigAction = QAction('Create a New Configuration', self)
        exitAction = QAction('Exit', self)

        saveAction.triggered.connect(self.save)
        saveConfigAction.triggered.connect(self.saveConfig)
        loadConfigAction.triggered.connect(self.loadConfig)
        createConfigAction.triggered.connect(self.createConfig)
        exitAction.triggered.connect(self.close)

        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveConfigAction)
        fileMenu.addAction(loadConfigAction)
        fileMenu.addAction(createConfigAction)
        fileMenu.addAction(exitAction)

        self.setWindowTitle('Midi App Controller')
        self.setGeometry(0, 0, 300, 150)

    def showXTouchMini(self):
        layout = QVBoxLayout()

        image_label = QLabel(self)
        pixmap = QPixmap('./x_touch_mini.png')
        image_label.setPixmap(pixmap)
        image_label.setGeometry(10, 10, pixmap.width(), pixmap.height())

        layout.addWidget(image_label)

        x_touch_mini_widget = QWidget(self)
        x_touch_mini_widget.setLayout(layout)
        self.setCentralWidget(x_touch_mini_widget)

    def showOtherController(self):
        print("Other controller view")

    def save(self):
        print("Save")

    def saveConfig(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setOptions(options)
        file_dialog.setWindowTitle("Save Configuration File")
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_path, _ = file_dialog.getSaveFileName(self, "Save Configuration File", "", "Config Files (*.yaml);;All Files (*)")

        if file_path:
            config_data = {"message": "123"}
            with open(file_path, 'w') as file:
                yaml.dump(config_data, file, default_flow_style=False)
            print(f"Save Configuration. File Path: {file_path}")

    def loadConfig(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        file_dialog = QFileDialog()
        file_dialog.setOptions(options)
        file_dialog.setWindowTitle("Load Configuration File")
        file_path, _ = file_dialog.getOpenFileName(self, "Open Configuration File", "", "Config Files (*.yaml);;All Files (*)")

        if file_path:
            with open(file_path, 'r') as file:
                config_data = yaml.load(file, Loader=yaml.FullLoader)
                print(f"Load Configuration. File Path: {file_path}, Config Data: {config_data}")

    def createConfig(self):
        print("Create a New Configuration")

def main():
    app = QApplication(sys.argv)
    ex = OpeningScreen()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
