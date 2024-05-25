import datetime
import re
from typing import Callable

from qtpy.QtCore import QThread


class SimpleQThread(QThread):
    """QThread responsible for running a function.

    Attributes
    ----------
    func : Callable[[], None]
        Function to be called.
    """

    def __init__(self, func: Callable[[], None]):
        super().__init__()
        self.func = func

    def run(self):
        """Runs the function."""
        self.func()


def get_copy_name(current_name: str) -> str:
    """Finds a good name for a copy of a file.

    Currently adds "({timestamp} copy)" to the end of the name, or replaces
    the timestamp with current time if already present.
    """
    if m := re.fullmatch(r"(.*) \([0-9. -]* copy\)", current_name):
        current_name = m.group(1)
    timestamp = datetime.datetime.now().isoformat().replace(":", "-").replace("T", " ")
    return f"{current_name} ({timestamp} copy)"
