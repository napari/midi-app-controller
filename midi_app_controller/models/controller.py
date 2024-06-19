from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .utils import YamlBaseModel, find_duplicate


class ControllerElement(BaseModel):
    """Any element of a controller.

    Attributes
    ----------
    id : int
        The ID of the element that the controller sends with every event.
        Should be in the range [0, 127].
    name : str
        A user-defined name for the element that helps to differentiate elements.
        Cannot be empty.
    """

    id: int = Field(ge=0, le=127)
    name: str = Field(min_length=1)


class Controller(YamlBaseModel):
    """A controller's schema.

    Attributes
    ----------
    name : str
        The name of the controller. Cannot be empty. Must be unique among all schemas.
    button_value_off : int
        The number sent by the controller when a button is in 'off' state.
        Should be in the range [0, 127].
    button_value_on : int
        The number sent by the controller when a button is in 'on' state.
        Should be in the range [0, 127].
    knob_value_min : int
        The minimum value sent by the controller when a knob is rotated.
        Should be in the range [0, 127].
    knob_value_max : int
        The maximum value sent by the controller when a knob is rotated.
        Should be in the range [0, 127].
    default_channel : int
        The default channel which MIDI messages will be sent on. Should
        be in the range [1, 16].
    preferred_midi_in : Optional[str]
        MIDI input name that is preferred for this controller.
    preferred_midi_out : Optional[str]
        MIDI output name that is preferred for this controller.
    buttons : list[ControllerElement]
        List of available buttons on the controller.
    knobs : list[ControllerElement]
        List of available knobs on the controller.
    """

    name: str = Field(min_length=1)
    button_value_off: int = Field(ge=0, le=127)
    button_value_on: int = Field(ge=0, le=127)
    knob_value_min: int = Field(ge=0, le=127)
    knob_value_max: int = Field(ge=0, le=127)
    default_channel: int = Field(ge=1, le=16)
    preferred_midi_in: Optional[str] = None
    preferred_midi_out: Optional[str] = None
    buttons: list[ControllerElement]
    knobs: list[ControllerElement]

    @model_validator(mode="after")
    @classmethod
    def check_duplicate_ids(cls, values):
        """Ensures that every button and every knob has a different id."""
        button_ids = [elem.id for elem in values.buttons]
        knob_ids = [elem.id for elem in values.knobs]

        duplicate = find_duplicate(button_ids)
        if duplicate is not None:
            raise ValueError(f"id={duplicate} was used for multiple buttons")

        duplicate = find_duplicate(knob_ids)
        if duplicate is not None:
            raise ValueError(f"id={duplicate} was used for multiple knobs")

        return values

    @field_validator("buttons", "knobs", mode="after")
    @classmethod
    def check_duplicate_names(
        cls, v: list[ControllerElement]
    ) -> list[ControllerElement]:
        """Ensures that no two elements of same kind have the same name."""
        names = [elem.name for elem in v]

        duplicate = find_duplicate(names)
        if duplicate is not None:
            raise ValueError(f"name={duplicate} was used for multiple elements")

        return v

    @model_validator(mode="after")
    @classmethod
    def check_button_values(cls, values):
        """Ensures that the 'off' and 'on' values for buttons are different."""
        if values.button_value_off == values.button_value_on:
            raise ValueError("button_value_off and button_value_on are equal")
        return values

    @model_validator(mode="after")
    @classmethod
    def check_knob_values(cls, values):
        """Ensures that the minimum value of knobs is smaller than the maximum value."""
        if values.knob_value_min >= values.knob_value_max:
            raise ValueError("knob_value_min must be smaller than knob_value_max")
        return values
