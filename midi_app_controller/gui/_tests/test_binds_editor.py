import pytest
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from midi_app_controller.gui.binds_editor import ButtonBinds, KnobBinds, BindsEditor
from midi_app_controller.models.controller import ControllerElement, Controller
from midi_app_controller.models.binds import ButtonBind, KnobBind, Binds
from unittest.mock import patch


@pytest.fixture
def controller_sample():
    buttons = [
        ControllerElement(id=1, name="Play"),
        ControllerElement(id=2, name="Stop")
    ]
    knobs = [
        ControllerElement(id=3, name="Volume"),
        ControllerElement(id=4, name="Zoom")
    ]

    return Controller(
        name="TestController",
        button_value_off=0,
        button_value_on=127,
        knob_value_min=0,
        knob_value_max=127,
        buttons=buttons,
        knobs=knobs
    )


@pytest.fixture
def button_binds_sample():
    return [
        ButtonBind(button_id=1, action_id="play_action"),
        ButtonBind(button_id=2, action_id="stop_action")
    ]


@pytest.fixture
def knob_binds_sample():
    return [
        KnobBind(knob_id=3, action_id_increase="volume_up", action_id_decrease="volume_down"),
        KnobBind(knob_id=4, action_id_increase="zoom_in", action_id_decrease="zoom_out")
    ]


@pytest.fixture
def binds_sample(button_binds_sample, knob_binds_sample):
    return Binds(
        name="TestBinds",
        app_name="TestApp",
        controller_name="TestController",
        button_binds=button_binds_sample,
        knob_binds=knob_binds_sample
    )


@pytest.fixture
def button_binds_fixture(qtbot, controller_sample, button_binds_sample):
    actions = ["play_action", "stop_action"]
    widget = ButtonBinds(controller_sample.buttons, button_binds_sample, actions)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def knob_binds_fixture(qtbot, controller_sample, knob_binds_sample):
    actions = ["volume_up", "volume_down", "zoom_in", "zoom_out"]
    widget = KnobBinds(controller_sample.knobs, knob_binds_sample, actions)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def binds_editor_fixture_basic(qtbot, controller_sample, binds_sample):
    actions = ["play_action", "volume_up", "volume_down", "zoom_in", "zoom_out"]
    widget = BindsEditor(controller_sample, binds_sample, actions, save_binds=lambda x, y: None)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def binds_editor_fixture(qtbot, controller_sample, binds_sample):
    with patch.object(BindsEditor, '_save_and_exit') as mock_save_and_exit, \
            patch.object(BindsEditor, '_exit') as mock_exit:
        actions = ["play_action", "volume_up", "volume_down", "zoom_in", "zoom_out"]
        widget = BindsEditor(controller_sample, binds_sample, actions, save_binds=lambda x, y: None)
        qtbot.addWidget(widget)
        yield widget, mock_save_and_exit, mock_exit


def test_button_binds_initialization(button_binds_fixture):
    assert len(button_binds_fixture.button_combos) == 2


def test_get_button_binds(button_binds_fixture):
    binds = button_binds_fixture.get_binds()
    assert len(binds) == 2
    assert binds[0].action_id == "play_action"
    assert binds[1].action_id == "stop_action"


def test_knob_binds_initialization(knob_binds_fixture):
    assert len(knob_binds_fixture.knob_combos) == 2


def test_get_knob_binds(knob_binds_fixture):
    binds = knob_binds_fixture.get_binds()
    assert len(binds) == 2
    assert binds[0].action_id_increase == "volume_up"
    assert binds[1].action_id_decrease == "zoom_out"


def test_binds_editor_switch_views(binds_editor_fixture_basic, qtbot):
    widget = binds_editor_fixture_basic
    QTest.mouseClick(widget.buttons_radio, Qt.LeftButton)
    assert widget.buttons_widget.isVisible()
    assert not widget.knobs_widget.isVisible()

    QTest.mouseClick(widget.knobs_radio, Qt.LeftButton)
    assert widget.knobs_widget.isVisible()
    assert not widget.buttons_widget.isVisible()


def test_binds_editor_save_and_exit(binds_editor_fixture, qtbot):
    widget, mock_save_and_exit, _ = binds_editor_fixture
    all_buttons = widget.findChildren(QPushButton)
    save_and_exit_button = next((btn for btn in all_buttons if btn.text() == "Save and exit"), None)
    assert save_and_exit_button is not None

    QTest.mouseClick(save_and_exit_button, Qt.LeftButton)

    mock_save_and_exit.assert_called_once()


def test_binds_editor_exit(binds_editor_fixture, qtbot):
    widget, _, mock_exit = binds_editor_fixture
    all_buttons = widget.findChildren(QPushButton)
    exit_button = next((btn for btn in all_buttons if btn.text() == "Exit"), None)
    assert exit_button is not None

    QTest.mouseClick(exit_button, Qt.LeftButton)

    mock_exit.assert_called_once()


def test_binds_editor_save_and_exit_no_mock(binds_editor_fixture_basic, qtbot):
    widget = binds_editor_fixture_basic
    all_buttons = widget.findChildren(QPushButton)
    save_and_exit_button = next((btn for btn in all_buttons if btn.text() == "Save and exit"), None)
    assert save_and_exit_button is not None

    QTest.mouseClick(save_and_exit_button, Qt.LeftButton)
    QTest.qWait(100)

    assert not widget.isVisible()


def test_binds_editor_exit_no_mock(binds_editor_fixture_basic, qtbot):
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