from unittest.mock import Mock, call, patch

# ruff: noqa: E402
patch("superqt.utils.ensure_main_thread", lambda await_return: lambda f: f).start()

import pytest
from app_model.types import Action, ToggleRule

from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller

from ..actions_handler import ActionsHandler
from ..bound_controller import BoundController


@pytest.fixture
def bound_controller() -> BoundController:
    binds_data = {
        "name": "TestBinds",
        "app_name": "TestApp",
        "controller_name": "TestController",
        "description": None,
        "button_binds": [{"button_id": 1, "action_id": "Action1"}],
        "knob_binds": [
            {
                "knob_id": 2,
                "action_id_increase": "incr",
                "action_id_decrease": "decr",
            }
        ],
    }

    controller_data = {
        "name": "TestController",
        "button_value_off": 0,
        "button_value_on": 127,
        "knob_value_min": 0,
        "knob_value_max": 127,
        "default_channel": 3,
        "preferred_midi_in": "TestMidiIn",
        "preferred_midi_out": "TestMidiOut",
        "buttons": [{"id": 0, "name": "Button1"}, {"id": 1, "name": "Button2"}],
        "knobs": [{"id": 2, "name": "Knob1"}, {"id": 3, "name": "Knob2"}],
    }

    actions = [
        Action(
            id="Action1",
            title="sdfgsdfg",
            callback=lambda: None,
            toggled=ToggleRule(get_current=lambda: True),
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

    return BoundController.create(
        controller=Controller(**controller_data),
        binds=Binds(**binds_data),
        actions=actions,
    )


def test_is_button_toggled_when_button_not_bound(bound_controller):
    actions_handler = ActionsHandler(bound_controller=bound_controller, app=Mock())

    assert actions_handler.is_button_toggled(0) is None


def test_is_button_toggled(bound_controller):
    app = Mock()
    app.injection_store.inject = lambda x: x
    actions_handler = ActionsHandler(bound_controller=bound_controller, app=app)

    assert actions_handler.is_button_toggled(1)


def test_get_knob_value(bound_controller):
    actions_handler = ActionsHandler(bound_controller=bound_controller, app=Mock())

    with pytest.raises(NotImplementedError):
        actions_handler.get_knob_value(0)


def test_handle_button_action(bound_controller):
    app = Mock()
    actions_handler = ActionsHandler(bound_controller=bound_controller, app=app)

    actions_handler.handle_button_action(1)

    app.commands.execute_command.assert_called_once_with("Action1")


@pytest.mark.parametrize("button_id", [3, 10, 1000])
def test_handle_button_action_when_button_not_bound(bound_controller, button_id):
    app = Mock()
    actions_handler = ActionsHandler(bound_controller=bound_controller, app=app)

    actions_handler.handle_button_action(button_id)

    app.commands.execute_command.assert_not_called()


@pytest.mark.parametrize("old_value, new_value", [(10, 20), (10, 10), (10, 11)])
def test_handle_knob_action_increase(bound_controller, old_value, new_value):
    app = Mock()
    actions_handler = ActionsHandler(bound_controller=bound_controller, app=app)

    actions_handler.handle_knob_action(
        knob_id=2, old_value=old_value, new_value=new_value
    )

    assert old_value <= new_value
    calls = [call("incr")] * (new_value - old_value)
    app.commands.execute_command.assert_has_calls(calls)


@pytest.mark.parametrize("old_value, new_value", [(20, 10), (11, 10)])
def test_handle_knob_action_decrease(bound_controller, old_value, new_value):
    app = Mock()
    actions_handler = ActionsHandler(bound_controller=bound_controller, app=app)

    actions_handler.handle_knob_action(
        knob_id=2, old_value=old_value, new_value=new_value
    )

    assert old_value > new_value
    calls = [call("decr")] * (old_value - new_value)
    app.commands.execute_command.assert_has_calls(calls)


@pytest.mark.parametrize(
    "knob_id, old_value, new_value",
    [
        (3, 10, 10),
        (3, 11, 10),
        (3, 10, 11),
        (1000, 10, 20),
        (-1, 10, 20),
    ],
)
def test_handle_knob_action_when_knob_not_bound(
    bound_controller, knob_id, old_value, new_value
):
    app = Mock()
    actions_handler = ActionsHandler(bound_controller=bound_controller, app=app)

    actions_handler.handle_knob_action(
        knob_id=knob_id, old_value=old_value, new_value=new_value
    )

    app.commands.execute_command.assert_not_called()
