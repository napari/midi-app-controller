from pathlib import Path

from ..config import get_yaml_files_in_dirs


def test_get_yaml_files_in_dirs():
    files = get_yaml_files_in_dirs(
        [
            (Path(__file__) / "../../config_files/controllers").resolve(),
            (Path(__file__) / "../../config_files/binds").resolve(),
        ]
    )
    controllers = get_yaml_files_in_dirs(
        [(Path(__file__) / "../../config_files/controllers").resolve()]
    )
    binds = get_yaml_files_in_dirs(
        [(Path(__file__) / "../../config_files/binds").resolve()]
    )

    assert len(files) >= 2
    assert len(files) == len(controllers) + len(binds)
    assert files == controllers + binds


def test_get_yaml_files_in_dirs_when_non_existent():
    files = get_yaml_files_in_dirs(
        [
            (Path(__file__) / "../../../abc").resolve(),
            (Path(__file__) / "../../../qwerty").resolve(),
        ]
    )

    assert len(files) == 0


def test_get_yaml_files_in_dirs_when_empty():
    files = get_yaml_files_in_dirs(
        [
            (Path(__file__) / "..").resolve(),
            (Path(__file__) / "..").resolve(),
        ]
    )

    assert len(files) == 0
