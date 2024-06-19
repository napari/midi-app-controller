import pytest
from pydantic import ValidationError

from ..controller import Controller, ControllerElement


@pytest.fixture
def controller_data() -> dict:
    return {
        "name": "TestController",
        "button_value_off": 11,
        "button_value_on": 100,
        "knob_value_min": 33,
        "knob_value_max": 55,
        "default_channel": 2,
        "preferred_midi_in": "TestMidiIn",
        "preferred_midi_out": "TestMidiOut",
        "buttons": [{"id": 1, "name": "Button1"}, {"id": 2, "name": "Button2"}],
        "knobs": [{"id": 3, "name": "Knob1"}, {"id": 4, "name": "Knob2"}],
    }


def test_valid_controller(controller_data):
    controller = Controller(**controller_data)

    assert controller.model_dump() == controller_data


@pytest.mark.parametrize(
    "buttons, knobs",
    [
        (
            [{"id": 1, "name": "Button1"}, {"id": 1, "name": "Button2"}],
            [{"id": 2, "name": "Knob1"}],
        ),
        (
            [{"id": 2, "name": "Button1"}],
            [{"id": 1, "name": "Knob1"}, {"id": 1, "name": "Knob2"}],
        ),
    ],
)
def test_controller_duplicate_element_id(controller_data, buttons, knobs):
    controller_data["buttons"] = buttons
    controller_data["knobs"] = knobs

    with pytest.raises(ValidationError):
        Controller(**controller_data)


@pytest.mark.parametrize(
    "buttons, knobs",
    [
        (
            [{"id": 1, "name": "duplicate_name"}, {"id": 2, "name": "duplicate_name"}],
            [{"id": 3, "name": "Knob1"}],
        ),
        (
            [{"id": 1, "name": "Button1"}],
            [{"id": 2, "name": "duplicate_name"}, {"id": 3, "name": "duplicate_name"}],
        ),
    ],
)
def test_controller_duplicate_element_name(controller_data, buttons, knobs):
    controller_data["buttons"] = buttons
    controller_data["knobs"] = knobs

    with pytest.raises(ValidationError):
        Controller(**controller_data)


@pytest.mark.parametrize(
    "button_value_off, button_value_on, knob_value_min, knob_value_max",
    [
        (-1, 127, 0, 127),
        (0, 128, 0, 127),
        (0, 127, -1, 127),
        (0, 127, 0, 128),
    ],
)
def test_controller_values_range(
    controller_data, button_value_off, button_value_on, knob_value_min, knob_value_max
):
    controller_data["button_value_off"] = button_value_off
    controller_data["button_value_on"] = button_value_on
    controller_data["knob_value_min"] = knob_value_min
    controller_data["knob_value_max"] = knob_value_max

    with pytest.raises(ValidationError):
        Controller(**controller_data)


def test_knob_min_value_greater_than_max_value(controller_data):
    controller_data["knob_value_min"] = 100
    controller_data["knob_value_max"] = 50

    with pytest.raises(ValidationError):
        Controller(**controller_data)


def test_button_on_and_off_values_equal(controller_data):
    controller_data["button_value_off"] = 100
    controller_data["button_value_on"] = 100

    with pytest.raises(ValidationError):
        Controller(**controller_data)


@pytest.mark.parametrize("id", [-1, 128])
def test_controller_element_id_out_of_range(id):
    element_data = {"id": id, "name": "Name"}

    with pytest.raises(ValidationError):
        ControllerElement(**element_data)
