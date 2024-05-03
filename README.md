# midi-app-controller

[![codecov](https://codecov.io/gh/midi-app-controller/midi-app-controller/graph/badge.svg?token=YALMD0PQ80)](https://codecov.io/gh/midi-app-controller/midi-app-controller)
[![Documentation Status](https://readthedocs.org/projects/midi-app-controller/badge/?version=latest)](https://midi-app-controller.readthedocs.io/en/latest/?badge=latest)

midi-app-controller is an app, that allows user to control all applications using 'pyapp-kit/app-model' with a USB MIDI controller.

## Documentation

Documentation at https://midi-app-controller.readthedocs.io/en/latest/

## Installing
```sh
python3 -m pip install -e .
```

## Testing
```sh
python3 -m pytest --cov .
```

## Testing docs
```sh
mkdocs serve
```

## Using pre-commit
```sh
python3 -m pip install pre-commit
pre-commit install
```
