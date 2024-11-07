from typing import Optional

from pydantic import BaseModel, Field, model_validator

from .utils import YamlBaseModel, find_duplicate


class ButtonBind(BaseModel):
    """Information about an action bound to a button.

    Attributes
    ----------
    button_id : int
        The id of the button. Should be in the range [0, 127].
    action_id : str
        The id of an action to be executed when the button is pressed.
    """

    button_id: int = Field(ge=0, le=127)
    action_id: str


class KnobBind(BaseModel):
    """Information about actions bound to a knob.

    Attributes
    ----------
    knob_id : int
        The id of the knob. Should be in the range [0, 127].
    action_id_increase : str
        The id of an action to be executed when the knob's value increases.
    action_id_decrease : str
        The id of an action to be executed when the knob's value decreases.
    """

    knob_id: int = Field(ge=0, le=127)
    action_id_increase: Optional[str]
    action_id_decrease: Optional[str]


class Binds(YamlBaseModel):
    """User's binds for specific app and controller.

    Attributes
    ----------
    name : str
        The name of the binds set. Cannot be empty. Must be unique among all binds sets.
    app_name : str
        For which app are the binds intended. Cannot be empty.
    controller_name : str
        For which controller are the binds intended. Cannot be empty.
    button_binds : list[ButtonBind]
        A list of bound buttons.
    knob_binds : list[KnobBind]
        A list of bound knobs.
    """

    name: str = Field(min_length=1)
    app_name: str = Field(min_length=1)
    controller_name: str = Field(min_length=1)
    description: Optional[str] = None
    button_binds: list[ButtonBind]
    knob_binds: list[KnobBind]

    @model_validator(mode="after")
    @classmethod
    def check_duplicate_ids(cls, values):
        """Ensures that every element has different id."""
        button_ids = [bind.button_id for bind in values.button_binds]
        knob_ids = [bind.knob_id for bind in values.knob_binds]

        duplicate_buttons = find_duplicate(button_ids)
        if duplicate_buttons is not None:
            raise ValueError(
                f"button id={duplicate_buttons} was bound to multiple actions"
            )

        duplicate_knobs = find_duplicate(knob_ids)
        if duplicate_knobs is not None:
            raise ValueError(f"knob id={duplicate_knobs} was bound to multiple actions")

        return values
