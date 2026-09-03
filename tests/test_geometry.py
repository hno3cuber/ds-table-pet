import pytest
from pet.geometry import (
    scaled_size,
    scaled_size_xy,
    scale_from_corner_drag,
    corner_resize_size,
    anchor_and_topleft,
    wander_step_x,
)


def test_scaled_size_rounds_half_up():
    assert scaled_size(100, 200, 1.5) == (150, 300)


def test_scaled_size_min_one_px():
    assert scaled_size(100, 200, 0.005) == (1, 1)


def test_scaled_size_xy_independent():
    """宽高独立缩放（不锁宽高比）。"""
    assert scaled_size_xy(100, 200, 1.5, 0.5) == (150, 100)


# ---- PPT 式等比投影（Shift 键） ----

def test_corner_drag_no_change():
    """光标不动 → ratio=1（不变）。"""
    assert scale_from_corner_drag((100, 100), (100, 100), 1.0) == pytest.approx(1.0)


def test_corner_drag_enlarge():
    """光标沿对角线远离锚点 2 倍 → scale ×2。"""
    assert scale_from_corner_drag((100, 100), (200, 200), 1.0) == pytest.approx(2.0)


def test_corner_drag_shrink():
    """光标靠近锚点 → 缩小。"""
    assert scale_from_corner_drag((100, 100), (50, 50), 1.0) == pytest.approx(0.5)


def test_corner_drag_past_anchor_clamp():
    """光标越过锚点 → ratio<0 → 钳制。"""
    assert scale_from_corner_drag((100, 100), (-50, -50), 1.0, min_scale=0.1) == 0.1


def test_corner_drag_zero_start_vec():
    """start_vec 几乎为零（安全退化）→ 返回 start_scale。"""
    assert scale_from_corner_drag((0, 0), (100, 100), 1.0) == 1.0


# ---- PPT 式自由缩放（默认：不锁宽高比） ----

def test_corner_resize_right_bottom_grows():
    """拖右下角：光标向右下移 → 宽高同时变大（锚=左上）。"""
    w, h = corner_resize_size(3, (100, 100), (300, 400))
    assert (w, h) == (200, 300)


def test_corner_resize_right_bottom_shrinks():
    """拖右下角：光标向锚点靠近 → 变小。"""
    w, h = corner_resize_size(3, (100, 100), (150, 150))
    assert (w, h) == (50, 50)


def test_corner_resize_left_top_grows():
    """拖左上角：光标向左上移 → 宽高同时变大（锚=右下）。"""
    w, h = corner_resize_size(0, (300, 400), (100, 100))
    assert (w, h) == (200, 300)


def test_corner_resize_free_aspect():
    """不锁宽高比：光标只水平移动 → 只有宽度变，高度钳到最小像素。"""
    w, h = corner_resize_size(3, (100, 100), (300, 100))
    assert (w, h) == (200, 1)  # 高度方向光标未离开锚点水平线 → min_h=1


def test_corner_resize_past_anchor_clamped():
    """光标越过锚点 → 该方向钳制到最小像素。"""
    w, h = corner_resize_size(3, (100, 100), (50, 50), min_w=10, min_h=20)
    assert (w, h) == (10, 20)


# ---- 对角锚定 ----

def test_anchor_topleft_corner3_right_bottom():
    """拖右下角：锚=左上，新窗口左上角=锚（不动）。"""
    anchor, tl = anchor_and_topleft(3, (100, 200), (200, 300), (100, 150))
    assert anchor == (100, 200)
    assert tl == (100, 200)


def test_anchor_topleft_corner0_left_top():
    """拖左上角：锚=右下，新窗口右下角=锚 → topLeft=锚-新尺寸。"""
    anchor, tl = anchor_and_topleft(0, (100, 200), (200, 300), (100, 150))
    assert anchor == (300, 500)
    assert tl == (200, 350)


def test_anchor_topleft_corner1_right_top():
    """拖右上角：锚=左下，新窗口左下角=锚 → topLeft.x=锚x, topLeft.y=锚y-新高。"""
    anchor, tl = anchor_and_topleft(1, (100, 200), (200, 300), (100, 150))
    assert anchor == (100, 500)
    assert tl == (100, 350)


def test_anchor_topleft_corner2_left_bottom():
    """拖左下角：锚=右上，新窗口右上角=锚 → topLeft.x=锚x-新宽, topLeft.y=锚y。"""
    anchor, tl = anchor_and_topleft(2, (100, 200), (200, 300), (100, 150))
    assert anchor == (300, 200)
    assert tl == (200, 200)


# ---- 自由走动：水平步进 + 边缘掉头 ----

def test_wander_step_plain_left():
    """朝左走一步：x 减小，方向不变。"""
    assert wander_step_x(500, -1, 8, 0, 800, 100) == (492, -1)


def test_wander_step_plain_right():
    """朝右走一步：x 增大，方向不变。"""
    assert wander_step_x(500, 1, 8, 0, 800, 100) == (508, 1)


def test_wander_step_bounce_at_left_edge():
    """越过左缘 → 钳到 left 并掉头朝右。"""
    assert wander_step_x(4, -1, 8, 0, 800, 100) == (0, 1)


def test_wander_step_bounce_at_right_edge():
    """窗口右缘贴 right 时 x=right-width；再向右越界 → 钳回并掉头朝左。"""
    assert wander_step_x(695, 1, 8, 0, 800, 100) == (700, -1)  # 700 = 800-100


def test_wander_step_already_at_left_edge_keeps_bouncing():
    """已经贴左缘还朝左走 → 原地不动并掉头（不掉出边界）。"""
    assert wander_step_x(0, -1, 8, 0, 800, 100) == (0, 1)


def test_wander_step_already_at_right_edge_keeps_bouncing():
    """已经贴右缘还朝右走 → 原地不动并掉头。"""
    assert wander_step_x(700, 1, 8, 0, 800, 100) == (700, -1)


def test_wander_step_wider_than_room_stays_put():
    """退化：窗口比可用区还宽（right-width <= left）→ 钳到左缘原地停，
    方向不变，不左右贴边抖动。"""
    # 左缘 0 右缘 100，窗口宽 150 → right_max = -50 <= 0
    assert wander_step_x(200, -1, 8, 0, 100, 150) == (0, -1)
    assert wander_step_x(0, -1, 8, 0, 100, 150) == (0, -1)
    assert wander_step_x(-5, 1, 8, 0, 100, 150) == (0, 1)
