import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMainWindow, QAction, QMenuBar

class OpeningScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Create a menu bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')

        # Create an "Exit" action for the "File" menu
        exitAction = QAction('Exit', self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        # Create buttons for different options
        button_option1 = QPushButton('Option 1', self)
        button_option2 = QPushButton('Option 2', self)

        # Connect buttons to functions
        button_option1.clicked.connect(self.showView1)
        button_option2.clicked.connect(self.showView2)

        layout = QVBoxLayout()
        layout.addWidget(button_option1)
        layout.addWidget(button_option2)

        # Set layout as central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.setWindowTitle('Opening Screen')

    def showView1(self):
        self.hide()  # Hide the current window
        view1 = View1()
        view1.show()

    def showView2(self):
        self.hide()  # Hide the current window
        view2 = View2()
        view2.show()

class View1(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        label = QLabel('View 1', self)
        layout.addWidget(label)

        self.setLayout(layout)
        self.setWindowTitle('View 1')

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
