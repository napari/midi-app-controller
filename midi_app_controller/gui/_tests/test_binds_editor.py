from unittest.mock import MagicMock, patch

import pytest
from app_model import Action
from qtpy import QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtTest import QTest

from midi_app_controller.controller.connected_controller import ConnectedController
from midi_app_controller.gui.binds_editor import BindsEditor, ButtonBinds, KnobBinds
from midi_app_controller.gui.utils import HIGHLIGHT_DURATION_MS
from midi_app_controller.models.binds import Binds, ButtonBind, KnobBind
from midi_app_controller.models.controller import Controller, ControllerElement


def list_of_actions(actions: list[str]) -> list[Action]:
    return [
        Action(id=action, title=action, callback=lambda: None) for action in actions
    ]


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
        preferred_midi_in="TestMidiIn",
        preferred_midi_out="TestMidiOut",
        buttons=buttons,
        knobs=knobs,
        default_channel=1,
    )


@pytest.fixture
def button_binds_list() -> list[ButtonBind]:
    return [
        ButtonBind(button_id=1, action_id="play_action"),
        ButtonBind(button_id=2, action_id="stop_action"),
    ]


@pytest.fixture
def knob_binds_list() -> list[KnobBind]:
    return [
        KnobBind(
            knob_id=3, action_id_increase="volume_up", action_id_decrease="volume_down"
        ),
        KnobBind(
            knob_id=4, action_id_increase="zoom_in", action_id_decrease="zoom_out"
        ),
    ]


@pytest.fixture
def mixed_knob_binds_list() -> list[KnobBind]:
    return [KnobBind(knob_id=3, action_id_increase="volume_up", action_id_decrease="")]


@pytest.fixture
def binds_sample(button_binds_list, knob_binds_list) -> Binds:
    return Binds(
        name="TestBinds",
        app_name="TestApp",
        controller_name="TestController",
        description="description",
        button_binds=button_binds_list,
        knob_binds=knob_binds_list,
    )


@pytest.fixture
def button_binds(qtbot, controller_sample, button_binds_list) -> ButtonBinds:
    actions_str = ["play_action", "stop_action"]
    widget = ButtonBinds(
        controller_sample.buttons,
        button_binds_list,
        list_of_actions(actions_str),
        MagicMock(spec=ConnectedController),
        QtWidgets.QCheckBox(),
    )
    widget.show()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def knob_binds(qtbot, controller_sample, knob_binds_list) -> KnobBinds:
    actions_str = ["volume_up", "volume_down", "zoom_in", "zoom_out"]
    widget = KnobBinds(
        controller_sample.knobs,
        knob_binds_list,
        list_of_actions(actions_str),
        MagicMock(spec=ConnectedController),
        QtWidgets.QCheckBox(),
    )
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def knob_binds_mixed(qtbot, controller_sample, mixed_knob_binds_list) -> KnobBinds:
    actions_str = ["volume_up", "volume_down", "zoom_in", "zoom_out"]
    widget = KnobBinds(
        controller_sample.knobs,
        mixed_knob_binds_list,
        list_of_actions(actions_str),
        MagicMock(spec=ConnectedController),
        QtWidgets.QCheckBox(),
    )
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def binds_editor_basic(qtbot, controller_sample, binds_sample) -> BindsEditor:
    actions_str = ["play_action", "volume_up", "volume_down", "zoom_in", "zoom_out"]
    widget = BindsEditor(
        controller_sample,
        binds_sample,
        list_of_actions(actions_str),
        save_binds=lambda x: None,
        connected_controller=MagicMock(spec=ConnectedController),
    )
    qtbot.addWidget(widget)
    widget.show()
    return widget


@pytest.fixture
def binds_editor(
    qtbot, controller_sample, binds_sample
) -> tuple[BindsEditor, patch, patch]:
    with (
        patch.object(BindsEditor, "_save_and_exit") as mock_save_and_exit,
        patch.object(BindsEditor, "_exit") as mock_exit,
    ):
        actions_str = ["play_action", "volume_up", "volume_down", "zoom_in", "zoom_out"]
        widget = BindsEditor(
            controller_sample,
            binds_sample,
            list_of_actions(actions_str),
            save_binds=lambda x: None,
            connected_controller=MagicMock(spec=ConnectedController),
        )
        qtbot.addWidget(widget)
        widget.show()
        yield widget, mock_save_and_exit, mock_exit


def test_button_binds_initialization(button_binds):
    fixture = button_binds
    expected_length = 2
    assert len(fixture.button_combos) == expected_length


def test_get_button_binds(button_binds):
    expected_binds = ["play_action", "stop_action"]

    binds = button_binds.get_binds()

    assert len(binds) == len(expected_binds)
    for i in range(len(binds)):
        assert binds[i].action_id == expected_binds[i]


@pytest.mark.parametrize(
    "binds, expected_length", [("knob_binds", 2), ("knob_binds_mixed", 2)]
)
def test_knob_binds_initialization(request, binds, expected_length):
    binds = request.getfixturevalue(binds)
    assert len(binds.knob_combos) == expected_length


@pytest.mark.parametrize(
    "binds, expected_binds",
    [
        ("knob_binds", [("volume_up", "volume_down"), ("zoom_in", "zoom_out")]),
        ("knob_binds_mixed", [("volume_up", None)]),
    ],
)
def test_get_knob_binds(request, binds, expected_binds):
    binds = request.getfixturevalue(binds).get_binds()
    assert len(binds) == len(expected_binds)
    for bind, (expected_increase, expected_decrease) in zip(binds, expected_binds):
        assert bind.action_id_increase == expected_increase
        assert bind.action_id_decrease == expected_decrease


def test_binds_editor_save_and_exit(binds_editor):
    widget, mock_save_and_exit, mock_exit = binds_editor
    assert widget.save_and_exit_button is not None

    QTest.mouseClick(widget.save_and_exit_button, Qt.LeftButton)
    QTest.qWait(100)
    mock_save_and_exit.assert_called_once()
    mock_exit.assert_not_called()


def test_binds_editor_exit(binds_editor):
    widget, mock_save_and_exit, mock_exit = binds_editor
    assert widget.exit_button is not None

    QTest.mouseClick(widget.exit_button, Qt.LeftButton)
    QTest.qWait(100)
    mock_exit.assert_called_once()
    mock_save_and_exit.assert_not_called()


def test_binds_editor_save_and_exit_no_mock(binds_editor_basic):
    save_and_exit_button = binds_editor_basic.save_and_exit_button
    assert save_and_exit_button is not None

    QTest.mouseClick(save_and_exit_button, Qt.LeftButton)
    QTest.qWait(100)
    assert not binds_editor_basic.isVisible()


def test_binds_editor_exit_no_mock(binds_editor_basic):
    widget = binds_editor_basic
    exit_button = widget.exit_button
    assert exit_button is not None
    QTest.mouseClick(exit_button, Qt.LeftButton)
    QTest.qWait(100)
    assert not widget.isVisible()


def test_button_binds_initialization_unbound(qtbot, controller_sample):
    unbound_buttons = [ControllerElement(id=3, name="Unbound Button")]
    actions_str = ["play_action", "stop_action"]
    widget = ButtonBinds(
        unbound_buttons,
        [],
        list_of_actions(actions_str),
        MagicMock(spec=ConnectedController),
        QtWidgets.QCheckBox(),
    )
    qtbot.addWidget(widget)

    assert len(widget.button_combos) == 1
    button_id = unbound_buttons[0].id
    action_combo = widget.button_combos[button_id]
    assert action_combo.currentText() == ""


def test_knob_binds_initialization_unbound(qtbot, controller_sample):
    unbound_knobs = [ControllerElement(id=5, name="Unbound Knob")]
    actions_str = ["volume_up", "volume_down", "zoom_in", "zoom_out"]
    widget = KnobBinds(
        unbound_knobs,
        [],
        list_of_actions(actions_str),
        MagicMock(spec=ConnectedController),
        QtWidgets.QCheckBox(),
    )
    qtbot.addWidget(widget)

    assert len(widget.knob_combos) == 1
    knob_id = unbound_knobs[0].id
    increase_action_combo, decrease_action_combo = widget.knob_combos[knob_id]
    assert increase_action_combo.currentText() == ""
    assert decrease_action_combo.currentText() == ""


@pytest.mark.parametrize(
    "button_id, action_id",
    [
        (1, "stop_action"),
        (2, "play_action"),
        (1, "play_action"),
        (2, "stop_action"),
    ],
)
def test_modify_bind_action(button_binds, button_id, action_id):
    widget = button_binds
    action_combo = widget.button_combos[button_id]
    index = action_combo.findText(action_id)
    action_combo.setCurrentIndex(index)
    QTest.qWait(100)
    assert action_combo.currentText() == action_id


@pytest.mark.parametrize(
    "stop, controller",
    [
        (True, None),
        (False, None),
        (False, MagicMock()),
    ],
)
@pytest.mark.parametrize("button_id", [1, 2])
def test_light_up_button(button_binds, stop, controller, button_id):
    widget = button_binds
    widget.stop = stop
    widget.connected_controller = controller

    if not widget.connected_controller and not stop:
        with pytest.raises(Exception, match="No controller connected."):
            widget._light_up_button(button_id)
    else:
        widget._light_up_button(button_id)
        if controller and not stop:
            QTest.qWait(100)
            widget.connected_controller.flash_button.assert_called_with(button_id)
        else:
            if controller:
                widget.connected_controller.flash_button.assert_not_called()


@pytest.mark.parametrize("knob_id", [3, 4])
def test_light_up_knob(knob_binds, knob_id):
    widget = knob_binds
    widget.connected_controller = MagicMock(spec=ConnectedController)
    widget._light_up_knob(knob_id)
    QTest.qWait(100)
    widget.connected_controller.flash_knob.assert_called_with(knob_id)


def test_wait_for_worker_threads(binds_editor_basic):
    widget = binds_editor_basic
    thread = MagicMock()
    widget.buttons_widget.thread_list.append(thread)
    widget.knobs_widget.thread_list.append(thread)
    thread.wait = MagicMock()

    widget._wait_for_worker_threads()
    thread.wait.assert_called()


@pytest.mark.parametrize("tab_index", [0, 1])
def test_save_and_exit(binds_editor_basic, tab_index):
    widget = binds_editor_basic
    widget.tab_widget.setCurrentIndex(tab_index)
    widget._save_and_exit()
    assert not widget.isVisible()


@pytest.mark.parametrize("tab_index", [0, 1])
def test_exit(binds_editor_basic, tab_index):
    widget = binds_editor_basic
    widget.tab_widget.setCurrentIndex(tab_index)
    widget._exit()
    assert not widget.isVisible()


@pytest.mark.parametrize(
    "tab, bind_type, bind_id",
    [
        (0, "button", 1),
        (0, "button", 2),
        (1, "knob", 3),
        (1, "knob", 4),
    ],
)
def test_highlight_button_and_knob(binds_editor_basic, tab, bind_type, bind_id):
    widget = binds_editor_basic
    widget.tab_widget.setCurrentIndex(tab)

    if bind_type == "button":
        widget.buttons_widget.highlight_button(bind_id)
        QTest.qWait(HIGHLIGHT_DURATION_MS + 100)
        combo = widget.buttons_widget.button_combos[bind_id]
        assert combo.styleSheet() == ""
    else:
        widget.knobs_widget.highlight_knob(bind_id)
        QTest.qWait(HIGHLIGHT_DURATION_MS + 100)
        combos = widget.knobs_widget.knob_combos[bind_id]
        assert combos[0].styleSheet() == ""
        assert combos[1].styleSheet() == ""


@pytest.mark.parametrize("tab", [0, 1])
def test_toggle_names_mode(binds_editor_basic, tab):
    widget = binds_editor_basic
    widget.tab_widget.setCurrentIndex(tab)

    if tab == 0:
        for combo1, combo2 in widget.knobs_widget.knob_combos.values():
            combo1.toggle_names_mode = MagicMock()
            combo2.toggle_names_mode = MagicMock()
    else:
        for combo in widget.buttons_widget.button_combos.values():
            combo.toggle_names_mode = MagicMock()

    widget._toggle_names_mode()

    if tab == 0:
        for combo1, combo2 in widget.knobs_widget.knob_combos.values():
            combo1.toggle_names_mode.assert_called_once()
            combo2.toggle_names_mode.assert_called_once()
    else:
        for combo in widget.buttons_widget.button_combos.values():
            combo.toggle_names_mode.assert_called_once()
