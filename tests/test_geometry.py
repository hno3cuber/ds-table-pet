import pytest
from pet.geometry import scaled_size, scale_from_drag


def test_scaled_size_rounds_half_up():
    assert scaled_size(100, 200, 1.5) == (150, 300)


def test_scaled_size_min_one_px():
    assert scaled_size(100, 200, 0.005) == (1, 1)


def test_scale_increases_with_drag():
    assert scale_from_drag(100, 50, 1.0) == pytest.approx(1.5)


def test_scale_decreases_with_negative_drag():
    assert scale_from_drag(100, -50, 1.0) == pytest.approx(0.5)


def test_scale_clamps_at_min():
    assert scale_from_drag(100, -999, 1.0, min_scale=0.3) == 0.3
