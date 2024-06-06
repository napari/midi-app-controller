import platform
import subprocess
from pathlib import Path
from typing import Callable, Optional, TypeVar

from app_model.types import CommandRule
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget

HIGHLIGHT_STYLE_SHEET = "background-color: SeaGreen"
HIGHLIGHT_DURATION_MS = 1000
T = TypeVar("T")


class DynamicQComboBox(QComboBox):
    """QComboBox that refreshes the list of items each time it is opened."""

    def __init__(
        self,
        current_item: Optional[T],
        get_items: Callable[[], list[T]],
        select_item: Callable[[T], None],
        get_item_label: Callable[[T], str] = str,
        parent: QWidget = None,
    ):
        """Creates DynamicQComboBox widget.

        Parameters
        ---------
        current_item : Optional[T]
            Optional default item.
        get_items : Callable[[], list[T]]
            Function that fetches the list of current items. An option
            corresponding to "None" will be added anyway.
        select_item : Callable[[T], None]
            Function that should be called when the user chooses an option.
        get_item_label : Callable[[T], str]
            Function that returns a label corresponding to an item. Doesn't
            have to accept the "None" option.
        parent : QWidget
            Parent widget.
        """
        super().__init__(parent)

        self.get_items = lambda: [None] + get_items()
        self.get_item_label = get_item_label
        self.activated.connect(lambda _: select_item(self.currentData()))

        self.refresh_items()
        self.set_current(current_item)

    def set_current(
        self, item: Optional[T], _items: Optional[list[Optional[T]]] = None
    ):
        """Sets the currently selected item.

        Does not select the item if it's not in the list returned by get_items().
        If provided, _items is used instead of calling get_items().
        """
        items = _items if _items is not None else self.get_items()
        self.setCurrentIndex((items + [item]).index(item))

    def refresh_items(self):
        """Refresh the list of items. Optionally set currently selected item."""

        # Note that the objects in here may be equal to the objects that were
        # returned last time but not be exactly the same objects.
        new_items = self.get_items()

        current_item = self.currentData()
        self.clear()
        for item in new_items:
            label = self.get_item_label(item) if item is not None else "(none)"
            self.addItem(label, userData=item)
        self.set_current(current_item, _items=new_items)

    def showPopup(self):
        self.refresh_items()
        super().showPopup()


class ActionsQComboBox(QComboBox):
    """QComboBox that allows to search available actions.

    It also supports switching the display text for each action between
    its title and its id.
    """

    def __init__(
        self,
        actions: list[CommandRule],
        default_action_id: Optional[str],
        parent: QWidget = None,
    ):
        """Creates ActionsQComboBox widget.

        Parameters
        ---------
        actions: list[CommandRule]
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

    def wheelEvent(self, event):
        # Ignore the wheel event to prevent changing items on scroll.
        event.ignore()


def is_subpath(path: Path, subpath: Path) -> bool:
    """Checks if one path represents a file/directory inside the other directory."""
    path_str = str(path.resolve().absolute())
    subpath_str = str(subpath.resolve().absolute())
    return subpath_str.startswith(path_str)


def reveal_in_explorer(file: Path):
    """Show where the file is in the system's file explorer.

    Currently only Windows, Linux (majority of distributions), and macOS are
    supported. On Linux, only the folder is opened.
    """
    assert file.is_file(), "Not a valid file"
    if platform.system() == "Windows":
        subprocess.Popen(f'explorer /select,"{file}"')
    elif platform.system() == "Linux":
        subprocess.Popen(["xdg-open", str(file.parent)])
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", "-R", str(file)])
    else:
        raise NotImplementedError("Only Linux, Windows, and macOS are supported")


def vertical_layout(label: str, widget: QWidget) -> QVBoxLayout:
    """Creates vertical layout consisting of the `label` and `widget`."""
    layout = QVBoxLayout()
    layout.addWidget(QLabel(label))
    layout.addWidget(widget)
    return layout
