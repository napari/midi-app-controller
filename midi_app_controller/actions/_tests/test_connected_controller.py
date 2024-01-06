import time
from unittest.mock import Mock, call

import pytest
from app_model.types import Action

from midi_app_controller.actions.connected_controller import ConnectedController
from midi_app_controller.actions.bound_controller import BoundController
from midi_app_controller.actions.actions_handler import ActionsHandler
from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller


@pytest.fixture
def actions_handler() -> ActionsHandler:
    binds_data = {
        "name": "TestBinds",
        "app_name": "TestApp",
        "controller_name": "X-TOUCH MINI",
        "button_binds": [{"button_id": 8, "action_id": "Action1"}],
        "knob_binds": [
            {
                "knob_id": 1,
                "action_id_increase": "incr",
                "action_id_decrease": "decr",
            }
        ],
    }

    controller_data = {
        "name": "X-TOUCH MINI",
        "button_value_off": 0,
        "button_value_on": 127,
        "knob_value_min": 0,
        "knob_value_max": 127,
        "buttons": [{"id": 8, "name": "Button1"}, {"id": 9, "name": "Button2"}],
        "knobs": [{"id": 1, "name": "Knob1"}, {"id": 2, "name": "Knob2"}],
    }

    actions = [
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

    bound_controller = BoundController.create(
        controller=Controller(**controller_data),
        binds=Binds(**binds_data),
        actions=actions,
    )

    return ActionsHandler(
        bound_controller=bound_controller,
        app=Mock()
    )


def test_create(actions_handler):
    connected_controller = \
        ConnectedController.create(
            actions_handler=actions_handler,
        )
    
    connected_controller.turn_on_knob_backlight(1)
    connected_controller.turn_on_button_led(8)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        del connected_controller

