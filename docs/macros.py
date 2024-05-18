from pathlib import Path


def define_env(env):
    """Hook functions"""

    # Replace paths to images pointing to inside the docs/ folder so that the
    # paths are correct when readme is imported.
    @env.macro
    def include_readme():
        return Path("README.md").read_text("utf8").replace("](docs/img/", "](img/")
