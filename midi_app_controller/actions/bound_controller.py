import logging
from typing import Optional

from app_model.types import CommandRule
from pydantic import BaseModel, Field

from midi_app_controller.models.binds import Binds
from midi_app_controller.models.controller import Controller


class ButtonActions(BaseModel):
    """Action bound to a button.

    Attributes
    ----------
    action_press : CommandRule
        Action to be executed when the button is pressed.
    """

    action_press: CommandRule


class KnobActions(BaseModel):
    """Actions bound to a knob.

    Attributes
    ----------
    action_increase : Optional[CommandRule]
        Action to be executed when the knob's value increases.
    action_decrease : Optional[CommandRule]
        Action to be executed when the knob's value decreases.
    """

    action_increase: Optional[CommandRule]
    action_decrease: Optional[CommandRule]


class BoundController(BaseModel):
    """A controller with actions bound to its elements.

    Attributes
    ----------
    knob_value_min : int
        The minimum value sent by the controller when a knob is rotated.
        Should be in the range [0, 127].
    knob_value_max : int
        The maximum value sent by the controller when a knob is rotated.
        Should be in the range [0, 127].
    buttons : dict[int, ButtonActions]
        All actions for a button with given id.
    knobs : dict[int, KnobActions]
        All actions for a knob with given id.
    """

    knob_value_min: int = Field(ge=0, le=127)
    knob_value_max: int = Field(ge=0, le=127)
    buttons: dict[int, ButtonActions]
    knobs: dict[int, KnobActions]

    @classmethod
    def create(
        cls, *, binds: Binds, controller: Controller, actions: list[CommandRule]
    ) -> "BoundController":
        """Creates an instance of `BoundController`.

        Ensures that the arguments are valid, i.e., all needed actions exist,
        binds are intended for the provided controller, and all the bound
        elements exist on the controller.

        Parameters
        ----------
        binds : Binds
            Information about binds.
        controller : Controller
            Information about the controller the binds are for.
        actions : list[CommandRule]
            List of actions available in the application the binds are for.

        Returns
        -------
        BoundController
            A created model.

        Raises
        ------
        ValueError
            If the provided arguments are invalid together.
        """

        # Check if the binds and the controller are intended to be used together.
        if controller.name != binds.controller_name:
            raise ValueError(
                f"tried to use binds intended for '{binds.controller_name}'"
                f"with controller '{controller.name}'"
            )

        # Create a dictionary to retrieve actions by id faster.
        actions_dict = {action.id: action for action in actions}

        # Find actions for all bound buttons.
        bound_buttons = {}
        for bind in binds.button_binds:
            action = actions_dict.get(bind.action_id)
            if action is None:
                logging.warning(f"bound action '{bind.action_id}' cannot be found")
            else:
                bound_buttons[bind.button_id] = ButtonActions(action_press=action)

        # Find actions for all bound knobs.
        bound_knobs = {}
        for bind in binds.knob_binds:
            action_increase = actions_dict.get(bind.action_id_increase)
            action_decrease = actions_dict.get(bind.action_id_decrease)
            if bind.action_id_increase is not None and action_increase is None:
                logging.warning(
                    f"bound action '{bind.action_id_increase}' cannot be found"
                )
            if bind.action_id_decrease is not None and action_decrease is None:
                logging.warning(
                    f"bound action '{bind.action_id_decrease}' cannot be found"
                )
            bound_knobs[bind.knob_id] = KnobActions(
                action_increase=action_increase,
                action_decrease=action_decrease,
            )

        # Check if all bound buttons are elements of the controller.
        bound_button_ids = set(bound_buttons.keys())
        controller_button_ids = {button.id for button in controller.buttons}
        if not bound_button_ids <= controller_button_ids:
            raise ValueError("one of bound button ids is not on the controller")

        # Check if all bound knobs are elements of the controller.
        bound_knob_ids = set(bound_knobs.keys())
        controller_knobs_ids = {knob.id for knob in controller.knobs}
        if not bound_knob_ids <= controller_knobs_ids:
            raise ValueError("one of bound knob ids is not on the controller")

        return cls(
            knob_value_min=controller.knob_value_min,
            knob_value_max=controller.knob_value_max,
            buttons=bound_buttons,
            knobs=bound_knobs,
        )

    def get_button_press_action(self, button_id: int) -> Optional[CommandRule]:
        """Finds the action to be executed when a button is pressed.

        Returns None if there is no such action.
        """
        button = self.buttons.get(button_id)
        if button is not None:
            return button.action_press

    def get_knob_increase_action(self, knob_id: int) -> Optional[CommandRule]:
        """Finds action to be executed when knob's value is increased.

        Returns None if there is no such action.
        """
        knob = self.knobs.get(knob_id)
        if knob is not None:
            return knob.action_increase

    def get_knob_decrease_action(self, knob_id: int) -> Optional[CommandRule]:
        """Finds action to be executed when knob's value is decreased.

        Returns None if there is no such action.
        """
        knob = self.knobs.get(knob_id)
        if knob is not None:
            return knob.action_decrease
