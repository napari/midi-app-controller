import os


class Config:
    """ "Class that stores configuration."""

    # TODO Find better locations for config files.
    BINDS_DIRECTORY = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config_files", "binds"
        )
    )
    CONTROLLERS_DIRECTORY = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config_files", "controllers"
        )
    )
