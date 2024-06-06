import os
from collections.abc import Iterable
from pathlib import Path

import appdirs


class Config:
    """Class that stores configuration.

    Attributes
    ----------
    BINDS_READONLY_DIR : Path
        Path to readonly binds shipped with the library.
    BINDS_USER_DIR : Path
        Path to binds owned by the user.
    BINDS_DIRS : list[Path]
        List of all paths where binds can be found.
    BINDS_READONLY_DIR : Path
        Path to readonly controller schemas shipped with the library.
    CONTROLLERS_USER_DIR : Path
        Path to controller schemas owned by the user.
    CONTROLLER_DIRS : list[Path]
        List of all paths where controller schemas can be found.
    APP_STATE_FILE : Path
        Path to a file where recent settings are saved.
    """

    _APP_NAME = "MIDI App Controller"
    _CONFIG_DIR = (Path(__file__) / "../config_files").resolve().absolute()
    _USER_CONFIG_DIR = (Path(appdirs.user_config_dir(appname=_APP_NAME))).absolute()
    _USER_STATE_DIR = (Path(appdirs.user_state_dir(appname=_APP_NAME))).absolute()

    BINDS_READONLY_DIR: Path = _CONFIG_DIR / "binds"
    BINDS_USER_DIR: Path = _USER_CONFIG_DIR / "binds"
    BINDS_DIRS: tuple[Path, ...] = (BINDS_READONLY_DIR, BINDS_USER_DIR)

    CONTROLLERS_READONLY_DIR: Path = _CONFIG_DIR / "controllers"
    CONTROLLERS_USER_DIR: Path = _USER_CONFIG_DIR / "controllers"
    CONTROLLER_DIRS: tuple[Path, ...] = (CONTROLLERS_READONLY_DIR, CONTROLLERS_USER_DIR)

    APP_STATE_FILE: Path = _USER_STATE_DIR / "app_state.yaml"


def get_yaml_files_in_dirs(directories: Iterable[Path]) -> list[Path]:
    """Returns paths of all `.yaml` or `.yml` files in `directories`."""
    return [
        directory / filename
        for directory in directories
        if directory.exists()
        for filename in os.listdir(directory)
        if filename.lower().endswith((".yaml", ".yml"))
    ]
