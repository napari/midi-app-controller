import os
import sys
import pathlib
from typing import List

from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

from midi_app_controller.models.binds import ButtonBind, KnobBind, Binds
from midi_app_controller.models.controller import Controller
from midi_app_controller.gui.binds_editor import BindsEditor


class MidiStatus(QWidget):
    """Widget that allows to select currently used controller, binds, etc."""

    def __init__(self):
        super().__init__()

        self.button = QPushButton("Edit binds")
        self.button.clicked.connect(self.on_button_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)

    def on_button_clicked(self):
        # TODO Open real config files. It must wait until state manager is merged.
        current_path = pathlib.Path(__file__).parent.resolve()
        controller_path = os.path.join(current_path, "sample_controller.yaml")
        binds_path = os.path.join(current_path, "sample_binds.yaml")

        controller = Controller.load_from(controller_path)
        binds = Binds.load_from(binds_path)

        def save(knob_binds: List[KnobBind], button_binds: List[ButtonBind]) -> None:
            print(knob_binds)
            print(button_binds)
            binds.knob_binds = knob_binds
            binds.button_binds = button_binds
            binds.save_to(binds_path)

        from napari._app_model import get_app

        actions = list(map(lambda x: x[0], list(get_app().commands)))

        editor_dialog = BindsEditor(
            controller,
            binds,
            actions,
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
