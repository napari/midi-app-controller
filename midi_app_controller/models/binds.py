from typing import List, Optional
from pydantic import BaseModel, Field, root_validator

from .utils import YamlBaseModel, find_duplicate


class ButtonBind(BaseModel):
    """
    Information about an action bound to a button.

    Attributes
    ----------
    button_id : int
        The id of the button. Should be in the range [0, 127].
    action_name : int
        A name of the action to be executed when the button is pressed.
    """

    button_id: int = Field(ge=0, le=127)
    action_name: str


class KnobBind(BaseModel):
    """
    Information about actions bound to a knob.

    Attributes
    ----------
    knob_id : int
        The id of the knob. Should be in the range [0, 127].
    action_name_increase : str
        A name of the action to be executed when the knob's value increases.
    action_name_decrease : str
        A name of the action to be executed when the knob's value decreases.
    """

    knob_id: int = Field(ge=0, le=127)
    action_name_increase: str
    action_name_decrease: str


class Binds(YamlBaseModel):
    """
    User's binds for specific app and controller.

    Attributes
    ----------
    name : str
        The name of the binds set.
    description : Optional[str]
        Additional information that the user may provide.
    app_name : str
        For which app are the binds intended.
    controller_name : str
        For which controller are the binds intended.
    button_binds : List[ButtonBind]
        A list of bound buttons.
    knob_binds : List[KnobBind]
        A list of bound knobs.
    """

    name: str
    description: Optional[str]
    app_name: str
    controller_name: str
    button_binds: List[ButtonBind]
    knob_binds: List[KnobBind]

    @root_validator
    @classmethod
    def check_duplicate_ids(cls, values):
        """Ensures that every element has different id."""
        button_ids = list(map(lambda x: x.button_id, values.get("button_binds")))
        knob_ids = list(map(lambda x: x.knob_id, values.get("knob_binds")))

        duplicate = find_duplicate(button_ids + knob_ids)
        if duplicate is not None:
            raise ValueError(f"id={duplicate} was bound to multiple actions")

        return values
