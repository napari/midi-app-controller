import threading
import time
from unittest.mock import MagicMock, patch

import pytest
import rtmidi
from qtpy.QtCore import QMutex

from midi_app_controller.actions.actions_handler import ActionsHandler
from midi_app_controller.controller.connected_controller import ConnectedController
from midi_app_controller.controller.controller_constants import ControllerConstants
from midi_app_controller.models.controller import Controller, ControllerElement


@pytest.fixture
def controller():
    buttons = [ControllerElement(id=i, name=f"button_{i}") for i in range(3)]
    knobs = [ControllerElement(id=i, name=f"knob_{i}") for i in range(3)]
    return Controller(
        name="Test Controller",
        button_value_off=0,
        button_value_on=127,
        knob_value_min=0,
        knob_value_max=127,
        default_channel=1,
        preferred_midi_in="TestMidiIn",
        preferred_midi_out="TestMidiOut",
        buttons=buttons,
        knobs=knobs,
    )


@pytest.fixture
def actions_handler():
    return MagicMock(spec=ActionsHandler)


@pytest.fixture
def midi_in():
    return MagicMock(spec=rtmidi.MidiIn)


@pytest.fixture
def midi_out():
    return MagicMock(spec=rtmidi.MidiOut)


@pytest.fixture
def connected_controller(actions_handler, controller, midi_in, midi_out):
    connected_controller = ConnectedController(
        actions_handler=actions_handler,
        controller=controller,
        midi_in=midi_in,
        midi_out=midi_out,
    )
    return connected_controller


def test_connected_controller_init(connected_controller):
    assert connected_controller.controller is not None
    assert connected_controller.actions_handler is not None
    assert connected_controller.midi_in is not None
    assert connected_controller.midi_out is not None
    assert len(connected_controller.button_ids) == 3
    assert len(connected_controller.knob_ids) == 3


def test_stop(connected_controller):
    connected_controller.synchronize_buttons_thread.wait = MagicMock()
    connected_controller.stop()
    assert connected_controller.stopped
    connected_controller.midi_in.cancel_callback.assert_called_once()
    connected_controller.synchronize_buttons_thread.wait.assert_called_once()


def test_midi_callback(connected_controller):
    event = ([129, 1, 2], 0.2)
    connected_controller.handle_midi_message = MagicMock()
    connected_controller.midi_callback(event)
    connected_controller.handle_midi_message.assert_called_once_with(128, 1, [1, 2])


def test_pause(connected_controller):
    button_callback = MagicMock()
    knob_callback = MagicMock()
    connected_controller.pause(button_callback, knob_callback)
    assert connected_controller.paused
    assert connected_controller.paused_button_callback == button_callback
    assert connected_controller.paused_knob_callback == knob_callback


def test_resume(connected_controller):
    connected_controller.force_synchronize = {
        id: True for id in connected_controller.button_ids
    }
    connected_controller.knob_engagement = {
        id: connected_controller.controller.knob_value_min
        for id in connected_controller.knob_ids
    }
    connected_controller.resume()
    assert not connected_controller.paused

    for id in connected_controller.button_ids:
        assert connected_controller.force_synchronize[id]

    for id in connected_controller.knob_ids:
        assert (
            connected_controller.knob_engagement[id]
            == connected_controller.controller.knob_value_min
        )


@pytest.mark.parametrize("paused", [True, False])
def test_synchronize_buttons(paused, connected_controller):
    connected_controller.actions_handler.is_button_toggled.side_effect = (
        lambda id: id == 1
    )
    connected_controller.paused = paused
    connected_controller.turn_on_button_led = MagicMock()
    connected_controller.turn_off_button_led = MagicMock()

    def stop_thread_with_delay():
        time.sleep(1)
        connected_controller.stopped = True

    thread = threading.Thread(target=stop_thread_with_delay)
    thread.start()
    connected_controller.synchronize_buttons_thread = threading.Thread(
        target=connected_controller.synchronize_buttons
    )
    connected_controller.synchronize_buttons_thread.start()
    connected_controller.synchronize_buttons_thread.join()
    thread.join()

    if not paused:
        connected_controller.turn_on_button_led.assert_called_with(1)
        connected_controller.turn_off_button_led.assert_called_with(2)
        connected_controller.turn_off_button_led.assert_any_call(0)
    else:
        connected_controller.turn_on_button_led.assert_not_called()
        connected_controller.turn_off_button_led.assert_not_called()

    assert connected_controller.stopped


def test_synchronize_buttons_exception(connected_controller):
    connected_controller.actions_handler.is_button_toggled = MagicMock(
        side_effect=Exception("Test Exception")
    )
    connected_controller.turn_on_button_led = MagicMock()
    connected_controller.turn_off_button_led = MagicMock()

    def stop_thread_with_delay():
        time.sleep(1)
        connected_controller.stopped = True

    stop_thread = threading.Thread(target=stop_thread_with_delay)
    stop_thread.start()

    connected_controller.synchronize_buttons()
    connected_controller.turn_on_button_led.assert_not_called()
    connected_controller.turn_off_button_led.assert_not_called()
    stop_thread.join()


def test_init_buttons(connected_controller):
    connected_controller.turn_off_button_led = MagicMock()
    connected_controller.init_buttons()
    assert connected_controller.turn_off_button_led.call_count == 3


def test_init_knobs(connected_controller):
    connected_controller.change_knob_value = MagicMock()
    connected_controller.init_knobs()
    assert connected_controller.change_knob_value.call_count == 3


@pytest.mark.parametrize("paused", [True, False])
def test_handle_button_disengagement(paused, connected_controller):
    connected_controller.paused = paused
    connected_controller.actions_handler.handle_button_action = MagicMock()
    connected_controller.paused_button_callback = MagicMock()
    connected_controller.handle_button_disengagement([1])

    if not paused:
        connected_controller.actions_handler.handle_button_action.assert_called_once_with(
            1
        )
        connected_controller.paused_button_callback.assert_not_called()
    else:
        connected_controller.actions_handler.handle_button_action.assert_not_called()
        connected_controller.paused_button_callback.assert_called_once_with(1)


@pytest.mark.parametrize("paused", [True, False])
def test_handle_knob_message(paused, connected_controller):
    connected_controller.actions_handler.handle_knob_action = MagicMock()
    connected_controller.paused_knob_callback = MagicMock()
    connected_controller.paused = paused
    connected_controller.knob_engagement[1] = 0
    connected_controller.handle_knob_message([1, 64])
    if not paused:
        connected_controller.actions_handler.handle_knob_action.assert_called_once_with(
            knob_id=1, old_value=0, new_value=64
        )
        connected_controller.paused_knob_callback.assert_not_called()
    else:
        connected_controller.actions_handler.handle_knob_action.assert_not_called()
        connected_controller.paused_knob_callback.assert_called_once_with(1)


def test_send_midi_message(connected_controller):
    connected_controller.midi_out.send_message = MagicMock(side_effect=ValueError)
    with patch("logging.error") as mock_logging_error:
        connected_controller.send_midi_message([1, 2, 3])
        connected_controller.midi_out.send_message.assert_called_once_with([1, 2, 3])
        mock_logging_error.assert_called_once()


def test_check_set_and_run():
    func = MagicMock()
    ConnectedController.check_set_and_run(func, 1, QMutex(), set())
    func.assert_called_once()


@pytest.mark.parametrize(
    "command, channel, data, result",
    [
        (128, 5, [1, 127], [132, 1, 127]),
        (144, 1, [15, 107], [144, 15, 107]),
        (160, 16, [10, 0], [175, 10, 0]),
        (160, 8, [100, 127], [167, 100, 127]),
    ],
)
def test_build_message(connected_controller, command, channel, data, result):
    message = connected_controller.build_message(command, channel, data)
    assert message == result


def test_change_knob_value(connected_controller):
    connected_controller.send_midi_message = MagicMock()
    connected_controller.change_knob_value(1, 100)
    connected_controller.send_midi_message.assert_called_with([176, 1, 100])


def test_turn_on_button_led(connected_controller):
    connected_controller.send_midi_message = MagicMock()
    connected_controller.turn_on_button_led(1)
    connected_controller.send_midi_message.assert_called_with([144, 1, 127])


def test_turn_off_button_led(connected_controller):
    connected_controller.send_midi_message = MagicMock()
    connected_controller.turn_off_button_led(1)
    connected_controller.send_midi_message.assert_called_with([128, 1, 0])


def test_handle_midi_message(connected_controller):
    connected_controller.handle_knob_message = MagicMock()
    connected_controller.handle_button_engagement = MagicMock()
    connected_controller.handle_button_disengagement = MagicMock()
    connected_controller.handle_midi_message(
        ControllerConstants.CONTROL_CHANGE_COMMAND, 0, [1, 64]
    )
    connected_controller.handle_knob_message.assert_called_once()
    connected_controller.handle_midi_message(
        ControllerConstants.BUTTON_ENGAGED_COMMAND, 0, [1, 0]
    )
    connected_controller.handle_button_engagement.assert_called_once()
    connected_controller.handle_midi_message(
        ControllerConstants.BUTTON_DISENGAGED_COMMAND, 0, [1, 0]
    )
    connected_controller.handle_button_disengagement.assert_called_once()


def test_handle_knob_message_min(connected_controller):
    connected_controller.actions_handler.handle_knob_action = MagicMock()
    knob_value_min = connected_controller.controller.knob_value_min
    connected_controller.knob_engagement[1] = knob_value_min
    connected_controller.handle_knob_message([1, knob_value_min])
    connected_controller.actions_handler.handle_knob_action.assert_called_once_with(
        knob_id=1,
        old_value=connected_controller.controller.knob_value_min + 1,
        new_value=connected_controller.controller.knob_value_min,
    )


def test_handle_knob_message_max(connected_controller):
    connected_controller.actions_handler.handle_knob_action = MagicMock()
    connected_controller.knob_engagement[1] = (
        connected_controller.controller.knob_value_max
    )
    connected_controller.handle_knob_message(
        [1, connected_controller.controller.knob_value_max]
    )
    connected_controller.actions_handler.handle_knob_action.assert_called_once_with(
        knob_id=1,
        old_value=connected_controller.controller.knob_value_max - 1,
        new_value=connected_controller.controller.knob_value_max,
    )


@pytest.mark.parametrize("flashing", [True, False])
def test_flash_knob(flashing, connected_controller):
    if flashing:
        connected_controller.flashing_knobs.add(1)
    connected_controller.change_knob_value = MagicMock()
    connected_controller.knob_engagement[1] = 0
    connected_controller.flash_knob(1)
    if not flashing:
        assert connected_controller.change_knob_value.call_count > 0
    else:
        connected_controller.change_knob_value.assert_not_called()


@pytest.mark.parametrize("flashing", [True, False])
def test_flash_button(flashing, connected_controller):
    if flashing:
        connected_controller.flashing_buttons.add(1)
    connected_controller.turn_on_button_led = MagicMock()
    connected_controller.turn_off_button_led = MagicMock()
    connected_controller.flash_button(1)
    if not flashing:
        assert connected_controller.turn_on_button_led.call_count > 0
        assert connected_controller.turn_off_button_led.call_count > 0
    else:
        connected_controller.turn_on_button_led.assert_not_called()
        connected_controller.turn_off_button_led.assert_not_called()
