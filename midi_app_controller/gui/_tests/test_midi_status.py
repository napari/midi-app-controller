import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from qtpy.QtCore import Qt
from qtpy.QtTest import QTest
from qtpy.QtWidgets import QMessageBox

from midi_app_controller.gui.midi_status import get_state_manager, main
from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller
from midi_app_controller.state.state_manager import SelectedItem


@pytest.fixture(autouse=True)
def patch_rtmidi() -> tuple:
    midi_in_mock = MagicMock(name="MidiIn")
    midi_out_mock = MagicMock(name="MidiOut")

    with patch("rtmidi.MidiIn", new=midi_in_mock):  # noqa
        with patch("rtmidi.MidiOut", new=midi_out_mock):  # noqa
            state_manager = get_state_manager()
            state_manager.selected_midi_in = "Midi Through:Midi Through Port-0 14:0"
            state_manager.selected_midi_out = "Midi Through:Midi Through Port-0 14:0"

            binds = [
                SelectedItem(f"Binds {i + 1}", Path(f"/path/binds_{i + 1}.yaml"))
                for i in range(3)
            ]
            controllers = [
                SelectedItem(
                    f"Controller {i + 1}", Path(f"/path/controller_{i + 1}.yaml")
                )
                for i in range(3)
            ]
            state_manager.get_available_binds = MagicMock(return_value=binds)
            state_manager.get_available_controllers = MagicMock(
                return_value=controllers
            )

            yield (
                binds,
                controllers,
            )


def create_binds(path):
    path_str = str(path)
    match = re.search(r"binds_(\d+)\.yaml$", path_str)
    index = int(match.group(1))
    mock = MagicMock(spec=Binds)
    mock.name = f"Binds {index}"
    mock.controller_name = f"Controller {(index - 1) % 3 + 1}"
    mock.button_binds = []
    mock.knob_binds = []
    return mock


def create_controller(path):
    path_str = str(path)
    match = re.search(r"controller_(\d+)\.yaml$", path_str)
    index = match.group(1)
    mock = MagicMock(spec=Controller)
    mock.name = f"Controller {index}"
    mock.preferred_midi_in = "TestMidiIn"
    mock.preferred_midi_out = "TestMidiOut"
    mock.buttons = []
    mock.knobs = []
    mock.knob_value_min = 0
    mock.knob_value_max = 127
    return mock


@pytest.fixture(autouse=True)
def load_methods():
    with (
        patch(
            "midi_app_controller.models.binds.Binds.load_from", side_effect=create_binds
        ),
        patch(
            "midi_app_controller.models.controller.Controller.load_from",
            side_effect=create_controller,
        ),
    ):
        yield


@pytest.fixture(autouse=True)
def midi_status(qtbot, patch_rtmidi, load_methods):
    from midi_app_controller.gui.midi_status import MidiStatus

    widget = MidiStatus()
    qtbot.addWidget(widget)
    widget.show()
    return widget


def test_select_controller(midi_status, patch_rtmidi, qtbot):
    binds_names, controller_names = patch_rtmidi
    QTest.qWait(300)

    for i in range(len(controller_names)):
        QTest.qWait(300)
        qtbot.keyClicks(midi_status.current_controller, controller_names[i].name)
        QTest.qWait(300)
        selected_controller = get_state_manager().selected_controller.name
        assert selected_controller == controller_names[i].name


def test_copy_binds(midi_status, qtbot, patch_rtmidi):
    state_manager = get_state_manager()
    state_manager.copy_binds = MagicMock()
    state_manager.select_binds_path = MagicMock()
    binds_names, controller_names = patch_rtmidi

    qtbot.mouseClick(midi_status.copy_binds_button, Qt.LeftButton)
    QTest.qWait(300)

    assert not state_manager.copy_binds.called
    assert not state_manager.select_binds_path.called

    qtbot.keyClicks(midi_status.current_controller, controller_names[0].name)
    QTest.qWait(300)
    qtbot.keyClicks(midi_status.current_binds, binds_names[0].name)
    QTest.qWait(300)

    state_manager.copy_binds = MagicMock()
    state_manager.select_binds_path = MagicMock()

    qtbot.mouseClick(midi_status.copy_binds_button, Qt.LeftButton)

    state_manager.copy_binds.assert_called_once()
    state_manager.select_binds_path.assert_called_once()


def test_start_stop_handling(midi_status, qtbot, patch_rtmidi):
    qtbot.keyClicks(midi_status.current_controller, "Controller 1")
    QTest.qWait(300)
    qtbot.keyClicks(midi_status.current_binds, "Binds 1")

    QTest.qWait(300)
    assert midi_status.status.text() == "Not running"
    qtbot.mouseClick(midi_status.start_handling_button, Qt.LeftButton)
    QTest.qWait(300)
    assert midi_status.status.text() == "Running"
    qtbot.mouseClick(midi_status.stop_handling_button, Qt.LeftButton)
    QTest.qWait(300)
    assert midi_status.status.text() == "Not running"


@patch("midi_app_controller.gui.midi_status.BindsEditor")
def test_edit_binds(binds_editor_mock, midi_status, patch_rtmidi, qtbot):
    binds_names, controller_names = patch_rtmidi
    state_manager = get_state_manager()
    QTest.qWait(500)
    qtbot.keyClicks(midi_status.current_binds, "(none)")

    for i in range(len(binds_names)):
        QTest.qWait(500)
        qtbot.keyClicks(midi_status.current_binds, binds_names[i].name)
        QTest.qWait(500)

        assert state_manager.selected_binds.name == binds_names[i].name
        midi_status.edit_binds_button.click()
        QTest.qWait(500)
        assert binds_editor_mock.called
        assert (
            binds_editor_mock.call_args[0][0].name
            == state_manager.selected_controller.name
        )
        assert (
            binds_editor_mock.call_args[0][1].name == state_manager.selected_binds.name
        )


def test_edit_binds_exceptions(midi_status, patch_rtmidi):
    state_manager = get_state_manager()
    state_manager.selected_controller = None
    state_manager.selected_binds = None

    with pytest.raises(Exception, match="No controller selected."):
        midi_status._edit_binds()

    state_manager.selected_controller = SelectedItem(
        "test_controller", Path("test_path")
    )
    with pytest.raises(Exception, match="No binds selected."):
        midi_status._edit_binds()


def test_refresh(midi_status, patch_rtmidi):
    state_manager = get_state_manager()
    state_manager.is_running = MagicMock(return_value=True)
    midi_status.refresh()

    assert midi_status.status.text() == "Running"
    assert midi_status.start_handling_button.text() == "Restart handling"
    assert midi_status.stop_handling_button.isEnabled() is True


def test_select_binds(midi_status, patch_rtmidi):
    state_manager = get_state_manager()
    binds_names, _ = patch_rtmidi
    new_binds = SelectedItem(binds_names[2].name, Path(""))

    midi_status._select_binds(new_binds)
    assert state_manager.selected_binds == new_binds


@patch("midi_app_controller.gui.midi_status.BindsEditor")
def test_edit_binds_with_subpath(
    mock_binds_editor, load_methods, midi_status, patch_rtmidi, qtbot
):
    state_manager = get_state_manager()
    state_manager.connected_controller = MagicMock()

    qtbot.keyClicks(midi_status.current_controller, "Controller 1")
    QTest.qWait(300)
    qtbot.keyClicks(midi_status.current_binds, "Binds 1")
    QTest.qWait(300)

    controller = Controller.load_from(Path("/path/controller_1.yaml"))
    binds = Binds.load_from(Path("/path/binds_1.yaml"))

    midi_status._edit_binds()
    assert mock_binds_editor.called
    call_args = mock_binds_editor.call_args[0]

    assert call_args[0].name == controller.name
    assert call_args[1].name == binds.name


def test_main():
    with patch.object(sys, "exit") as mock_exit:  # noqa
        with patch("midi_app_controller.gui.midi_status.QApplication") as q_app:
            q_app.return_value = MagicMock()
            with patch("midi_app_controller.gui.midi_status.MidiStatus") as midi_status:
                main()
                midi_status.assert_called_once()
                mock_view_instance = midi_status.return_value
                assert mock_view_instance.show.called
                mock_exit.assert_called_once_with(q_app.return_value.exec_())


@patch(
    "midi_app_controller.gui.midi_status.QMessageBox.question",
    return_value=QMessageBox.Yes,
)
def test_delete_binds(mock_question, midi_status, patch_rtmidi, qtbot):
    state_manager = get_state_manager()
    state_manager.delete_binds = MagicMock()
    binds_names, controller_names = patch_rtmidi

    qtbot.keyClicks(midi_status.current_controller, controller_names[0].name)
    QTest.qWait(300)
    qtbot.keyClicks(midi_status.current_binds, binds_names[0].name)
    QTest.qWait(300)

    qtbot.mouseClick(midi_status.delete_binds_button, Qt.LeftButton)
    QTest.qWait(300)

    assert mock_question.called
    state_manager.delete_binds.assert_called_once()
