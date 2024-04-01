from typing import Optional

from app_model.types import Action
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QComboBox, QWidget


class DynamicQComboBox(QComboBox):
    """QComboBox that refreshes the list of items each time it is opened."""

    def __init__(
        self,
        current_item: Optional[str],
        get_items: callable[[], list[str]],
        select_item: callable[[str], None],
        parent: QWidget = None,
    ):
        """Creates DynamicQComboBox widget.

        Parameters
        ---------
        current_item : Optional[str]
            Optional default item.
        get_items : callable[[], list[str]]
            Functions that fetches list of current items.
        select_item : callable[[str], None]
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


class ActionsQComboBox(QComboBox):
    """QComboBox that allows to search available actions.

    It also supports switching the display text for each action between
    its title and its id.
    """

    def __init__(
        self,
        actions: list[Action],
        default_action_id: Optional[str],
        parent: QWidget = None,
    ):
        """Creates ActionsQComboBox widget.

        Parameters
        ---------
        actions : list[Action]
            List of available actions.
        default_action_id : Optional[str]
            Optional default action used to initialize the widget.
        parent : QWidget
            Parent widget.
        """
        super().__init__(parent)

        # Add items.
        self.addItem(None)  # Empty item
        self.setCurrentIndex(0)
        for action in actions:
            self.addItem(action.id, action)

        # Find and select the default action.
        for i in range(self.count()):
            if self.itemText(i) == default_action_id:
                self.setCurrentIndex(i)
                break

        # We set `self.display_titles` to False and then toggle the names mode
        # because we only have the `default_action_id` so it's easier this way.
        self.display_titles = False
        self.toggle_names_mode()

        # Make searchable.
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.completer().setFilterMode(Qt.MatchContains)

    def toggle_names_mode(self) -> None:
        """Switches the display text for each action between its title and its id."""
        self.display_titles = not self.display_titles
        for i in range(self.count()):
            if (action := self.itemData(i)) is not None:
                if self.display_titles:
                    self.setItemText(i, action.title)
                else:
                    self.setItemText(i, action.id)

    def get_selected_action_id(self) -> Optional[str]:
        """Returns the id of currently selected action."""
        if (action := self.currentData()) is not None:
            return action.id
