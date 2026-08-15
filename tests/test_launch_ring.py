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


def test_click_blank_hides_ring(qapp, tmp_path):
    ring = _ring(tmp_path, qapp)
    centers = ring.layout_for(QPoint(300, 300), pet_radius=50)
    ring.show()
    # 点空白（窗口角落，远离所有圆）
    corner = QPoint(2, 2)
    assert ring._hit_index(corner) is None
    from PySide6.QtTest import QTest
    QTest.mousePress(ring, Qt.LeftButton, pos=corner)
    QTest.mouseRelease(ring, Qt.LeftButton, pos=corner)
    assert ring.isHidden() is True
