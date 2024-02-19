from unittest.mock import Mock, patch
from typing import List

from app_model import Application
from app_model.types import Action
import pytest

from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller
from ..state_manager import StateManager, SelectedItem


@pytest.fixture
def actions() -> List[Action]:
    return [
        Action(
            id="Action1",
            title="sdfgsdfg",
            callback=lambda: None,
        ),
        Action(
            id="incr",
            title="dfgssdfg",
            callback=lambda: None,
        ),
        Action(
            id="decr",
            title="sdfdfg",
            callback=lambda: None,
        ),
        Action(
            id="other",
            title="aaaasfd",
            callback=lambda: None,
        ),
    ]


@pytest.fixture
def binds() -> Binds:
    binds_data = {
        "name": "TestBinds",
        "description": "Test description",
        "app_name": "TestApp",
        "controller_name": "TestController",
        "button_binds": [{"button_id": 1, "action_id": "Action1"}],
        "knob_binds": [
            {
                "knob_id": 2,
                "action_id_increase": "incr",
                "action_id_decrease": "decr",
            }
        ],
    }
    return Binds(**binds_data)


@pytest.fixture
def controller() -> Controller:
    controller_data = {
        "name": "TestController",
        "button_value_off": 11,
        "button_value_on": 100,
        "knob_value_min": 33,
        "knob_value_max": 55,
        "buttons": [{"id": 0, "name": "Button1"}, {"id": 1, "name": "Button2"}],
        "knobs": [{"id": 2, "name": "Knob1"}, {"id": 3, "name": "Knob2"}],
    }
    return Controller(**controller_data)


@pytest.fixture
def state_manager(actions) -> StateManager:
    actions = actions
    app = Application.get_or_create("app123")
    return StateManager(actions, app)


@pytest.fixture
def mock_midi_in_out():
    with patch("rtmidi.MidiIn") as mock_in, patch("rtmidi.MidiOut") as mock_out:
        yield mock_in.return_value, mock_out.return_value


@pytest.fixture
def mock_binds_load(binds):
    with patch("midi_app_controller.models.binds.Binds.load_from") as mock_binds_load:
        mock_binds_load.return_value = binds
        yield mock_binds_load


@pytest.fixture
def mock_controller_load(controller):
    with patch(
        "midi_app_controller.models.controller.Controller.load_from"
    ) as mock_controller_load:
        mock_controller_load.return_value = controller
        yield mock_controller_load


def test_selected_item():
    item = SelectedItem("name", "path")

    assert item.name == "name"
    assert item.path == "path"


@pytest.mark.parametrize("ports", [[], ["in1", "in2"], ["a"] * 10])
def test_get_available_midi_in(mock_midi_in_out, state_manager, ports):
    mock_midi_in, _ = mock_midi_in_out
    mock_midi_in.get_ports.return_value = ports
    assert state_manager.get_available_midi_in() == ports


@pytest.mark.parametrize("ports", [[], ["out1", "out2"], ["b"] * 10])
def test_get_available_midi_out(mock_midi_in_out, state_manager, ports):
    _, mock_midi_out = mock_midi_in_out
    mock_midi_out.get_ports.return_value = ports
    assert state_manager.get_available_midi_out() == ports


@pytest.mark.parametrize("name", ["abc", "", "x" * 100])
def test_select_midi_in(mock_midi_in_out, state_manager, name):
    state_manager.select_midi_in(name)

    assert state_manager.selected_midi_in == name


@pytest.mark.parametrize("name", ["abc", "", "x" * 100])
def test_select_midi_out(mock_midi_in_out, state_manager, name):
    state_manager.select_midi_out(name)

    assert state_manager.selected_midi_out == name


def test_stop_handling(mock_midi_in_out, state_manager):
    mock_midi_in, mock_midi_out = mock_midi_in_out

    state_manager._connected_controller = Mock()
    state_manager.stop_handling()

    mock_midi_in.cancel_callback.assert_called_once()
    mock_midi_in.close_port.assert_called_once()
    mock_midi_out.close_port.assert_called_once()
    assert not state_manager.is_running()


def test_start_handling(
    mock_midi_in_out, state_manager, mock_binds_load, mock_controller_load
):
    mock_midi_in, mock_midi_out = mock_midi_in_out
    mock_midi_in.get_ports.return_value = ["x", "input1"]
    mock_midi_out.get_ports.return_value = ["a", "b", "output1"]

    state_manager.selected_controller = SelectedItem("test_controller", "xyz")
    state_manager.selected_binds = SelectedItem("test_binds", "abc")
    state_manager.selected_midi_in = "input1"
    state_manager.selected_midi_out = "output1"

    state_manager.start_handling()

    mock_midi_in.open_port.assert_called_once_with(1)
    mock_midi_out.open_port.assert_called_once_with(2)
    mock_binds_load.assert_called_once()
    mock_controller_load.assert_called_once()
    assert state_manager.is_running()
