import os
from pathlib import Path
import appdirs


class Config:
    """Class that stores configuration."""

    _CONFIG_DIR = (Path(__file__) / "../../config_files").resolve().absolute()
    _USER_CONFIG_DIR = (Path(appdirs.user_config_dir(appname="MIDI App Controller")) / "config").absolute()

    BINDS_READONLY_DIR: Path = _CONFIG_DIR / "binds"
    BINDS_USER_DIR: Path = _USER_CONFIG_DIR / "binds"
    BINDS_DIRS: tuple[Path, ...] = (BINDS_READONLY_DIR, BINDS_USER_DIR)

    CONTROLLERS_READONLY_DIR: Path = _CONFIG_DIR / "controllers"
    CONTROLLERS_USER_DIR: Path = _USER_CONFIG_DIR / "controllers"
    CONTROLLER_DIRS: tuple[Path, ...] = (CONTROLLERS_READONLY_DIR, CONTROLLERS_USER_DIR)

    APP_STATE_FILE: Path = _USER_CONFIG_DIR / "app_state.yaml"



def get_yaml_files_in_dirs(directories) -> list[Path]:
    return [
        directory / filename
        for directory in directories
        if directory.exists()
        for filename in os.listdir(directory)
        if filename.lower().endswith((".yaml", ".yml"))
    ]
