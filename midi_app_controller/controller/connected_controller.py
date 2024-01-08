from app_model.types import Action
from typing import Dict, List, Set, Optional
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass

from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller
from ..actions.bound_controller import BoundController, KnobActions, ButtonActions
from ..actions.actions_handler import ActionsHandler

from rtmidi import MidiIn, MidiOut
import rtmidi
from .controller_constants import *

def midi_callback(message, time_stamp, data):
    # Process MIDI message here
    status_byte = message[0][0]
    command = (status_byte & 0xF0)
    channel = (status_byte & 0x0F)
    data_bytes = message[0][1:]

    data.dupa()
    print(f"Command: {command}, Channel: {channel}, Data: {data_bytes}")

class ConnectedController(BaseModel):
    """A controller connected to the physical device capable of 
    sending and receiving signals

    Attributes
    ----------
    bound_controller : BoundController
    """

    actions_handler : ActionsHandler
    midi_in : rtmidi.MidiIn
    midi_out : rtmidi.MidiOut
    button_ids : List[int]
    knob_ids : List[int]

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create(
        cls, *, actions_handler : ActionsHandler
    ) -> "ConnectedController":
        """Creates an instance of `ConnectedController`.

        Parameters
        ----------
    
        Returns
        -------
        ConnectedController
            A created model.

        Raises
        ------
        ValueError
            If the provided arguments are invalid together.
        """
        
        bound_controller = actions_handler.bound_controller
        button_ids = set(bound_controller.buttons.keys())
        knob_ids = set(bound_controller.knobs.keys())
        midi_in = None
        midi_out = None

        try:
            # Create an instance of MidiIn and MidiOut
            midi_in = rtmidi.MidiIn()
            midi_out = rtmidi.MidiOut()

            # Listing available MIDI ports
            available_ports_in = midi_in.get_ports()
            available_ports_out = midi_out.get_ports()

            available_ports = [port \
                for port in available_ports_in \
                if port in available_ports_out]
            
            controller_port = ""
            port_index = -1

            if available_ports:
                for i, port in enumerate(available_ports):
                    name = port.split(":")[0]
                    if name == bound_controller.name:
                        controller_port = port
                        port_index = i
            
            if controller_port == "":
                raise IOError("No correct MIDI ports available.")
            
            print(f"port index {i}")
            #Creating MidiIn and MidiOut instances
            midi_in.open_port(port_index)
            midi_out.open_port(port_index)

        except TypeError as err:
            print(f"Type Error: {err}")
        except SystemError as err:
            print(f"System Error: {err}")
        except rtmidi.InvalidPortError as err:
            print(f"Invalid Port Error: {err}")
        except rtmidi.InvalidUseError as err:
            print(f"Invalid Use Error: {err}")

        instance = cls(
            actions_handler = actions_handler,
            midi_out = midi_out,
            midi_in = midi_in,
            button_ids = button_ids,
            knob_ids = knob_ids,
        )

        return instance

    def __del__(self):
        self.midi_in.close_port()
        self.midi_in.delete()
        self.midi_out.close_port()
        self.midi_out.delete()

    # def create_callback_to_self(self):
    #     def midi_callback(message, time_stamp):
    #         # Process MIDI message here
    #         status_byte = message[0][0]
    #         command = (status_byte & 0xF0)
    #         channel = (status_byte & 0x0F)
    #         data_bytes = message[0][1:]
    
    #         self.handle_midi_message(
    #             command=command,
    #             channel=channel,
    #             data=data_bytes
    #         )

    #         print(f"Command: {command}, Channel: {channel}, Data: {data_bytes}")
    #         print(self.name)

    #     return midi_callback

    def dupa(self):
        print("dupa")

    def set_midi_in_callback(self, function):
        function([[0xBB, 1, 100], 1], 1, self)
        self.midi_in.set_callback(function, data=self)

    def handle_button_engagement(self, command, channel, data):
        id = data[0]
        velocity = data[1]

        self.action_handler.handle_button_action(
            button_id=id,
        )

    def handle_button_disengagement(self, command, channel, data):
        pass #TODO: for now we're not handling button disengagement

    def handle_knob_message(self, command, channel, data):
        id = data[0]
        velocity = data[1]

        self.action_handler.handle_knob_action(
            knob_id=id,
            old_value=0, #TODO: we're not keeping old value anywhere for now
            new_value=velocity,
        )

    def send_midi_message(self, data):
        try:
            self.midi_out.send_message(data)
        except ValueError as err:
            print(f"Value Error: {err}")

    def turn_on_knob_backlight(self, id):
        postion = self.turn_knob_id_to_position(id)
        data = [knob_value_change_command, postion, 27]
        self.send_midi_message(data)

    def turn_on_button_led(self, id):
        postion = self.turn_button_id_to_position(id)
        data = [button_engaged_command, postion, 1]
        self.send_midi_message(data)

    def turn_off_button_led(self, id):
        postion = self.turn_button_id_to_position(id)
        data = [button_disengaged_command, postion, 0]
        self.send_midi_message(data)
        

    def turn_knob_id_to_position(self, id) -> int:
        if id >= B_knob_layer_id:
            id = id - B_knob_layer_id
        elif id >= A_knob_layer_id:
            id = id - A_knob_layer_id
        else:
            raise ValueError(
                    f"knob '{id}' cannot be found"
                )
        
        return id
    
    def turn_button_id_to_position(self, id) -> int:
        if id >= B_button_layer_id:
            id = id - B_button_layer_id
        elif id >= A_button_layer_id:
            id = id - A_button_layer_id
        else:
            raise ValueError(
                    f"button '{id}' cannot be found"
                )
        
        return id
            
    def handle_midi_message(self, command, channel, data):
        id = data[0]

        if id in self.knob_ids:
            self.handle_knob_message(command, channel, data)
        elif id in self.knob_ids and command == button_engaged_command:
            self.handle_button_engagement(command, channel, data)
        elif id in self.knob_ids and command == button_disengaged_command:
            self.handle_button_disengagement(command, channel, data)
        else:
            raise ValueError(
                    f"action '{id}' cannot be found"
                )
