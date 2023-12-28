import pytest

from ..utils import find_duplicate


@pytest.mark.parametrize(
    "values, result",
    [
        ([1, 2, 3], None),
        (["a", "b"], None),
        ([1, 2, 3, 1, 4], 1),
        ([1, 2, 1, 2], 1),
        ([], None),
    ],
)
def test_find_duplicate(values, result):
    assert find_duplicate(values) == result
