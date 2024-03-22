import pytest
from unittest.mock import patch
from qtpy.QtWidgets import QPushButton
from qtpy.QtCore import Qt
from qtpy.QtTest import QTest

from midi_app_controller.gui.binds_editor import ButtonBinds, KnobBinds, BindsEditor
from midi_app_controller.models.controller import ControllerElement, Controller
from midi_app_controller.models.binds import ButtonBind, KnobBind, Binds


@pytest.fixture
def controller_sample() -> Controller:
    buttons = [
        ControllerElement(id=1, name="Play"),
        ControllerElement(id=2, name="Stop"),
    ]
    knobs = [
        ControllerElement(id=3, name="Volume"),
        ControllerElement(id=4, name="Zoom"),
    ]

    return Controller(
        name="TestController",
        button_value_off=0,
        button_value_on=127,
        knob_value_min=0,
        knob_value_max=127,
        buttons=buttons,
        knobs=knobs,
    )


@pytest.fixture
def button_binds_sample() -> list:
    return [
        ButtonBind(button_id=1, action_id="play_action"),
        ButtonBind(button_id=2, action_id="stop_action"),
    ]


@pytest.fixture
def knob_binds_sample() -> list:
    return [
        KnobBind(
            knob_id=3, action_id_increase="volume_up", action_id_decrease="volume_down"
        ),
        KnobBind(
            knob_id=4, action_id_increase="zoom_in", action_id_decrease="zoom_out"
        ),
    ]


@pytest.fixture
def mixed_button_binds_sample() -> list:
    return [
        ButtonBind(button_id=1, action_id="play_action"),
    ]


@pytest.fixture
def mixed_knob_binds_sample() -> list:
    return [
        KnobBind(
            knob_id=3, action_id_increase="volume_up", action_id_decrease="volume_down"
        ),
    ]


@pytest.fixture
def binds_sample(button_binds_sample, knob_binds_sample) -> Binds:
    return Binds(
        name="TestBinds",
        app_name="TestApp",
        controller_name="TestController",
        button_binds=button_binds_sample,
        knob_binds=knob_binds_sample,
    )


@pytest.fixture
def button_binds_fixture(qtbot, controller_sample, button_binds_sample) -> ButtonBinds:
    actions = ["play_action", "stop_action"]
    widget = ButtonBinds(controller_sample.buttons, button_binds_sample, actions)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def button_binds_mixed_fixture(
    qtbot, controller_sample, mixed_button_binds_sample
) -> ButtonBinds:
    actions = ["play_action", "stop_action"]
    widget = ButtonBinds(controller_sample.buttons, mixed_button_binds_sample, actions)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def knob_binds_fixture(qtbot, controller_sample, knob_binds_sample) -> KnobBinds:
    actions = ["volume_up", "volume_down", "zoom_in", "zoom_out"]
    widget = KnobBinds(controller_sample.knobs, knob_binds_sample, actions)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def knob_binds_fixture_mixed(
    qtbot, controller_sample, mixed_knob_binds_sample
) -> KnobBinds:
    actions = ["volume_up", "volume_down", "zoom_in", "zoom_out"]
    widget = KnobBinds(controller_sample.knobs, mixed_knob_binds_sample, actions)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def binds_editor_fixture_basic(qtbot, controller_sample, binds_sample) -> BindsEditor:
    actions = ["play_action", "volume_up", "volume_down", "zoom_in", "zoom_out"]
    widget = BindsEditor(
        controller_sample, binds_sample, actions, save_binds=lambda x, y: None
    )
    qtbot.addWidget(widget)
    widget.show()
    return widget


@pytest.fixture
def binds_editor_fixture(qtbot, controller_sample, binds_sample) -> tuple:
    with patch.object(
        BindsEditor, "_save_and_exit"
    ) as mock_save_and_exit, patch.object(BindsEditor, "_exit") as mock_exit:
        actions = ["play_action", "volume_up", "volume_down", "zoom_in", "zoom_out"]
        widget = BindsEditor(
            controller_sample, binds_sample, actions, save_binds=lambda x, y: None
        )
        qtbot.addWidget(widget)
        widget.show()
        yield widget, mock_save_and_exit, mock_exit


@pytest.mark.parametrize(
    "button_binds, expected_length",
    [
        ("button_binds_fixture", 2),
        ("button_binds_mixed_fixture", 2),
    ],
)
def test_button_binds_initialization(request, button_binds, expected_length):
    fixture = request.getfixturevalue(button_binds)
    assert len(fixture.button_combos) == expected_length


@pytest.mark.parametrize(
    "button_binds, expected_binds",
    [
        (
            "button_binds_fixture",
            [
                "play_action",
                "stop_action",
            ],
        ),
        (
            "button_binds_mixed_fixture",
            [
                "play_action",
            ],
        ),
    ],
)
def test_get_button_binds(request, button_binds, expected_binds):
    fixture = request.getfixturevalue(button_binds)
    binds = fixture.get_binds()
    assert len(binds) == len(expected_binds)
    for i in range(len(binds)):
        assert binds[i].action_id == expected_binds[i]


@pytest.mark.parametrize(
    "knob_binds, expected_length",
    [
        ("knob_binds_fixture", 2),
        ("knob_binds_fixture_mixed", 2),
    ],
)
def test_knob_binds_initialization(request, knob_binds, expected_length):
    knob_binds_fixture = request.getfixturevalue(knob_binds)
    assert len(knob_binds_fixture.knob_combos) == expected_length


@pytest.mark.parametrize(
    "button_binds, expected_binds",
    [
        (
            "knob_binds_fixture",
            [
                ("volume_up", "volume_down"),
                ("zoom_in", "zoom_out"),
            ],
        ),
        (
            "knob_binds_fixture_mixed",
            [
                ("volume_up", "volume_down"),
            ],
        ),
    ],
)
def test_get_knob_binds(request, button_binds, expected_binds):
    fixture = request.getfixturevalue(button_binds)
    binds = fixture.get_binds()
    assert len(binds) == len(expected_binds)
    for bind, (expected_increase, expected_decrease) in zip(binds, expected_binds):
        assert bind.action_id_increase == expected_increase
        assert bind.action_id_decrease == expected_decrease


def test_binds_editor_switch_views(binds_editor_fixture_basic):
    widget = binds_editor_fixture_basic
    QTest.mouseClick(widget.buttons_radio, Qt.LeftButton)
    QTest.qWait(100)
    assert widget.buttons_widget.isVisible()
    assert not widget.knobs_widget.isVisible()

    QTest.mouseClick(widget.knobs_radio, Qt.LeftButton)
    QTest.qWait(100)
    assert widget.knobs_widget.isVisible()
    assert not widget.buttons_widget.isVisible()


def test_binds_editor_save_and_exit(binds_editor_fixture):
    widget, mock_save_and_exit, mock_exit = binds_editor_fixture
    save_and_exit_button = widget.save_and_exit_button
    assert save_and_exit_button is not None

    QTest.mouseClick(save_and_exit_button, Qt.LeftButton)
    QTest.qWait(100)

    mock_save_and_exit.assert_called_once()
    mock_exit.assert_not_called()


def test_binds_editor_exit(binds_editor_fixture):
    widget, mock_save_and_exit, mock_exit = binds_editor_fixture
    exit_button = widget.exit_button
    assert exit_button is not None

    QTest.mouseClick(exit_button, Qt.LeftButton)
    QTest.qWait(100)

    mock_exit.assert_called_once()
    mock_save_and_exit.assert_not_called()


def test_binds_editor_save_and_exit_no_mock(binds_editor_fixture_basic):
    widget = binds_editor_fixture_basic
    all_buttons = widget.findChildren(QPushButton)
    save_and_exit_button = next(
        (btn for btn in all_buttons if btn.text() == "Save and exit"), None
    )
    assert save_and_exit_button is not None

    QTest.mouseClick(save_and_exit_button, Qt.LeftButton)
    QTest.qWait(100)

    assert not widget.isVisible()


def test_binds_editor_exit_no_mock(binds_editor_fixture_basic):
    widget = binds_editor_fixture_basic
    all_buttons = widget.findChildren(QPushButton)
    exit_button = next((btn for btn in all_buttons if btn.text() == "Exit"), None)
    assert exit_button is not None

    QTest.mouseClick(exit_button, Qt.LeftButton)
    QTest.qWait(100)

    assert not widget.isVisible()


def test_button_binds_initialization_unbound(qtbot, controller_sample):
    unbound_buttons = [ControllerElement(id=3, name="Unbound Button")]
    actions = ["play_action", "stop_action"]
    widget = ButtonBinds(unbound_buttons, [], actions)
    qtbot.addWidget(widget)

    assert len(widget.button_combos) == 1
    assert widget.button_combos[0][1].currentText() == ""


def test_knob_binds_initialization_unbound(qtbot, controller_sample):
    unbound_knobs = [ControllerElement(id=5, name="Unbound Knob")]
    actions = ["volume_up", "volume_down", "zoom_in", "zoom_out"]
    widget = KnobBinds(unbound_knobs, [], actions)
    qtbot.addWidget(widget)

    assert len(widget.knob_combos) == 1
    assert widget.knob_combos[0][1].currentText() == ""
    assert widget.knob_combos[0][2].currentText() == ""
