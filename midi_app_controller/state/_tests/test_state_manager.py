import uuid
from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest
from app_model import Application
from app_model.types import Action

from midi_app_controller.config import Config
from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller

from ..state_manager import SelectedItem, StateManager, get_state_manager


@pytest.fixture
def actions() -> list[Action]:
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
        "default_channel": 5,
        "preferred_midi_in": "TestMidiIn",
        "preferred_midi_out": "TestMidiOut",
        "buttons": [{"id": 0, "name": "Button1"}, {"id": 1, "name": "Button2"}],
        "knobs": [{"id": 2, "name": "Knob1"}, {"id": 3, "name": "Knob2"}],
    }
    return Controller(**controller_data)


@pytest.fixture
def state_manager(actions) -> StateManager:
    app = Application("app123" + str(uuid.uuid4()))
    for action in actions:
        app.register_action(action)
    return StateManager(app)


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


def test_get_available_controllers(mock_midi_in_out, state_manager):
    controllers = state_manager.get_available_controllers()

    assert len(controllers) > 0


def test_get_available_binds_when_no_controller(mock_midi_in_out, state_manager):
    binds = state_manager.get_available_binds()

    assert len(binds) == 0


def test_get_available_binds(mock_midi_in_out, state_manager):
    state_manager.select_controller(SelectedItem("X-TOUCH MINI", None))
    binds = state_manager.get_available_binds()

    assert len(binds) > 0


def test_get_available_binds_unknown_controller(mock_midi_in_out, state_manager):
    state_manager.select_controller(SelectedItem("asdfsdfasdf", None))
    binds = state_manager.get_available_binds()

    assert len(binds) == 0


def test_select_binds_path(mock_midi_in_out, state_manager, binds, tmp_path):
    binds_path = tmp_path / "binds.yaml"
    binds.save_to(binds_path)

    state_manager.select_binds_path(binds_path)

    assert state_manager.selected_binds == SelectedItem(binds.name, binds_path)


def test_select_binds_path_none(mock_midi_in_out, state_manager):
    state_manager.select_binds_path(None)

    assert state_manager.selected_binds is None


def test_select_binds(mock_midi_in_out, state_manager):
    binds = SelectedItem("abc", Path(__file__))
    state_manager.select_binds(binds)

    assert state_manager.selected_binds == binds


def test_select_binds_when_controller_selected(mock_midi_in_out, state_manager):
    controller = SelectedItem("123", Path(__file__) / "a")
    binds = SelectedItem("abc", Path(__file__) / "b")
    state_manager.select_controller(controller)
    state_manager.select_binds(binds)

    assert state_manager.selected_binds == binds
    assert state_manager.selected_controller == controller
    assert state_manager.recent_binds_for_controller == {controller.path: binds.path}


def test_select_binds_none(mock_midi_in_out, state_manager):
    state_manager.select_binds(None)

    assert state_manager.selected_binds is None


def test_select_recent_binds(mock_midi_in_out, state_manager, mock_binds_load):
    controller1 = SelectedItem("123", Path(__file__) / "a")
    controller2 = SelectedItem("456", Path(__file__) / "a" / "c")
    binds1 = SelectedItem("abc", Path(__file__) / "b")
    binds2 = SelectedItem("def", Path(__file__) / "b" / "x")

    state_manager.select_controller(controller1)
    state_manager.select_binds(binds1)
    state_manager.select_controller(controller2)
    state_manager.select_binds(binds2)

    state_manager.select_controller(controller1)
    state_manager.select_recent_binds()
    assert state_manager.selected_binds.path == binds1.path

    state_manager.select_controller(controller2)
    state_manager.select_recent_binds()
    assert state_manager.selected_binds.path == binds2.path


def test_delete_binds_not_selected(mock_midi_in_out, state_manager):
    with pytest.raises(Exception) as excinfo:
        state_manager.delete_binds()
    assert "No binds" in str(excinfo.value)


def test_delete_binds_not_user_dir(mock_midi_in_out, state_manager):
    with pytest.raises(PermissionError):
        state_manager.select_binds(SelectedItem("123", Path(__file__).resolve()))
        state_manager.delete_binds()


def test_delete_binds(mock_midi_in_out, state_manager, binds, tmp_path):
    binds_path = tmp_path / "binds.yaml"
    binds.save_to(binds_path)
    state_manager.select_binds_path(binds_path)

    assert binds_path.exists()
    with patch.object(Config, "BINDS_USER_DIR", tmp_path):
        state_manager.delete_binds()
    assert not binds_path.exists()


def test_copy_binds(mock_midi_in_out, state_manager, mock_binds_load):
    with patch("midi_app_controller.models.binds.Binds.save_copy_to") as mock_save:
        state_manager.select_binds(SelectedItem("123", Path(__file__).resolve()))
        state_manager.copy_binds()

        mock_save.assert_called_once_with(ANY, Config.BINDS_USER_DIR)


def test_copy_binds_when_none_selected(mock_midi_in_out, state_manager):
    with pytest.raises(Exception) as excinfo:
        state_manager.copy_binds()
    assert "No binds" in str(excinfo.value)


def test_select_controller_path(mock_midi_in_out, state_manager, controller, tmp_path):
    controller_path = tmp_path / "controller.yaml"
    controller.save_to(controller_path)

    state_manager.select_controller_path(controller_path)

    assert state_manager.selected_controller == SelectedItem(
        controller.name, controller_path
    )


def test_select_controller_path_none(mock_midi_in_out, state_manager):
    state_manager.select_controller_path(None)

    assert state_manager.selected_controller is None


def test_select_controller(mock_midi_in_out, state_manager):
    controller = SelectedItem("123", Path(__file__) / "a")
    state_manager.select_controller(controller)

    assert state_manager.selected_controller == controller


def test_get_actions(mock_midi_in_out, state_manager, actions):
    assert len(state_manager.get_actions()) == len(actions)


def test_get_state_manager(mock_midi_in_out):
    state = get_state_manager()

    assert state is not None
    assert len(state.get_actions()) > 10


@pytest.mark.parametrize("name", ["abc", "", "x" * 100, None])
def test_select_midi_in(mock_midi_in_out, state_manager, name):
    state_manager.select_midi_in(name)

    assert state_manager.selected_midi_in == name


@pytest.mark.parametrize("name", ["abc", "", "x" * 100, None])
def test_select_midi_out(mock_midi_in_out, state_manager, name):
    state_manager.select_midi_out(name)

    assert state_manager.selected_midi_out == name


def test_save_state(mock_midi_in_out, state_manager):
    with patch("midi_app_controller.models.app_state.AppState.save_to") as mock_save:
        state_manager.save_state()

        mock_save.assert_called_once_with(Config.APP_STATE_FILE)


def test_save_load_state(mock_midi_in_out, state_manager, tmp_path, binds, controller):
    with (
        patch.object(Config, "APP_STATE_FILE", tmp_path / "state.yaml"),
        patch.object(Config, "BINDS_DIRS", (tmp_path,)),
        patch.object(Config, "CONTROLLER_DIRS", (tmp_path,)),
    ):
        binds_path = tmp_path / "binds.yaml"
        controller_path = tmp_path / "controller.yaml"
        binds.save_to(binds_path)
        controller.save_to(controller_path)

        state_manager.select_controller_path(controller_path)
        state_manager.select_binds_path(binds_path)
        state_manager.select_midi_in("in")
        state_manager.select_midi_out("out")

        state_manager.save_state()

        state_manager.select_controller_path(None)
        state_manager.select_binds_path(None)
        state_manager.select_midi_in(None)
        state_manager.select_midi_in(None)

        state_manager.load_state()

        assert state_manager.selected_controller.path == controller_path
        assert state_manager.selected_binds.path == binds_path
        assert state_manager.selected_midi_in == "in"
        assert state_manager.selected_midi_out == "out"
        assert state_manager.recent_binds_for_controller == {
            controller_path: binds_path
        }


def test_stop_handling(mock_midi_in_out, state_manager):
    mock_midi_in, mock_midi_out = mock_midi_in_out

    connected_controller = Mock()
    state_manager.connected_controller = connected_controller
    state_manager.stop_handling()

    connected_controller.stop.assert_called_once()
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

    state_manager.stop_handling()


def test_start_handling_without_fields_set(mock_midi_in_out, state_manager):
    with pytest.raises(Exception) as excinfo:
        state_manager.start_handling()
    assert "No controller" in str(excinfo.value)

    state_manager.select_controller(SelectedItem("name", None))

    with pytest.raises(Exception) as excinfo:
        state_manager.start_handling()
    assert "No binds" in str(excinfo.value)

    state_manager.select_binds(SelectedItem("name", None))

    with pytest.raises(Exception) as excinfo:
        state_manager.start_handling()
    assert "No MIDI input" in str(excinfo.value)

    state_manager.select_midi_in("in")

    with pytest.raises(Exception) as excinfo:
        state_manager.start_handling()
    assert "No MIDI output" in str(excinfo.value)

    state_manager.select_midi_out("out")

    with pytest.raises(Exception) as excinfo:
        state_manager.start_handling()
    assert "No MIDI output" not in str(excinfo.value)


@pytest.mark.parametrize(
    (
        "available_midi_in, available_midi_out, recent_ports, "
        "expected_midi_in, expected_midi_out"
    ),
    [
        (["in1", "in2"], ["out1", "out2"], {"in": "in1", "out": "out2"}, "in1", "out2"),
        (["in1", "in2"], ["out1", "out2"], {}, None, None),
        (["in1", "in2"], ["out1", "out2"], {"in": "in3", "out": "out3"}, None, None),
    ],
)
def test_select_recent_midi_ports(
    mock_midi_in_out,
    state_manager,
    available_midi_in,
    available_midi_out,
    recent_ports,
    expected_midi_in,
    expected_midi_out,
):
    mock_midi_in, mock_midi_out = mock_midi_in_out
    mock_midi_in.get_ports.return_value = available_midi_in
    mock_midi_out.get_ports.return_value = available_midi_out

    controller_path = Path("test_controller_path")
    state_manager.selected_controller = SelectedItem("TestController", controller_path)

    state_manager.recent_midi_ports_for_controller = (
        {controller_path: recent_ports} if recent_ports else {}
    )

    state_manager.select_recent_midi_ports()

    assert state_manager.selected_midi_in == expected_midi_in
    assert state_manager.selected_midi_out == expected_midi_out
