from napari._app_model._app import get_app
from napari._app_model.constants._commands import CommandId


def toggle_viewer_scale_bar():
    """An example showing how to execute commands."""
    command_id = CommandId.TOGGLE_VIEWER_SCALE_BAR

    # It is necessary to use `execute_command` to execute commands as it
    # automatically injects missing arguments into the callback function.
    get_app().commands.execute_command(command_id)
