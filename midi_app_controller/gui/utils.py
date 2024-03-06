from typing import Callable, List, Optional

from qtpy.QtCore import Qt
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
        # Refresh items.
        self.clear()
        self.addItems(self.get_items())

        super().showPopup()


class SearchableQComboBox(QComboBox):
    """QComboBox that allows to search available items."""

    def __init__(
        self,
        items: List[str],
        default_item: Optional[str] = None,
        parent: QWidget = None,
    ):
        """Creates SearchableQComboBox widget.

        Parameters
        ---------
        items : List[str]
            List of available items.
        default_item : Optional[str]
            Optional default item used to initialize the widget.
        parent : QWidget
            Parent widget.
        """
        super().__init__(parent)

        # Make searchable.
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)

        # Add items.
        self.addItems(items)
        self.setCurrentText(default_item)

        # Set filter mode.
        self.completer().setFilterMode(Qt.MatchContains)
