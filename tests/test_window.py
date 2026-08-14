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
    """真实事件流：右下角手柄按下后，多次 move 的 scale 是相对 press 起点的总位移（绝对语义幂等）。

    使用 QTest 合成 press/move/release，验证：
    - drag_dx 是相对 press 瞬间的增量，而非光标距窗口左缘的绝对距离；
    - 连续 move 不会在已更新的 scale 上重复叠加（双重累计）。
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
    # 右移 50px：总位移 50，scale = 1.0 + 50/100 = 1.5，窗口宽 150
    QTest.mouseMove(w, QPoint(145, 95))
    assert w.current_scale() == pytest.approx(1.5, abs=0.1)
    assert w.width() == pytest.approx(150, abs=1)
    # 再右移 10px：总位移 60，scale = 1.6（双重累计会得出 2.1）
    QTest.mouseMove(w, QPoint(155, 95))
    assert w.current_scale() == pytest.approx(1.6, abs=0.1)
    # 回拖 50px：总位移 10，scale = 1.1（双重累计会得出 2.2）
    QTest.mouseMove(w, QPoint(105, 95))
    assert w.current_scale() == pytest.approx(1.1, abs=0.1)
    QTest.mouseRelease(w, Qt.LeftButton, pos=QPoint(105, 95))


def test_window_min_scale_on_start(qapp, tmp_path):
    """启动 scale 钳制：config 里合法但小于 0.3 的 scale 被抬到最小 0.3。"""
    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    cfg.set("window.scale", 0.1)
    w = PetWindow(pm, cfg)
    assert w.current_scale() == 0.3
    assert w.width() == 30


def test_hud_is_top_level_window(qapp, tmp_path):
    """HUD 是独立顶层窗口（child widget 绘制会被裁剪到父窗口矩形内，且 windowOpacity 只对顶层生效）。"""
    from PySide6.QtCore import Qt

    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    hud = w._hud
    assert hud.isWindow() is True
    assert hud.windowFlags() & Qt.Tool
    assert hud.isHidden() is True  # 构造后初始隐藏


def test_hud_follows_window_position(qapp, tmp_path):
    """主窗口移动后，HUD 以全局坐标跟随到窗口右缘外侧（x = 窗口 x + 宽 + 6）。"""
    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.show()
    w.move(200, 150)
    hud = w._hud
    assert hud.pos().x() == w.pos().x() + w.width() + 6
    assert hud.pos().y() == w.pos().y()


def test_hud_fade_out_hides(qapp, tmp_path):
    """顶层窗口上 windowOpacity 动画有效，fade_out 完成（opacity<=0.01）后触发 hide。"""
    from PySide6.QtTest import QTest

    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.show()
    hud = w._hud
    hud.fade_in()
    hud.fade_out()
    QTest.qWait(250)  # 动画 150ms，等待完成并触发 finished 回调
    assert hud.isHidden() is True


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
