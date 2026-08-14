from PySide6.QtGui import QPixmap
from pet.config import Config
from pet.window import PetWindow


def test_window_creates_with_scale(qapp, tmp_path):
    pm = QPixmap(200, 300)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    cfg.set("window.scale", 2.0)
    w = PetWindow(pm, cfg)
    assert w.current_scale() == 2.0
    assert w.width() == 400
    assert w.height() == 600


def test_window_min_scale_after_resize_drag(qapp, tmp_path):
    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    w = PetWindow(pm, cfg)
    w._enter_resize_mode()
    w._begin_resize(3)  # 按下右下角手柄
    w._apply_resize(-200)  # 向左拖 200px（相对原图 100，触发最小钳制）
    assert w.current_scale() >= 0.3


def test_resize_drag_incremental_scale(qapp, tmp_path):
    """真实事件流：右下角手柄按下后右移 50px，scale 应为 1.5（增量语义）。

    使用 QTest 合成 press/move/release，验证 mouseMoveEvent 里 drag_dx 是相对
    press 瞬间的增量，而不是光标距窗口左缘的绝对距离。
    """
    import pytest
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    w = PetWindow(pm, cfg)
    w.show()
    w._enter_resize_mode()
    # 右下角手柄命中区（局部坐标，窗口 100x100）
    QTest.mousePress(w, Qt.LeftButton, pos=QPoint(95, 95))
    # 右移 50px：增量 50，scale = 1.0 + 50/100 = 1.5，窗口宽 150
    QTest.mouseMove(w, QPoint(145, 95))
    assert w.current_scale() == pytest.approx(1.5, abs=0.1)
    assert w.width() == pytest.approx(150, abs=1)
    QTest.mouseRelease(w, Qt.LeftButton, pos=QPoint(145, 95))


def test_breathing_follows_config(qapp, tmp_path):
    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    cfg.set("breathing_animation", False)
    w = PetWindow(pm, cfg)
    assert w._actor._breath_anim.state() != w._actor._breath_anim.State.Running


def test_install_plugin_adds_block(qapp, tmp_path):
    from PySide6.QtWidgets import QLabel
    from pet.plugin import Plugin
    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")

    class Fake(Plugin):
        id = "fake"
        name = "假"
        def start(self): pass
        def stop(self): pass
        def poll(self): return {}
        def panel(self, parent): return QLabel("X", parent)

    w = PetWindow(pm, cfg)
    w.install_plugin(Fake())
    assert w._hud.layout().count() >= 1


def test_toggle_pause(qapp, tmp_path):
    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.set_paused(True)
    assert w._paused is True
    w.set_paused(False)
    assert w._paused is False
