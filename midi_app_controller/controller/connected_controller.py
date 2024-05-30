import logging
import time
from typing import Callable, Optional

import rtmidi
from qtpy.QtCore import QMutex, QMutexLocker

from midi_app_controller.actions.actions_handler import ActionsHandler
from midi_app_controller.models.controller import Controller
from midi_app_controller.utils import SimpleQThread

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
    button_ids : frozenset[int]
        Set of all button ids on the controller.
    knob_ids : frozenset[int]
        Set of all knob ids on the controller.
    knob_engagement : dict[int, int]
        A dictionary that keeps the value of every knob.
    butons_mutex : QMutex
        Mutex for worker threads.
    flashing_buttons : set[int]
        Set with ids of buttons that are currently flashing.
    knobs_mutex : QMutex
        Mutex for worker threads.
    flashing_knobs : set[int]
        Set of the knob ids, that are currently flashing.
    stopped : bool
        Indicates if the `stop` method was called.
    paused : bool
        Indicates if the synchronization and standard handling is paused.
    paused_button_callback : Optional[Callable[[int], None]]
        Function to be called with button id as an argument when `paused` and
        a message is received.
    paused_knob_callback : Optional[Callable[[int], None]]
        Function to be called with knob id as an argument when `paused` and
        a message is received.
    synchronize_buttons_thread : Thread
        Thread that checks values of the actions associated with buttons.
    force_synchronize : dict[int, bool]
        Dictionary that indicates if there was a message from a button with
        given id, but the value associated with it wasn't synchronized yet.
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
        self.button_ids = frozenset(element.id for element in controller.buttons)
        self.knob_ids = frozenset(element.id for element in controller.knobs)
        self.knob_engagement = {}

        # Set default values for buttons and knobs.
        self.init_buttons()
        self.init_knobs()

        # Flashing elements.
        self.flashing_knobs = set()
        self.flashing_buttons = set()

        self.knobs_mutex = QMutex()
        self.buttons_mutex = QMutex()

        # Set callback for getting data from controller.
        self.midi_in.set_callback(self.midi_callback)

        # Threads.
        self.stopped = False
        self.paused = False
        self.paused_button_callback = None
        self.paused_knob_callback = None
        self.force_synchronize = {id: True for id in self.button_ids}
        self.synchronize_buttons_thread = SimpleQThread(self.synchronize_buttons)
        self.synchronize_buttons_thread.start()

    def stop(self) -> None:
        """Stops all threads and callbacks.

        After calling this method, the object can be safely discarded.
        """
        self.stopped = True
        self.midi_in.cancel_callback()
        self.synchronize_buttons_thread.wait()

    def midi_callback(self, event: tuple[list[int], float], data=None) -> None:
        """Callback function for MIDI input, specified by rtmidi package.

        Parameters
        ----------
        event : tuple[list[int], float]
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

    def pause(
        self,
        paused_button_callback: Optional[Callable[[int], None]],
        paused_knob_callback: Optional[Callable[[int], None]],
    ) -> None:
        """Pauses synchronization and messages handling."""
        self.paused_button_callback = paused_button_callback
        self.paused_knob_callback = paused_knob_callback
        self.paused = True

    def resume(self) -> None:
        """Resumes synchronization and messages handling."""
        self.paused_button_callback = None
        self.paused_knob_callback = None

        # The knobs and buttons might have changed values, eg. due to highlighting.
        for id in self.button_ids:
            self.force_synchronize[id] = True
        for id in self.knob_ids:
            self.change_knob_value(id, self.knob_engagement[id])

        self.paused = False

    def synchronize_buttons(self) -> None:
        """Synchronizes button values on controller with values from app.

        For example, if user executes an action assosciated with a button
        directly in a GUI rather than on the MIDI controller, then this
        function will handle it.
        """
        SLEEP_SECONDS = 0.2
        N = 5 // SLEEP_SECONDS

        state = {id: (False, 0) for id in self.button_ids}
        # (previous value, iters since the last message was sent to the controller)
        # We don't want to send the same value every iteration. But at the same
        # time we also want to be sure that the values on controller are really
        # synchronized. So a current value is always sent every `N` iterations.

        while not self.stopped:
            try:
                time.sleep(SLEEP_SECONDS)
                if self.paused:
                    continue

                for id in self.button_ids:
                    is_toggled = self.actions_handler.is_button_toggled(id) or False
                    was_toggled, iters = state[id]
                    sync = self.force_synchronize[id]
                    if is_toggled != was_toggled or iters > N or sync:
                        iters = 0
                        self.force_synchronize[id] = False
                        if is_toggled:
                            self.turn_on_button_led(id)
                        else:
                            self.turn_off_button_led(id)
                    state[id] = (is_toggled, iters + 1)
            except Exception as e:
                logging.error(f"Error in `synchronize_buttons`: {e}")

    def init_buttons(self) -> None:
        """Initializes the buttons on the controller, setting them
        to the 'off' value.
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

    def handle_button_engagement(self, data: list[int]) -> None:
        """Curently does nothing.

        Parameters
        ----------
        data : list[int]
            Standard MIDI message.
        """
        pass

    def handle_button_disengagement(self, data: list[int]) -> None:
        """Runs the action bound to the button.

        Parameters
        ----------
        data : list[int]
            Standard MIDI message.
        """
        id = data[0]

        if self.paused:
            if self.paused_button_callback is not None:
                self.paused_button_callback(id)
        else:
            self.actions_handler.handle_button_action(id)

    def handle_knob_message(self, data: list[int]) -> None:
        """Runs the action bound to the knob turn, specified in
        `actions_handler`.

        Parameters
        ----------
        data : list[int]
            Standard MIDI message.
        """
        id = data[0]
        velocity = data[1]

        if self.paused:
            self.paused_knob_callback(id)
        else:
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

    def send_midi_message(self, data: list[int]) -> None:
        """Sends the specified MIDI message.

        Parameters
        ----------
        data : list[int]
            Standard MIDI message.
        """
        try:
            self.midi_out.send_message(data)
            logging.debug(f"Sent: {data}")
        except ValueError as err:
            logging.error(f"Value Error: {err}")

    @staticmethod
    def check_set_and_run(
        func: Callable[[], None], id: int, mutex: QMutex, id_set: set[int]
    ) -> None:
        """Checks if the provided set contains `id`.
        It executes `func` if it doesn't and does nothing otherwise.

        Parameters
        ----------
        func : Callable[[], None]
            Function to execute.
        id : int
            Id for which we check provided set.
        mutex : QMutex
            Mutex for ensuring that checking `id` presence is
            mutually exclusive.
        id_set : set[int]
            Set containing ids.
        """
        already_flashing = False
        with QMutexLocker(mutex):
            if id in id_set:
                already_flashing = True
            else:
                id_set.add(id)

        if not already_flashing:
            func()
            with QMutexLocker(mutex):
                id_set.remove(id)

    def flash_knob(self, id: int) -> None:
        """Flashes the LEDs corresponding to a knob on a MIDI controller.

        Parameters
        ----------
        id : int
            Id of the knob.
        """
        current_value = self.knob_engagement[id]
        sleep_seconds = 0.04
        intervals = 14
        min_max_diff = self.controller.knob_value_max - self.controller.knob_value_min

        def light_up_func():
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

        self.check_set_and_run(light_up_func, id, self.knobs_mutex, self.flashing_knobs)

    def flash_button(self, id: int) -> None:
        """Flashes the button LED on a MIDI controller.

        Parameters
        ----------
        id : int
            Id of the button.
        """
        sleep_seconds = 0.3

        def light_up_func():
            for _ in range(3):
                self.turn_on_button_led(id)
                time.sleep(sleep_seconds)
                self.turn_off_button_led(id)
                time.sleep(sleep_seconds)

        self.check_set_and_run(
            light_up_func, id, self.buttons_mutex, self.flashing_buttons
        )

    def build_message(
        self,
        command: int,
        channel: int,
        data: list[int],
    ) -> list[int]:
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
        channel = self.controller.default_channel

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
        channel = self.controller.default_channel

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
        channel = self.controller.default_channel

        data = self.build_message(
            ControllerConstants.BUTTON_DISENGAGED_COMMAND,
            channel,
            [id, self.controller.button_value_off],
        )

        self.send_midi_message(data)

    def handle_midi_message(self, command: int, channel: int, data: list[int]) -> None:
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
        data : list[int]
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
            self.force_synchronize[id] = True
            self.handle_button_disengagement(data)
        else:
            logging.debug(
                f"id: {id}, command: {command}, channel: {channel}, data: {data}"
            )
