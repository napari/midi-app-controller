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
