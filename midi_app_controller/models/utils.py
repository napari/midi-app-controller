from pathlib import Path

from pydantic import BaseModel
from typing import Any, List, Optional
import yaml


class YamlBaseModel(BaseModel):
    @classmethod
    def load_from(cls, path: Path):
        """Creates a model initialized with data from a YAML file.

        Parameters
        ----------
        path : Path
            YAML file path.

        Returns
        -------
        cls
            A created model.
        """
        with open(path) as f:
            data = yaml.safe_load(f)
            return cls(**data)

    def save_to(self, path: Path):
        """Saves the model's data to a YAML file.

        Parameters
        ----------
        path : Path
            YAML file path.
        """
        with open(path, "w") as f:
            yaml.safe_dump(self.dict(), f, default_flow_style=False)


def find_duplicate(values: List[Any]) -> Optional[Any]:
    """Checks if there are any duplicates in the list and returns the first one.

    Parameters
    ----------
    values : list
        The list of values to be searched for duplicates.

    Returns
    -------
    Any
        The first duplicate if it exists.
    None
        If there are no duplicates.
    """
    seen = set()
    for val in values:
        if val in seen:
            return val
        seen.add(val)
    return None
