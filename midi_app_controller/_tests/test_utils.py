import datetime
from unittest.mock import patch

import pytest

from ..utils import SimpleQThread, get_copy_name


@pytest.mark.parametrize(
    "name",
    [
        "name",
        "",
        " ",
        "abc.txt",
        "abc-x-.txt.txt",
    ],
)
@patch("midi_app_controller.utils.datetime")
def test_new_copy_name(mock_datetime, name):
    mock_datetime.datetime.now.return_value = datetime.datetime(2024, 5, 18, 15, 30, 45)
    expected_timestamp = "2024-05-18 15-30-45"

    assert get_copy_name(name) == f"{name} ({expected_timestamp} copy)"


@pytest.mark.parametrize(
    "real_name, name",
    [
        ("name", "name (2022-01-11 11-31-41 copy)"),
        (" ", "  (2022-01-11 11-31-41 copy)"),
    ],
)
@patch("midi_app_controller.utils.datetime")
def test_new_copy_name_when_already_with_timestamp(mock_datetime, real_name, name):
    mock_datetime.datetime.now.return_value = datetime.datetime(2024, 5, 18, 15, 30, 45)
    expected_timestamp = "2024-05-18 15-30-45"

    assert get_copy_name(name) == f"{real_name} ({expected_timestamp} copy)"


def test_simple_qthread():
    thread = SimpleQThread(lambda: None)
    thread.run()
    thread.start()
    thread.wait()
