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
    assert hud.isHidden() is False  # 常驻显示：构造后即浮现


def test_hud_follows_window_position(qapp, tmp_path):
    """主窗口移动后，HUD 以全局坐标跟随到窗口右缘（轻微重叠 x = 窗口 x + 宽 - 24）。"""
    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.show()
    w.move(200, 150)
    hud = w._hud
    assert hud.pos().x() == w.pos().x() + w.width() - 24
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


def test_pose_threshold_logic(qapp, tmp_path):
    """姿势判定单元：上拖过阈值 up、下拖过阈值 down、阈值内 normal。"""
    from PySide6.QtCore import QPoint

    normal = QPixmap(100, 100); normal.fill()
    up = QPixmap(100, 100); up.fill()
    down = QPixmap(100, 100); down.fill()
    w = PetWindow(normal, Config(tmp_path / "config.json"),
                  poses={"normal": normal, "up": up, "down": down})
    w._drag_start_global = QPoint(100, 100)
    w._update_pose(QPoint(100, 80))   # dy=-20 → up
    assert w._pose == "up"
    w._update_pose(QPoint(100, 150))  # dy=+50 → down
    assert w._pose == "down"
    w._update_pose(QPoint(100, 105))  # dy=+5（阈值内）→ normal
    assert w._pose == "normal"


def test_drag_up_then_release_restores_pose(qapp, tmp_path):
    """集成：按住向上拖 → up；松开 → 恢复 normal。"""
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    normal = QPixmap(100, 100); normal.fill(Qt.gray)
    up = QPixmap(100, 100); up.fill(Qt.red)
    down = QPixmap(100, 100); down.fill(Qt.blue)
    w = PetWindow(normal, Config(tmp_path / "config.json"),
                  poses={"normal": normal, "up": up, "down": down})
    w.show()
    QTest.mousePress(w, Qt.LeftButton, pos=QPoint(50, 50))
    assert w._pose == "normal"
    QTest.mouseMove(w, QPoint(50, 30))  # 全局上移 → up
    assert w._pose == "up"
    QTest.mouseRelease(w, Qt.LeftButton, pos=QPoint(50, 30))
    assert w._pose == "normal"
    assert w._actor._pixmap is normal


def test_toggle_pause(qapp, tmp_path):
    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.set_paused(True)
    assert w._paused is True
    w.set_paused(False)
    assert w._paused is False


def test_click_toggles_launch_ring(qapp, tmp_path):
    """短按（无拖动）→ 弹出快捷环；再点 → 收起。"""
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.show()
    assert w._launch_ring.isHidden() is True
    QTest.mousePress(w, Qt.LeftButton, pos=QPoint(50, 50))
    QTest.mouseRelease(w, Qt.LeftButton, pos=QPoint(50, 50))
    assert w._launch_ring.isVisible() is True
    QTest.mousePress(w, Qt.LeftButton, pos=QPoint(50, 50))
    QTest.mouseRelease(w, Qt.LeftButton, pos=QPoint(50, 50))
    assert w._launch_ring.isHidden() is True


def test_drag_does_not_open_launch_ring(qapp, tmp_path):
    """拖动（有位移）→ 不弹快捷环。"""
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.show()
    QTest.mousePress(w, Qt.LeftButton, pos=QPoint(50, 50))
    QTest.mouseMove(w, QPoint(60, 60))  # 移动 10px+，超过点击阈值
    QTest.mouseRelease(w, Qt.LeftButton, pos=QPoint(60, 60))
    assert w._launch_ring.isHidden() is True
