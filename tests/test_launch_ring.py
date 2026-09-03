from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from pet.config import Config
from pet.launch_ring import LaunchRing, RING_COUNT, RING_R


def _ring(tmp_path, qapp):
    return LaunchRing(Config(tmp_path / "config.json"))


def test_layout_eight_centers_evenly_spaced(qapp, tmp_path):
    ring = _ring(tmp_path, qapp)
    centers = ring.layout_for(QPoint(300, 300), pet_radius=50)
    assert len(centers) == RING_COUNT == 8
    # 相邻圆心间距相等（均匀分布）：任意相邻两点的距离相同
    dists = set()
    for i in range(RING_COUNT):
        a = centers[i]
        b = centers[(i + 1) % RING_COUNT]
        d = (a - b).manhattanLength()  # 45° 间隔下曼哈顿距离也一致
        dists.add(d)
    assert len(dists) == 1


def test_hit_index(qapp, tmp_path):
    ring = _ring(tmp_path, qapp)
    centers = ring.layout_for(QPoint(300, 300), pet_radius=50)
    # 圆心处命中
    assert ring._hit_index(centers[0]) == 0
    # 圆心正下方 RING_R 内命中
    inside = QPoint(centers[0].x(), centers[0].y() + RING_R - 2)
    assert ring._hit_index(inside) == 0
    # 圆外不命中
    outside = QPoint(centers[0].x() + RING_R + 10, centers[0].y())
    assert ring._hit_index(outside) != 0


def test_pick_slot_saves_and_shows_icon(qapp, tmp_path, monkeypatch):
    ring = _ring(tmp_path, qapp)
    ring.layout_for(QPoint(300, 300), pet_radius=50)
    monkeypatch.setattr(
        "pet.launch_ring.QFileDialog.getOpenFileName",
        lambda *a, **k: ("C:/fake/app.exe", ""),
    )
    ring._pick(3)
    assert ring._slots[3] == "C:/fake/app.exe"
    assert ring._config.get("launch_slots")[3] == "C:/fake/app.exe"  # 已持久化


def test_clear_slot(qapp, tmp_path, monkeypatch):
    ring = _ring(tmp_path, qapp)
    ring.layout_for(QPoint(300, 300), pet_radius=50)
    monkeypatch.setattr(
        "pet.launch_ring.QFileDialog.getOpenFileName",
        lambda *a, **k: ("C:/fake/app.exe", ""),
    )
    ring._pick(0)
    assert ring._slots[0] is not None
    ring._clear_slot(0)
    assert ring._slots[0] is None
    assert ring._config.get("launch_slots")[0] is None


def test_launch_calls_startfile(qapp, tmp_path, monkeypatch):
    ring = _ring(tmp_path, qapp)
    ring.layout_for(QPoint(300, 300), pet_radius=50)
    ring._slots[2] = "C:/fake/app.lnk"
    calls = []
    monkeypatch.setattr("pet.launch_ring.os.startfile", lambda p: calls.append(p))
    ring._launch(2)
    assert calls == ["C:/fake/app.lnk"]


def test_ring_has_annular_mask(qapp, tmp_path):
    """环形蒙版：只有圆本身接收鼠标，中心空洞穿透到本体（点本体才能收起）。"""
    ring = _ring(tmp_path, qapp)
    ring.layout_for(QPoint(300, 300), pet_radius=50)
    mask = ring.mask()
    assert mask is not None
    assert not mask.isEmpty()
    # 圆心在蒙版内（圆区域）
    assert mask.contains(ring._centers[0])
    # 中心空洞（桌宠本体位置）不在蒙版内 → 事件穿透
    center = QPoint(ring.width() // 2, ring.height() // 2)
    assert not mask.contains(center)


def test_ring_follows_pet_window_move(qapp, tmp_path):
    """圆环展开后拖动本体，圆环跟着走（相对位置不变）。"""
    from pet.window import PetWindow
    from PySide6.QtGui import QPixmap

    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.show()
    w.move(100, 100)  # 先移到正坐标（offscreen 会把负坐标钳制到 0，影响相对位置断言）
    w._toggle_launch_ring()
    ring = w._launch_ring
    assert ring.isVisible()
    before_center = ring.pos() + QPoint(ring.width() // 2, ring.height() // 2)
    pet_before = w.pos() + QPoint(50, 50)
    w.move(300, 250)
    after_center = ring.pos() + QPoint(ring.width() // 2, ring.height() // 2)
    pet_after = w.pos() + QPoint(50, 50)
    # 圆环中心相对本体中心的偏移不变
    assert (after_center - pet_after) == (before_center - pet_before)


def test_ring_follows_pet_window_resize(qapp, tmp_path):
    """圆环展开后缩放本体，圆环按新的本体半径重新布局：
    环窗口尺寸随 pet_radius 变化，且环中心仍与本体中心重合。"""
    import pytest
    from pet.window import PetWindow
    from PySide6.QtGui import QPixmap

    pm = QPixmap(200, 200)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.show()
    w._toggle_launch_ring()
    ring = w._launch_ring
    assert ring.isVisible()
    size_before = ring.size()

    w._enter_resize_mode()
    w._begin_resize(3, QPoint(w.x() + w.width() - 3, w.y() + w.height() - 3))
    w._resize_start_scale = w.current_scale()  # press 起点的 scale
    w._apply_resize(QPoint(w.x() + w.width() - 3 - 100, w.y() + w.height() - 3 - 100))  # 缩到 0.5

    assert w.current_scale() == pytest.approx(0.5, abs=0.05)
    # 本体变小 -> 环窗口跟着变小
    assert ring.width() < size_before.width()
    # 环中心仍与本体中心重合（相对本体偏移不变）
    pet_center = w.pos() + QPoint(w.width() // 2, w.height() // 2)
    ring_center = ring.pos() + QPoint(ring.width() // 2, ring.height() // 2)
    assert (ring_center - pet_center).manhattanLength() <= 2


def test_click_outside_ring_hides_it(qapp, tmp_path):
    """圆环展开时点击窗口外空白 → 收起（全局点击监听）。"""
    from PySide6.QtCore import QEvent, QPointF
    from PySide6.QtGui import QMouseEvent

    ring = _ring(tmp_path, qapp)
    ring.layout_for(QPoint(300, 300), pet_radius=50)
    ring.show()
    rect = ring.geometry()
    outside = QPointF(rect.x() - 50, rect.y() - 50)  # 窗口外左上角
    ev = QMouseEvent(QEvent.MouseButtonPress, QPointF(0, 0), outside,
                     Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    ring._catcher.eventFilter(None, ev)
    assert ring.isHidden() is True


def test_click_on_ring_circle_not_intercepted(qapp, tmp_path):
    """点击圆环上的圆 → 不触发收起（放行给圆环自己处理）。"""
    from PySide6.QtCore import QEvent, QPointF
    from PySide6.QtGui import QMouseEvent

    ring = _ring(tmp_path, qapp)
    ring.layout_for(QPoint(300, 300), pet_radius=50)
    ring.show()
    circle_global = ring.pos() + ring._centers[0]  # 第一个圆的圆心（全局）
    ev = QMouseEvent(QEvent.MouseButtonPress, QPointF(0, 0),
                     QPointF(circle_global.x(), circle_global.y()),
                     Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    ring._catcher.eventFilter(None, ev)
    assert ring.isVisible() is True
