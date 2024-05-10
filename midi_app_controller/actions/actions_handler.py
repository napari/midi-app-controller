from typing import Optional

from app_model import Application
from superqt.utils import ensure_main_thread

from .bound_controller import BoundController


class ActionsHandler:
    """Allows to execute actions and get their state using ids of controller
    elements."""

    def __init__(
        self,
        *,
        bound_controller: BoundController,
        app: Application,
    ):
        """Initializes the handler.

        Parameters
        ----------
        bound_controller : BoundController
            Controller and binds that should be handled.
        app : Application
            Application where the actions will be executed.
        """
        self.bound_controller = bound_controller
        self.app = app

    def is_button_toggled(self, button_id: int) -> Optional[bool]:
        """Checks if the action associated with the button is toggled."""
        action = self.bound_controller.get_button_press_action(button_id)
        if action is not None and action.toggled is not None:
            store = self.app.injection_store
            return store.inject(action.toggled.get_current)()

    def get_knob_value(self, knob_id: int) -> Optional[int]:
        """Returns knob's value from the action associated with the knob."""
        raise NotImplementedError  # TODO It's not available in app-model.

    # Without `await_return` closing MIDI ports freezes after handling
    # at least two actions.
    @ensure_main_thread(await_return=True)
    def handle_button_action(self, button_id: int) -> None:
        """Executes an action associated with the button if it exists."""
        action = self.bound_controller.get_button_press_action(button_id)
        if action is not None:
            self.app.commands.execute_command(action.id)

    @ensure_main_thread(await_return=True)
    def handle_knob_action(
        self,
        *,
        knob_id: int,
        old_value: int,
        new_value: int,
    ) -> None:
        """Executes an action based on how the knob's value changed if it exists.

        Parameters
        ----------
        knob_id : int
            The id of the knob.
        old_value : int
            Value of the knob before it was rotated.
        new_value : int
            Received new value of the knob.
        """
        diff = new_value - old_value
        if diff >= 0:
            action = self.bound_controller.get_knob_increase_action(knob_id)
        else:
            action = self.bound_controller.get_knob_decrease_action(knob_id)

        # TODO How many times should the command be executed? Maybe we
        # should let the user set it while binding the knob?
        # When fetching current value of actions will be added to app_model,
        # we could also execute the action once, check how much value
        # changed, and then adjust the sensitivity accordingly.
        if action is not None:
            for _ in range(abs(diff)):
                self.app.commands.execute_command(action.id)
