import numpy as np
import pytest
from napari.components import LayerList
from napari.layers import Image
from napari.layers.labels import Labels
from napari.layers.labels._labels_constants import Mode

from ..napari_actions import (
    activate_labels_mode,
    decrease_brush_size,
    decrease_contour,
    decrease_gamma,
    decrease_opacity,
    increase_brush_size,
    increase_contour,
    increase_dimensions_left,
    increase_dimensions_right,
    increase_gamma,
    increase_opacity,
    next_label,
    prev_label,
    toggled_labels_mode,
    zoom_in,
    zoom_out,
)


def test_opacity():
    layer = Image(np.random.random((3, 3)), opacity=0.5)
    other_layer = Image(np.random.random((3, 3)), opacity=0.5)
    ll = LayerList([other_layer, layer])

    decrease_opacity(ll)
    assert layer.opacity == 0.49
    assert other_layer.opacity == 0.5

    for _ in range(200):
        decrease_opacity(ll)
    assert layer.opacity == 0
    assert other_layer.opacity == 0.5

    increase_opacity(ll)
    assert layer.opacity == 0.01
    assert other_layer.opacity == 0.5

    for _ in range(200):
        increase_opacity(ll)
    assert layer.opacity == 1
    assert other_layer.opacity == 0.5


def test_brush_size():
    layer = Labels(np.ones((4, 4), dtype=np.int32))
    other_layer = Labels(np.ones((4, 4), dtype=np.int32))
    layer.brush_size = 20
    other_layer.brush_size = 20
    ll = LayerList([other_layer, layer])

    decrease_brush_size(ll)
    assert layer.brush_size == 19
    assert other_layer.brush_size == 20

    for _ in range(50):
        decrease_brush_size(ll)
    assert layer.brush_size == 1
    assert other_layer.brush_size == 20

    increase_brush_size(ll)
    assert layer.brush_size == 2
    assert other_layer.brush_size == 20

    for _ in range(50):
        increase_brush_size(ll)
    assert layer.brush_size == 40
    assert other_layer.brush_size == 20


@pytest.mark.parametrize(
    "mode",
    [Mode.ERASE, Mode.FILL, Mode.PAINT, Mode.PAN_ZOOM, Mode.PICK, Mode.TRANSFORM],
)
def test_labels_mode(mode):
    layer = Labels(np.ones((4, 4), dtype=np.int32))
    other_layer = Labels(np.ones((4, 4), dtype=np.int32))
    layer.mode = Mode.ERASE if mode != Mode.ERASE else Mode.PAINT
    other_layer.mode = Mode.ERASE if mode != Mode.ERASE else Mode.PAINT
    ll = LayerList([other_layer, layer])

    activate = activate_labels_mode(mode)
    toggled = toggled_labels_mode(mode)

    assert not toggled(ll)
    activate(ll)
    assert toggled(ll)


def test_selected_label():
    layer = Labels(np.ones((4, 4), dtype=np.int32))
    other_layer = Labels(np.ones((4, 4), dtype=np.int32))
    layer.selected_label = 5
    other_layer.selected_label = 5
    ll = LayerList([other_layer, layer])

    next_label(ll)
    assert layer.selected_label == 6
    assert other_layer.selected_label == 5

    for _ in range(50):
        next_label(ll)
    assert layer.selected_label == 56
    assert other_layer.selected_label == 5

    prev_label(ll)
    assert layer.selected_label == 55
    assert other_layer.selected_label == 5

    for _ in range(50):
        prev_label(ll)
    assert layer.selected_label == 5
    assert other_layer.selected_label == 5


def test_zoom_and_dimensions(make_napari_viewer):
    viewer = make_napari_viewer()
    zoom = viewer.camera.zoom

    zoom_out(viewer)
    assert viewer.camera.zoom < zoom

    zoom_in(viewer)
    assert viewer.camera.zoom == zoom

    zoom_in(viewer)
    assert viewer.camera.zoom > zoom

    increase_dimensions_left(viewer)
    increase_dimensions_right(viewer)


def test_contour():
    layer = Labels(np.ones((4, 4), dtype=np.int32))
    other_layer = Labels(np.ones((4, 4), dtype=np.int32))
    layer.contour = 5
    other_layer.contour = 5
    ll = LayerList([other_layer, layer])

    decrease_contour(ll)
    assert layer.contour == 4
    assert other_layer.contour == 5

    for _ in range(50):
        decrease_contour(ll)
    assert layer.contour == 0
    assert other_layer.contour == 5

    increase_contour(ll)
    assert layer.contour == 1
    assert other_layer.contour == 5

    for _ in range(50):
        increase_contour(ll)
    assert layer.contour == 51
    assert other_layer.contour == 5


def test_gamma():
    layer = Image(np.random.random((3, 3)), gamma=0.5)
    other_layer = Image(np.random.random((3, 3)), gamma=0.5)
    ll = LayerList([other_layer, layer])

    decrease_gamma(ll)
    assert layer.gamma == 0.48
    assert other_layer.gamma == 0.5

    for _ in range(100):
        decrease_gamma(ll)
    assert layer.gamma == 0.2
    assert other_layer.gamma == 0.5

    increase_gamma(ll)
    assert layer.gamma == 0.22
    assert other_layer.gamma == 0.5

    for _ in range(200):
        increase_gamma(ll)
    assert layer.gamma == 2
    assert other_layer.gamma == 0.5
