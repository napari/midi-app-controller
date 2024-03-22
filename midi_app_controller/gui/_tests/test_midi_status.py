import pytest
import os
import numpy
from PyQt5.QtTest import QTest
from qtpy.QtCore import Qt
from unittest.mock import MagicMock, patch
from napari.components import LayerList
from napari.layers import Image

from midi_app_controller.config import Config
from midi_app_controller.models.controller import Controller
from midi_app_controller.models.binds import Binds
from midi_app_controller.state.state_manager import SelectedItem


@pytest.fixture
def patch_rtmidi() -> tuple:
    midi_in_mock = MagicMock(name="MidiIn")
    midi_out_mock = MagicMock(name="MidiOut")

    with patch("rtmidi.MidiIn", new=midi_in_mock):
        with patch("rtmidi.MidiOut", new=midi_out_mock):
            from midi_app_controller.gui.midi_status import (
                state_manager,
                increase_opacity,
                decrease_opacity,
            )

            BASE_DIR = os.path.abspath(__file__)
            while os.path.basename(BASE_DIR) != "midi_app_controller":
                BASE_DIR = os.path.dirname(BASE_DIR)
            BASE_DIR = os.path.dirname(BASE_DIR)

            CONTROLLER_CONFIG_PATH = os.path.join(
                BASE_DIR, "config_files", "controllers", "x_touch_mini_example.yaml"
            )
            BINDS_CONFIG_PATH = os.path.join(
                BASE_DIR, "config_files", "binds", "x_touch_mini_test.yaml"
            )

            state_manager.selected_controller = SelectedItem(
                "X_TOUCH_MINI", CONTROLLER_CONFIG_PATH
            )
            state_manager.selected_binds = SelectedItem("TestBinds", BINDS_CONFIG_PATH)
            state_manager.selected_midi_in = "Midi Through:Midi Through Port-0 14:0"
            state_manager.selected_midi_out = "Midi Through:Midi Through Port-0 14:0"

            binds = Binds.load_all_from(Config.BINDS_DIRECTORY)
            binds_names = [b.name for b, _ in binds]
            controller = Controller.load_all_from(Config.CONTROLLERS_DIRECTORY)
            controller_names = [c.name for c, _ in controller]
            state_manager.get_available_binds = MagicMock(return_value=binds_names)
            state_manager.get_available_controllers = MagicMock(
                return_value=controller_names
            )
            yield (
                state_manager,
                binds_names,
                controller_names,
                increase_opacity,
                decrease_opacity,
            )


@pytest.fixture
def midi_status_fixture(qtbot, patch_rtmidi):
    from midi_app_controller.gui.midi_status import MidiStatus

    widget = MidiStatus()
    qtbot.addWidget(widget)
    widget.show()
    return widget


def test_start_stop_handling_updates_status_label(midi_status_fixture, qtbot):
    assert midi_status_fixture.status.text() == "Not running"
    qtbot.mouseClick(midi_status_fixture.start_handling_button, Qt.LeftButton)
    QTest.qWait(100)
    assert midi_status_fixture.status.text() == "Running"
    qtbot.mouseClick(midi_status_fixture.stop_handling_button, Qt.LeftButton)
    QTest.qWait(100)
    assert midi_status_fixture.status.text() == "Not running"


def test_controller_and_binds_selection_changes(
    qtbot, midi_status_fixture, patch_rtmidi
):
    state_manager, binds_names, controller_names, _, _ = patch_rtmidi
    initial_controller = midi_status_fixture.current_controller.currentText()
    initial_binds = midi_status_fixture.current_binds.currentText()

    assert initial_controller == ""
    assert initial_binds == ""

    qtbot.mouseClick(midi_status_fixture.current_controller, Qt.LeftButton)
    QTest.qWait(100)
    qtbot.mouseClick(midi_status_fixture.current_binds, Qt.LeftButton)
    QTest.qWait(100)

    updated_controller = midi_status_fixture.current_controller.currentText()
    updated_binds = midi_status_fixture.current_binds.currentText()

    assert updated_controller == controller_names[0]
    assert updated_binds == binds_names[0]


@pytest.mark.parametrize(
    "initial_opacity, expected_opacity, action",
    [
        (0.5, 0.49, "decrease_opacity"),
        (0, 0, "decrease_opacity"),
        (0.5, 0.51, "increase_opacity"),
        (1, 1, "increase_opacity"),
    ],
)
def test_opacity_changes(initial_opacity, expected_opacity, action, patch_rtmidi):
    if action == "decrease_opacity":
        action = patch_rtmidi[-1]
    else:
        action = patch_rtmidi[-2]

    ll = LayerList()

    layer = Image(numpy.random.random((10, 10)), opacity=initial_opacity)
    ll.append(layer)
    ll.selection.add(layer)

    action(ll)
    assert layer.opacity == expected_opacity


def test_init_select_controller_updates_state_and_resets_binds(
    midi_status_fixture, patch_rtmidi
):
    state_manager, binds_names, controller_names, _, _ = patch_rtmidi
    binds0 = state_manager.selected_binds
    midi_status_fixture.current_controller.textActivated.emit(controller_names[0])
    x = state_manager.selected_controller.name
    binds1 = state_manager.selected_binds
    midi_status_fixture.current_controller.textActivated.emit(controller_names[1])
    y = state_manager.selected_controller.name
    binds2 = state_manager.selected_binds

    assert binds0 and binds0.name == "TestBinds"
    assert binds1 is None
    assert binds2 is None
    assert x == controller_names[0]
    assert y == controller_names[1]


def test_edit_binds(midi_status_fixture, patch_rtmidi):
    state_manager, binds_names, controller_names, _, _ = patch_rtmidi
    midi_status_fixture.current_binds.textActivated.emit(binds_names[1])
    assert state_manager.selected_binds.name == binds_names[1]
    midi_status_fixture.current_binds.textActivated.emit(binds_names[0])
    assert state_manager.selected_binds.name == binds_names[0]
