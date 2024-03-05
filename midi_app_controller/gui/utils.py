from typing import Callable, List, Optional

from qtpy.QtWidgets import QComboBox, QWidget


class DynamicQComboBox(QComboBox):
    """QComboBox that refreshes the list of items each time it is opened."""

    def __init__(
        self,
        current_item: Optional[str],
        get_items: Callable[[], List[str]],
        select_item: Callable[[str], None],
        parent: QWidget = None,
    ):
        """Creates DynamicQComboBox widget.

        Parameters
        ---------
        current_item : Optional[str]
            Optional default item.
        get_items : Callable[[], List[str]]
            Functions that fetches list of current items.
        select_item : Callable[[str], None]
            Function that should be called when `textActivated` is emitted.
        parent : QWidget
            Parent widget.
        """
        super().__init__(parent)

        self.get_items = get_items

        self.textActivated.connect(select_item)
        self.setCurrentText(current_item)

    def showPopup(self):
        self.clear()
        self.addItems(self.get_items())
        super().showPopup()
