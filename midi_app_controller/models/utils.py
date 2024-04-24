import os
from pathlib import Path
from typing import Optional, Any

from pydantic import BaseModel
import yaml


class YamlBaseModel(BaseModel):
    @classmethod
    def load_from(cls, path: Path) -> "YamlBaseModel":
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

    @classmethod
    def load_all_from(cls, directory: Path) -> list[tuple["YamlBaseModel", Path]]:
        """Creates models initialized with data from all YAML files in directory.

        Parameters
        ----------
        directory : Path
            YAML files directory.

        Returns
        -------
        list[tuple[cls, Path]]
            List of created models with paths to corresponding YAML files.
        """
        return [
            (
                cls.load_from(os.path.join(directory, filename)),
                os.path.join(directory, filename),
            )
            for filename in os.listdir(directory)
            if filename.lower().endswith((".yaml", ".yml"))
        ]

    def save_to(self, path: Path) -> None:
        """Saves the model's data to a YAML file.

        Parameters
        ----------
        path : Path
            YAML file path.
        """
        with open(path, "w") as f:
            yaml.safe_dump(
                self.dict(),
                f,
                default_flow_style=False,  # collections always serialized in the block style
                sort_keys=False,  # keys in the order of declaration
            )


def find_duplicate(values: list[Any]) -> Optional[Any]:
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
