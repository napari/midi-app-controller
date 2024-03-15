import logging
import time
from typing import List, Tuple

import rtmidi
from qtpy.QtCore import QMutex, QMutexLocker

from midi_app_controller.models.controller import Controller
from midi_app_controller.actions.actions_handler import ActionsHandler
from .controller_constants import ControllerConstants


class ConnectedController:
    """A controller connected to the physical device capable of
    sending and receiving signals.

    Attributes
    ----------
    controller : Controller
        Data about the controller, the create method will try to connect to.
    actions_handler : ActionsHandler
        Actions handler class, responsible for executing actions, specific
        to a button press or a knob turn.
    midi_in : rtmidi.MidiIn
        Midi input client interface from python-rtmidi package.
    midi_out: rtmidi.MidiOut
        Midi output client interface from python-rtmidi package.
    button_ids : List[int]
        A list containing all valid button ids on a handled controller.
    knob_ids : List[int]
        A list containing all valid knob ids on a handled controller.
    knob_engagement: Dict[int, int]
        A dictionary that keeps the value of every knob.
    """

    def __init__(
        self,
        *,
        actions_handler: ActionsHandler,
        controller: Controller,
        midi_in: rtmidi.MidiIn,
        midi_out: rtmidi.MidiOut,
    ) -> None:
        """Initializes `ConnectedController`.

        Parameters
        ----------
        actions_handler : ActionsHandler
            Provides methods capable of executing actions in the app.
        controller : Controller
            Information about the controller.
        midi_in : rtmidi.MidiIn
            Midi input client with the controller's port opened.
        midi_out: rtmidi.MidiOut
            Midi output client with the controller's port opened.
        """
        self.controller = controller
        self.actions_handler = actions_handler
        self.midi_out = midi_out
        self.midi_in = midi_in
        self.button_ids = [element.id for element in controller.buttons]
        self.knob_ids = [element.id for element in controller.knobs]
        self.knob_engagement = {}

        # Set default values for buttons and knobs.
        self.init_buttons()
        self.init_knobs()

        self.mutex = QMutex()

        # Set callback for getting data from controller.
        self.set_default_callback()

    def set_custom_callback(self, callback: callable) -> None:
        """Sets custom callback function"""
        self.midi_in.set_callback(callback)

    def set_default_callback(self) -> None:
        """Sets default callback function"""
        self.midi_in.set_callback(self.midi_callback)

    def midi_callback(self, event: Tuple[List[int], float], data=None) -> None:
        """Callback function for MIDI input, specified by rtmidi package.

        Parameters
        ----------
        event : Tuple[List[int], float]
            Pair of (MIDI message, delta time).
        """
        message, _ = event

        command = message[0] & 0xF0
        channel = message[0] & 0x0F
        data_bytes = message[1:]

        logging.debug(
            f"Received command: {command}, channel: {channel}, data: {data_bytes}"
        )

        self.handle_midi_message(command, channel, data_bytes)

    def init_buttons(self) -> None:
        """Initializes the buttons on the controller, setting them
        to the 'off' value.

        Adds button entries to `button_engagement` dictionary.
        """
        for id in self.button_ids:
            self.turn_off_button_led(id)

    def init_knobs(self) -> None:
        """Initializes the knobs on the controller, setting them
        to the minimal value.

        Adds knob entries to `knob_engagement` dictionary.
        """
        for id in self.knob_ids:
            self.change_knob_value(id, self.controller.knob_value_min)
            self.knob_engagement[id] = self.controller.knob_value_min

    def handle_button_engagement(self, data) -> None:
        """Runs the action bound to the button, specified in `actions_handler`.

        Parameters
        ----------
        data : List[int]
            Standard MIDI message.
        """
        id = data[0]

        self.actions_handler.handle_button_action(
            button_id=id,
        )

    def handle_button_disengagement(self, data: List[int]) -> None:
        """Runs the action bound to the button release, specified in
        `actions_handler`.

        Parameters
        ----------
        data : List[int]
            Standard MIDI message.
        """
        pass  # TODO: for now we're not handling button disengagement

    def handle_knob_message(self, data: List[int]) -> None:
        """Runs the action bound to the knob turn, specified in
        `actions_handler`.

        Parameters
        ----------
        data : List[int]
            Standard MIDI message.
        """
        id = data[0]
        velocity = data[1]
        prev_velocity = self.knob_engagement[id]

        self.knob_engagement[id] = velocity

        if velocity == prev_velocity:
            if velocity == self.controller.knob_value_min:
                prev_velocity = self.controller.knob_value_min + 1
            elif velocity == self.controller.knob_value_max:
                prev_velocity = self.controller.knob_value_max - 1

        self.actions_handler.handle_knob_action(
            knob_id=id,
            old_value=prev_velocity,
            new_value=velocity,
        )

    def send_midi_message(self, data: List[int]) -> None:
        """Sends the specified MIDI message.

        Parameters
        ----------
        data : List[int]
            Standard MIDI message.
        """
        try:
            self.midi_out.send_message(data)
            logging.debug(f"Sent: {data}")
        except ValueError as err:
            logging.error(f"Value Error: {err}")

    def flash_knob(self, id: int) -> None:
        """Flashes the LEDs corresponding to a knob on a MIDI controller.

        Parameters
        ----------
        id : int
            Id of the knob.
        """
        with QMutexLocker(self.mutex):
            current_value = self.knob_engagement[id]

        sleep_seconds = 0.04
        intervals = 14
        min_max_diff = self.controller.knob_value_max - self.controller.knob_value_min

        for value in range(
            self.controller.knob_value_min,
            self.controller.knob_value_max,
            min_max_diff // intervals,
        ):
            self.change_knob_value(id, value)
            time.sleep(sleep_seconds)

        for value in range(
            self.controller.knob_value_max,
            self.controller.knob_value_min,
            -min_max_diff // intervals,
        ):
            self.change_knob_value(id, value)
            time.sleep(sleep_seconds)

        self.change_knob_value(id, current_value)

    def flash_button(self, id: int) -> None:
        """Flashes the button LED on a MIDI controller.

        Parameters
        ----------
        id : int
            Id of the button.
        """
        sleep_seconds = 0.3

        for _ in range(3):
            self.turn_on_button_led(id)
            time.sleep(sleep_seconds)
            self.turn_off_button_led(id)
            time.sleep(sleep_seconds)

    def build_message(
        self,
        command: int,
        channel: int,
        data: List[int],
    ) -> List[int]:
        """Builds the MIDI message, that is later sent to the controller."""
        status_byte = command ^ (channel - 1)
        return [status_byte, data[0], data[1]]

    def change_knob_value(self, id: int, new_value: int) -> None:
        """Sends the MIDI message, responsible for changing
        a value assigned to a knob.

        Parameters
        ----------
        id : int
            Knob id.
        new_value : int
            Value to set the knob to.
        """
        # For now we, only use single channel
        channel = 11

        data = self.build_message(
            ControllerConstants.CONTROL_CHANGE_COMMAND,
            channel,
            [id, new_value],
        )

        self.send_midi_message(data)

    def turn_on_button_led(self, id: int) -> None:
        """Sends the MIDI message, responsible for changing
        the button LED to 'on' state.

        Parameters
        ----------
        id : int
            Button id.
        """
        # For now we, only use single channel
        channel = 11

        data = self.build_message(
            ControllerConstants.BUTTON_ENGAGED_COMMAND,
            channel,
            [id, self.controller.button_value_on],
        )

        self.send_midi_message(data)

    def turn_off_button_led(self, id: int) -> None:
        """Sends the MIDI message, responsible for changing
        the button LED to 'off' state.

        Parameters
        ----------
        id : int
            Button id.
        """
        # For now we, only use single channel
        channel = 11

        data = self.build_message(
            ControllerConstants.BUTTON_DISENGAGED_COMMAND,
            channel,
            [id, self.controller.button_value_off],
        )

        self.send_midi_message(data)

    def handle_midi_message(self, command: int, channel: int, data: List[int]) -> None:
        """Handles the incoming MIDI message.

        The message is interpreted as follows:
        [command*16+channel, data[0], data[1]],
        where the three numbers are unsigned ints.

        Parameters
        ----------
        command : int
            Command id.
        channel : int
            Channel the MIDI message came from.
        data : List[int]
            Remaining part of the MIDI message.
        """
        id = data[0]

        if (
            id in self.knob_ids
            and command == ControllerConstants.CONTROL_CHANGE_COMMAND
        ):
            self.handle_knob_message(data)
        elif (
            id in self.button_ids
            and command == ControllerConstants.BUTTON_ENGAGED_COMMAND
        ):
            self.handle_button_engagement(data)
        elif (
            id in self.button_ids
            and command == ControllerConstants.BUTTON_DISENGAGED_COMMAND
        ):
            self.handle_button_disengagement(data)
        else:
            logging.debug(
                f"id: {id}, command: {command}, channel: {channel}, data: {data}"
            )
