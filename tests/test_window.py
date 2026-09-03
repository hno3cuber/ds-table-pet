from PySide6.QtCore import QPoint
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
    w.show()
    w._enter_resize_mode()
    # 按住右下角手柄，press 在 (95,95)，对角锚点=左上角=(窗口 x, 窗口 y)
    press = QPoint(w.x() + 95, w.y() + 95)
    w._begin_resize(3, press)
    # 拖到锚点位置 → ratio→0 → 钳制到 min_scale
    w._apply_resize(QPoint(w.x(), w.y()))
    assert w.current_scale() <= 0.1


def test_resize_drag_incremental_scale(qapp, tmp_path):
    """PPT 式角点缩放：拖右下角，光标远离对角锚点 → 放大；靠近 → 缩小。

    连续 move 不会双重累计（scale 始终由「当前光标」与 press 起点一次性算出）。
    """
    import pytest
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    w = PetWindow(pm, cfg)
    w.show()
    w.move(100, 100)  # offscreen 会把负坐标钳到 0
    w._enter_resize_mode()
    # 右下角手柄命中区
    QTest.mousePress(w, Qt.LeftButton, pos=QPoint(95, 95))
    # 右下拖 50px：光标沿对角线远离锚点 → 放大（手柄命中在 95，ratio≈1.53）
    QTest.mouseMove(w, QPoint(145, 145))
    assert w.current_scale() > 1.3
    assert w.width() > 130
    # 再拖：scale 不双重累计（一次性从 press 算）
    QTest.mouseMove(w, QPoint(155, 155))
    assert w.current_scale() > 1.5
    # 回拖：光标回到接近 press 位置 → scale 回到约 1.0
    QTest.mouseMove(w, QPoint(100, 100))
    assert w.current_scale() == pytest.approx(1.0, abs=0.2)
    QTest.mouseRelease(w, Qt.LeftButton, pos=QPoint(100, 100))


def test_resize_anchor_opposite_corner_fixed(qapp, tmp_path):
    """PPT 式对角锡定：拖右下角时左上角不动，拖左上角时右下角不动。"""
    import pytest
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    w = PetWindow(pm, cfg)
    w.show()
    w.move(200, 200)
    w._enter_resize_mode()

    # 拖右下角：锡点=左上角 (200,200)，缩放后左上角不动
    QTest.mousePress(w, Qt.LeftButton, pos=QPoint(95, 95))
    QTest.mouseMove(w, QPoint(145, 145))  # 放大
    assert w.x() == 200 and w.y() == 200  # 左上角没动
    QTest.mouseRelease(w, Qt.LeftButton, pos=QPoint(145, 145))

    # 重新进入缩放模式（release 后已退出本次拖拽），拖左上角：锡点=右下角
    w._enter_resize_mode()
    old_right = w.x() + w.width()
    old_bottom = w.y() + w.height()
    QTest.mousePress(w, Qt.LeftButton, pos=QPoint(5, 5))
    QTest.mouseMove(w, QPoint(-50, -50))  # 左上角向左上拖 → 放大
    # 右下角应该钉死不动
    new_right = w.x() + w.width()
    new_bottom = w.y() + w.height()
    assert abs(new_right - old_right) <= 1
    assert abs(new_bottom - old_bottom) <= 1
    QTest.mouseRelease(w, Qt.LeftButton, pos=QPoint(-50, -50))


def test_resize_free_aspect_ratio(qapp, tmp_path):
    """不锁宽高比：光标只水平移动 → 宽度变、高度不变；scale_x/scale_y 独立。"""
    import pytest
    from PySide6.QtCore import QPoint

    pm = QPixmap(200, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    w = PetWindow(pm, cfg)
    w.show()
    w.move(300, 300)
    w._enter_resize_mode()
    # 拖右下角：锡=左上 (300,300)；press 在角 (500,400) → start
    w._begin_resize(3, QPoint(500, 400))
    w._resize_start_scale = w.current_scale()
    # 水平向右拖到 (600, 400)：宽度 200→300，高度保持 100 不变
    w._apply_resize(QPoint(600, 400))
    assert w.width() == 300
    assert w.height() == 100  # 高度没变（自由宽高比）
    sx, sy = w.current_scales()
    assert sx == pytest.approx(1.5)
    assert sy == pytest.approx(1.0)


def test_resize_save_and_restore_free_aspect(qapp, tmp_path):
    """自由宽高比（scale_x≠scale_y）保存后重启恢复。"""
    import pytest
    from PySide6.QtCore import QPoint

    pm = QPixmap(200, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    w = PetWindow(pm, cfg)
    w.show()
    w.move(300, 300)
    w._enter_resize_mode()
    w._begin_resize(3, QPoint(500, 400))
    w._resize_start_scale = w.current_scale()
    w._apply_resize(QPoint(600, 400))  # 宽 1.5x，高不变
    w.save_scale()

    # 重新构建：应恢复 scale_x=1.5, scale_y=1.0
    w2 = PetWindow(pm, Config(tmp_path / "config.json"))
    assert w2.current_scales() == (pytest.approx(1.5), pytest.approx(1.0))
    assert w2.width() == 300
    assert w2.height() == 100


def test_resize_shift_keeps_aspect(qapp, tmp_path):
    """按住 Shift 拖角 → 等比缩放（scale_x == scale_y）。"""
    import pytest
    from PySide6.QtCore import QPoint

    pm = QPixmap(200, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    w = PetWindow(pm, cfg)
    w.show()
    w.move(300, 300)
    w._enter_resize_mode()
    w._begin_resize(3, QPoint(500, 400))  # 右下角手柄，锡=左上 (300,300)
    w._resize_start_scale = w.current_scale()
    # 按住 Shift 斜向右下拖：等比放大
    w._apply_resize(QPoint(650, 525), keep_aspect=True)
    sx, sy = w.current_scales()
    assert sx == pytest.approx(sy)  # 锁比
    assert sx > 1.0



def test_window_min_scale_on_start(qapp, tmp_path):
    """启动 scale 钳制：config 里合法但小于 0.1 的 scale 被抬到最小 0.1。"""
    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    cfg.set("window.scale", 0.01)
    w = PetWindow(pm, cfg)
    assert w.current_scale() == 0.1
    assert w.width() == 10


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


def test_enter_resize_mode_brings_pet_to_front(qapp, tmp_path, monkeypatch):
    """进入缩放模式时把本体 raise + activate，让调整框盖在快捷环之上
    （环的对角圆与角色四角重叠，不置顶则手柄被环遮住点不到）。"""
    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.show()
    calls = []
    monkeypatch.setattr(w, "raise_", lambda: calls.append("raise"))
    monkeypatch.setattr(w, "activateWindow", lambda: calls.append("activate"))
    w._enter_resize_mode()
    assert w._resize_mode is True
    assert calls == ["raise", "activate"]


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


def test_quit_calls_app_quit(qapp, tmp_path, monkeypatch):
    """退出：关闭窗口并显式 quit（Tool 窗口不触发 quitOnLastWindowClosed，
    否则 HUD/快捷环会残留挂屏）。"""
    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.show()
    calls = []
    monkeypatch.setattr(qapp, "quit", lambda: calls.append("quit"))
    w._quit()
    assert w.isHidden() is True       # 窗口已关
    assert calls == ["quit"]          # 应用已显式退出


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
