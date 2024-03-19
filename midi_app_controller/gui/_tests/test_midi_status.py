import pytest

from midi_app_controller.config import Config
import os
from midi_app_controller.models.controller import Controller
from midi_app_controller.models.binds import Binds
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock, patch
from midi_app_controller.state.state_manager import SelectedItem


midi_in_mock = MagicMock(name='MidiIn')
midi_out_mock = MagicMock(name='MidiOut')

# Zastosuj patch na poziomie modułu
patcher_midi_in = patch('rtmidi.MidiIn', new=midi_in_mock)
patcher_midi_out = patch('rtmidi.MidiOut', new=midi_out_mock)

# Uruchom patch przed importowaniem modułów
patcher_midi_in.start()
patcher_midi_out.start()


from midi_app_controller.gui.midi_status import state_manager, MidiStatus, decrease_opacity, increase_opacity


BASE_DIR = os.path.abspath(__file__)
while os.path.basename(BASE_DIR) != 'midi_app_controller':
    BASE_DIR = os.path.dirname(BASE_DIR)
BASE_DIR = os.path.dirname(BASE_DIR)

CONTROLLER_CONFIG_PATH = os.path.join(BASE_DIR, 'config_files', 'controllers', 'x_touch_mini_example.yaml')
BINDS_CONFIG_PATH = os.path.join(BASE_DIR, 'config_files', 'binds', 'x_touch_mini_test.yaml')

state_manager.selected_controller = SelectedItem("X_TOUCH_MINI", CONTROLLER_CONFIG_PATH)
state_manager.selected_binds = SelectedItem("TestBinds", BINDS_CONFIG_PATH)
state_manager.selected_midi_in = state_manager._midi_in.get_ports()[0]
state_manager.selected_midi_in = 'Midi Through:Midi Through Port-0 14:0'
state_manager.selected_midi_out = state_manager._midi_out.get_ports()[0]
state_manager.selected_midi_out = 'Midi Through:Midi Through Port-0 14:0'

binds = Binds.load_all_from(Config.BINDS_DIRECTORY)
binds_names = [b.name for b, _ in binds]
controller = Controller.load_all_from(Config.CONTROLLERS_DIRECTORY)
controller_names = [c.name for c, _ in controller]
state_manager.get_available_binds = MagicMock(return_value=binds_names)
state_manager.get_available_controllers = MagicMock(return_value=controller_names)


@pytest.fixture
def midi_status_fixture(qtbot):
    widget = MidiStatus()
    qtbot.addWidget(widget)
    return widget


def test_start_stop_handling_updates_status_label(midi_status_fixture, qtbot):
    assert midi_status_fixture.status.text() == "Not running"
    qtbot.mouseClick(midi_status_fixture.start_handling_button, Qt.LeftButton)
    assert midi_status_fixture.status.text() == "Running"
    qtbot.mouseClick(midi_status_fixture.stop_handling_button, Qt.LeftButton)
    assert midi_status_fixture.status.text() == "Not running"


def test_controller_and_binds_selection_changes(qtbot, midi_status_fixture):
    initial_controller = midi_status_fixture.current_controller.currentText()
    initial_binds = midi_status_fixture.current_binds.currentText()

    assert initial_controller == ''
    assert initial_binds == ''

    qtbot.mouseClick(midi_status_fixture.current_controller, Qt.LeftButton)
    qtbot.mouseClick(midi_status_fixture.current_binds, Qt.LeftButton)

    updated_controller = midi_status_fixture.current_controller.currentText()
    updated_binds = midi_status_fixture.current_binds.currentText()

    assert updated_controller == controller_names[0]
    assert updated_binds == binds_names[0]


def test_decrease_opacity():
    from napari.components import LayerList
    from napari.layers import Image

    ll = LayerList()
    import numpy
    layer = Image(numpy.random.random((10, 10)), opacity=0.5)
    ll.append(layer)
    ll.selection.add(layer)
    decrease_opacity(ll)
    assert layer.opacity == 0.49


def test_increase_opacity():
    from napari.components import LayerList
    from napari.layers import Image

    ll = LayerList()
    import numpy
    layer = Image(numpy.random.random((10, 10)), opacity=0.5)
    ll.append(layer)
    ll.selection.add(layer)
    increase_opacity(ll)
    assert layer.opacity == 0.51


def test_init_select_controller_updates_state_and_resets_binds(midi_status_fixture, qtbot):
    x = state_manager.selected_controller.name
    qtbot.mouseClick(midi_status_fixture.current_controller, Qt.LeftButton)
    qtbot.keyClick(midi_status_fixture.current_controller, Qt.Key_Down)
    y = state_manager.selected_controller.name
    assert x == controller_names[0]
    assert y == controller_names[1]
