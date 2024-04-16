from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, root_validator

from .utils import YamlBaseModel

class AppState(YamlBaseModel):
  """"""

  selected_controller_path : Optional[Path]
  selected_binds_path: Optional[Path]
  selected_midi_in: Optional[str]
  selected_midi_out: Optional[str]

  recent_binds_for_controller: dict[Path, Optional[Path]]
