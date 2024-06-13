from pathlib import Path
from typing import Optional

from .utils import YamlBaseModel


class AppState(YamlBaseModel):
    """Schema of data StateManager should remember between sessions.

    Attributes
    ----------
    selected_controller_path : Optional[Path]
        The path of the file with selected controller setup.
    selected_binds_path: Optional[Path]
        The path of the file with selected binds setup.
    selected_midi_in: Optional[str]
        Selected MIDI input port.
    selected_midi_out: Optional[str]
        Selected MIDI output port.
    recent_binds_for_controller: dict[Path, Optional[Path]]
        Mapping between each controller and which binds setup was last used.
    recent_midi_ports_for_controller: dict[Path, dict[str, Optional[str]]]
        Mapping between controllers and the last used MIDI ports (in/out)
    """

    selected_controller_path: Optional[Path]
    selected_binds_path: Optional[Path]
    selected_midi_in: Optional[str]
    selected_midi_out: Optional[str]

    recent_binds_for_controller: dict[Path, Optional[Path]]
    recent_midi_ports_for_controller: dict[Path, dict[str, Optional[str]]]
