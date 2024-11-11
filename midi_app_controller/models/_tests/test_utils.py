import os
from pathlib import Path
from typing import Optional

import pytest
import yaml
from pydantic import ValidationError

from ..utils import YamlBaseModel, find_duplicate


class TempYamlModel(YamlBaseModel):
    key2: str
    key1: str
    key3: list[str]
    key4: Optional[int]


class OtherTempYamlModel(YamlBaseModel):
    other_key: str


@pytest.fixture
def yaml_data() -> dict:
    return {"key2": "value2", "key1": "value1", "key3": ["a", "b"], "key4": None}


@pytest.fixture
def other_yaml_data() -> dict:
    return {"other_key": "hello"}


@pytest.fixture
def yaml_str(yaml_data) -> str:
    dumped = yaml.safe_dump(yaml_data, default_flow_style=False, sort_keys=False)
    assert dumped == "key2: value2\nkey1: value1\nkey3:\n- a\n- b\nkey4: null\n"
    return dumped


@pytest.fixture
def yaml_file(tmp_path, yaml_str) -> Path:
    yaml_file = tmp_path / "sample.yaml"
    with open(yaml_file, "w") as f:
        f.write(yaml_str)
    return yaml_file


def test_load_from(yaml_file, yaml_data):
    model = TempYamlModel.load_from(yaml_file)

    assert isinstance(model, TempYamlModel)
    assert model.model_dump() == yaml_data


def test_load_from_when_invalid_data(yaml_file, yaml_data):
    with pytest.raises(ValidationError):
        OtherTempYamlModel.load_from(yaml_file)


def test_load_all_from_robustness(tmp_path, yaml_data, other_yaml_data):
    d1 = tmp_path / "1"
    os.mkdir(d1)
    d2 = tmp_path / "2"
    os.mkdir(d2)
    non_existent_dir = tmp_path / "none"
    with open(d1 / "m1.yaml", "w") as f:
        yaml.safe_dump(yaml_data, f)
    with open(d1 / "m2.yaml", "w") as f:
        yaml.safe_dump(other_yaml_data, f)
    with open(d2 / "m1.yml", "w") as f:
        yaml.safe_dump(yaml_data, f)
    with open(d2 / "distractor.txt", "w") as f:
        f.write("not relevant\n")
    with pytest.warns(UserWarning, match="Unable to load model"):
        models = TempYamlModel.load_all_from([d1, d2, non_existent_dir])
    assert len(models) == 2
    assert models[0][1] == d1 / "m1.yaml"
    assert models[1][1] == d2 / "m1.yml"


def test_save_to(yaml_data, yaml_str, tmp_path):
    model = TempYamlModel(**yaml_data)
    yaml_file = tmp_path / "saved.yaml"

    model.save_to(yaml_file)

    with open(yaml_file) as f:
        assert f.read() == yaml_str
    assert TempYamlModel.load_from(yaml_file) == model


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
