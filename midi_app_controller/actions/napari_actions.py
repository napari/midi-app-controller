from functools import partial
from typing import Callable, Optional

from app_model import Application
from app_model.types import Action, ToggleRule
from napari.components import LayerList
from napari.layers.image import Image
from napari.layers.labels import Labels
from napari.layers.labels._labels_constants import Mode
from napari.viewer import Viewer

# TODO The actions should be deleted as soon as napari adds them.


def decrease_opacity(ll: LayerList):
    if (layer := ll.selection.active) is not None:
        layer.opacity = max(0, layer.opacity - 0.01)


def increase_opacity(ll: LayerList):
    if (layer := ll.selection.active) is not None:
        layer.opacity = min(1, layer.opacity + 0.01)


def decrease_brush_size(ll: LayerList) -> None:
    if (layer := ll.selection.active) is not None and isinstance(layer, Labels):
        layer.brush_size = max(1, layer.brush_size - 1)


def increase_brush_size(ll: LayerList) -> None:
    if (layer := ll.selection.active) is not None and isinstance(layer, Labels):
        layer.brush_size = min(40, layer.brush_size + 1)


def activate_labels_mode(mode: Mode) -> Callable[[LayerList], None]:
    def activate(ll: LayerList) -> None:
        """Activates the `mode` of `Labels` layer."""
        if (layer := ll.selection.active) is not None and isinstance(layer, Labels):
            layer.mode = mode

    return activate


def toggled_labels_mode(mode: Mode) -> Callable[[LayerList], Optional[bool]]:
    def toggled(ll: LayerList) -> Optional[bool]:
        """Checks is the `mode` of `Labels` layer is currently activated."""
        if (layer := ll.selection.active) is not None and isinstance(layer, Labels):
            return layer.mode == mode

    return toggled


def next_label(ll: LayerList) -> None:
    if (layer := ll.selection.active) is not None and isinstance(layer, Labels):
        layer.selected_label += 1


def prev_label(ll: LayerList) -> None:
    if (layer := ll.selection.active) is not None and isinstance(layer, Labels):
        layer.selected_label -= 1


def zoom_out(viewer: Viewer) -> None:
    viewer.camera.zoom *= 0.95


def zoom_in(viewer: Viewer) -> None:
    viewer.camera.zoom /= 0.95


def _replace_value_at(seq, pos, new_val):
    tmp_seq = list(seq)
    tmp_seq[pos] = new_val
    return tuple(tmp_seq)


def increment_axis(viewer: Viewer, slider_num=None, inc=1) -> None:
    not_disp = viewer.dims.not_displayed
    if slider_num is None:
        axis = viewer.dims.last_used
    elif slider_num < len(not_disp):
        axis = not_disp[slider_num]
    else:
        return
    cur = viewer.dims.current_step
    next_value = viewer.dims.current_step[axis] + inc
    # note: current_step automatically clamps to the correct range, so we
    # don't need to do bounds checks below.
    viewer.dims.current_step = _replace_value_at(cur, axis, next_value)


def increase_dimensions_left(viewer: Viewer) -> None:
    viewer.dims._increment_dims_left()


def increase_dimensions_right(viewer: Viewer) -> None:
    viewer.dims._increment_dims_right()


def decrease_contour(ll: LayerList) -> None:
    if (layer := ll.selection.active) is not None and isinstance(layer, Labels):
        layer.contour = max(0, layer.contour - 1)


def increase_contour(ll: LayerList) -> None:
    if (layer := ll.selection.active) is not None and isinstance(layer, Labels):
        layer.contour += 1


def decrease_gamma(ll: LayerList) -> None:
    if (layer := ll.selection.active) is not None and isinstance(layer, Image):
        layer.gamma = max(0.2, layer.gamma - 0.02)


def increase_gamma(ll: LayerList) -> None:
    if (layer := ll.selection.active) is not None and isinstance(layer, Image):
        layer.gamma = min(2, layer.gamma + 0.02)


CUSTOM_ACTIONS = [
    Action(
        id="napari:layer:decrease_opacity",
        title="Decrease opacity",
        callback=decrease_opacity,
    ),
    Action(
        id="napari:layer:increase_opacity",
        title="Increase opacity",
        callback=increase_opacity,
    ),
    Action(
        id="napari:layer:decrease_brush_size",
        title="Decrease brush size",
        callback=decrease_brush_size,
    ),
    Action(
        id="napari:layer:increase_brush_size",
        title="Increase brush size",
        callback=increase_brush_size,
    ),
    Action(
        id="napari:layer:pan_zoom_mode",
        title="Activate the pan/zoom mode",
        callback=activate_labels_mode(Mode.PAN_ZOOM),
        toggled=ToggleRule(get_current=toggled_labels_mode(Mode.PAN_ZOOM)),
    ),
    Action(
        id="napari:layer:paint_mode",
        title="Activate the paint brush mode",
        callback=activate_labels_mode(Mode.PAINT),
        toggled=ToggleRule(get_current=toggled_labels_mode(Mode.PAINT)),
    ),
    Action(
        id="napari:layer:fill_mode",
        title="Activate the fill bucket mode",
        callback=activate_labels_mode(Mode.FILL),
        toggled=ToggleRule(get_current=toggled_labels_mode(Mode.FILL)),
    ),
    Action(
        id="napari:layer:erase_mode",
        title="Activate the label erase mode",
        callback=activate_labels_mode(Mode.ERASE),
        toggled=ToggleRule(get_current=toggled_labels_mode(Mode.ERASE)),
    ),
    Action(
        id="napari:layer:transform_mode",
        title="Activate the label transform mode",
        callback=activate_labels_mode(Mode.TRANSFORM),
        toggled=ToggleRule(get_current=toggled_labels_mode(Mode.TRANSFORM)),
    ),
    Action(
        id="napari:layer:pick_mode",
        title="Activate the label pick mode",
        callback=activate_labels_mode(Mode.PICK),
        toggled=ToggleRule(get_current=toggled_labels_mode(Mode.PICK)),
    ),
    Action(
        id="napari:layer:next_label",
        title="Next label",
        callback=next_label,
    ),
    Action(
        id="napari:layer:previous_label",
        title="Previous label",
        callback=prev_label,
    ),
    Action(
        id="napari:viewer:zoom_out",
        title="Zoom out",
        callback=zoom_out,
    ),
    Action(
        id="napari:viewer:zoom_in",
        title="Zoom in",
        callback=zoom_in,
    ),
    Action(
        id="napari:viewer:increase_dimensions_left",
        title="Increase dimensions to the left",
        callback=partial(increment_axis, slider_num=None, inc=-1),
    ),
    Action(
        id="napari:viewer:increase_dimensions_right",
        title="Increase dimensions to the right",
        callback=partial(increment_axis, slider_num=None, inc=1),
    ),
    Action(
        id="napari:layer:decrease_contour",
        title="Decrease contour",
        callback=decrease_contour,
    ),
    Action(
        id="napari:layer:increase_contour",
        title="Increase contour",
        callback=increase_contour,
    ),
    Action(
        id="napari:layer:decrease_gamma",
        title="Decrease gamma",
        callback=decrease_gamma,
    ),
    Action(
        id="napari:layer:increase_gamma",
        title="Increase gamma",
        callback=increase_gamma,
    ),
]


def register_custom_napari_actions(app: Application) -> None:
    for action in CUSTOM_ACTIONS:
        app.register_action(action)
