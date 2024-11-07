import pytest
from pydantic import ValidationError

from ..binds import Binds, ButtonBind, KnobBind


@pytest.fixture
def binds_data() -> dict:
    return {
        "name": "TestBinds",
        "description": "Test description",
        "app_name": "TestApp",
        "controller_name": "TestController",
        "button_binds": [{"button_id": 0, "action_id": "Action1"}],
        "knob_binds": [
            {
                "knob_id": 127,
                "action_id_increase": "incr",
                "action_id_decrease": "decr",
            }
        ],
    }


def test_valid_binds(binds_data):
    binds = Binds(**binds_data)

    assert binds.model_dump() == binds_data


@pytest.mark.parametrize(
    "button_binds, knob_binds",
    [
        (
            [
                {"button_id": 1, "action_id": "Action1"},
                {"button_id": 1, "action_id": "Action2"},
            ],
            [
                {
                    "knob_id": 2,
                    "action_id_increase": "incr",
                    "action_id_decrease": "decr",
                }
            ],
        ),
        (
            [{"button_id": 1, "action_id": "Action1"}],
            [
                {
                    "knob_id": 2,
                    "action_id_increase": "incr",
                    "action_id_decrease": "decr",
                },
                {
                    "knob_id": 2,
                    "action_id_increase": "incr",
                    "action_id_decrease": "decr",
                },
            ],
        ),
    ],
)
def test_binds_duplicate_id(binds_data, button_binds, knob_binds):
    binds_data["button_binds"] = button_binds
    binds_data["knob_binds"] = knob_binds

    with pytest.raises(ValidationError):
        Binds(**binds_data)


@pytest.mark.parametrize(
    "button_binds, knob_binds",
    [
        (
            [{"button_id": 1, "action_id": "Action1"}],
            [
                {
                    "knob_id": 1,
                    "action_id_increase": "incr",
                    "action_id_decrease": "decr",
                }
            ],
        ),
    ],
)
def test_allow_knob_button_collision(binds_data, button_binds, knob_binds):
    binds_data["button_binds"] = button_binds
    binds_data["knob_binds"] = knob_binds
    Binds(**binds_data)


@pytest.mark.parametrize("id", [-1, 128])
def test_button_id_out_of_range(id):
    button_data = {"button_id": id, "action_id": "Action1"}

    with pytest.raises(ValidationError):
        ButtonBind(**button_data)


@pytest.mark.parametrize("id", [-1, 128])
def test_knob_id_out_of_range(id):
    knob_data = {
        "knob_id": id,
        "action_id_increase": "a",
        "action_id_decrease": "b",
    }

    with pytest.raises(ValidationError):
        KnobBind(**knob_data)
