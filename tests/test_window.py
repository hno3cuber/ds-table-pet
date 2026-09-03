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


# ---- 自由走动（随机站/走 + 边缘掉头） ----

def _make_walk_window(qapp, tmp_path, n_frames=4, wander=True):
    """构造带行走帧序列的窗口；默认关闭 wander 由测试自行驱动。"""
    pm = QPixmap(200, 300)
    pm.fill()
    frames = []
    for _ in range(n_frames):
        f = QPixmap(60, 80)
        f.fill()
        frames.append(f)
    cfg = Config(tmp_path / "config.json")
    cfg.set("wander.enabled", wander)
    w = PetWindow(pm, cfg, walk_frames=frames)
    w._halt_wander()  # 清掉构造时排程，从已知静止状态出发
    return w


def test_wander_disabled_without_frames(qapp, tmp_path):
    """没有行走帧时（旧调用/资源缺失）wander 强制关闭，不排程不崩溃。"""
    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    cfg.set("wander.enabled", True)
    w = PetWindow(pm, cfg)  # 无 walk_frames
    assert w._wander_enabled is False
    assert w._hold_timer.isActive() is False


def test_wander_disabled_by_config(qapp, tmp_path):
    """config wander.enabled=False → 构造后不进入走动状态机。"""
    w = _make_walk_window(qapp, tmp_path, wander=False)
    assert w._wander_enabled is False
    assert w._hold_timer.isActive() is False


def test_wander_enable_starts_idle_schedule(qapp, tmp_path):
    """开启 wander → 从站立开始，hold 定时器已排程。"""
    w = _make_walk_window(qapp, tmp_path)
    w.set_wander_enabled(True)
    assert w._wander_enabled is True
    assert w._walking is False          # 先站立
    assert w._hold_timer.isActive() is True
    assert w._actor._frames is None     # 静态立绘


def test_wander_walking_advances_frame_and_moves(qapp, tmp_path, monkeypatch):
    """行走 tick：位置刷新平滑移动、动画 tick 切下一帧（两者解耦）。"""
    w = _make_walk_window(qapp, tmp_path)
    monkeypatch.setattr(w, "_wander_bounds", lambda: (0, 1000))
    w.set_wander_enabled(True)
    w._start_walking()
    w._wander_dir = -1
    w._actor.set_mirror(False)
    w.move(500, 100)
    w._wander_move_tick()          # 位置：4px 平滑步
    assert w.pos().x() == 500 - 4
    assert w._actor._mirror is False   # 朝左（素材默认方向）不镜像
    w._wander_frame_tick()         # 动画：切下一帧
    assert w._wander_frame == 1
    assert w._actor._frame_index == 1
    assert w._actor._frames is not None


def test_wander_bounces_at_left_edge_and_mirrors(qapp, tmp_path, monkeypatch):
    """走到屏幕左缘 → 钳回边界、掉头朝右、镜像翻转素材。"""
    w = _make_walk_window(qapp, tmp_path)
    monkeypatch.setattr(w, "_wander_bounds", lambda: (0, 1000))
    w.set_wander_enabled(True)
    w._start_walking()
    w._wander_dir = -1
    w._actor.set_mirror(False)
    w.move(1, 100)
    w._wander_move_tick()  # 1 - 2 → 越界 → 钳到 0 并掉头朝右
    assert w.pos().x() == 0
    assert w._wander_dir == 1
    assert w._actor._mirror is True     # 朝右走 → 素材水平翻转


def test_wander_bounces_at_right_edge(qapp, tmp_path, monkeypatch):
    """右缘掉头：x = right - width 处朝右走 → 钳回并掉头朝左。"""
    w = _make_walk_window(qapp, tmp_path)  # 窗口宽 = pixmap 宽 200
    monkeypatch.setattr(w, "_wander_bounds", lambda: (0, 500))
    w.set_wander_enabled(True)
    w._start_walking()
    w._wander_dir = 1
    w._actor.set_mirror(True)
    w.move(299, 100)  # 右缘 499 < 500，再走一步就出界
    w._wander_move_tick()
    assert w.pos().x() == 500 - 200   # 钳回 right - width
    assert w._wander_dir == -1
    assert w._actor._mirror is False


def test_wander_hold_elapsed_switches_state(qapp, tmp_path):
    """hold 到点：站立→行走、行走→站立 自动轮转。"""
    w = _make_walk_window(qapp, tmp_path)
    w.set_wander_enabled(True)
    w._hold_timer.stop()
    # 站立到点 → 开始行走
    w._walking = False
    w._on_wander_hold()
    assert w._walking is True
    assert w._walk_timer.isActive() is True
    assert w._frame_timer.isActive() is True   # 位移与动画帧两个 timer 都已驱动
    # 行走时长到点 → 回到站立
    w._walking = True
    w._on_wander_hold()
    assert w._walking is False
    assert w._actor._frames is None
    assert w._walk_timer.isActive() is False
    assert w._hold_timer.isActive() is True   # 已排下一次


def test_wander_touch_interrupt_stops_walking(qapp, tmp_path):
    """鼠标按下（开始拖/点）→ 立即停走回站立并进入安静期。"""
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    w = _make_walk_window(qapp, tmp_path)
    w.set_wander_enabled(True)
    w._start_walking()
    assert w._walking is True
    w.show()
    QTest.mousePress(w, Qt.LeftButton, pos=QPoint(10, 10))
    assert w._walking is False
    assert w._actor._frames is None
    assert w._walk_timer.isActive() is False
    assert w._frame_timer.isActive() is False
    assert w._hold_timer.isActive() is True  # 安静期已排程


def test_wander_pause_halts_and_resume_restarts(qapp, tmp_path):
    """暂停监控 → 走动状态机停摆；恢复 → 重新从站立排程。"""
    w = _make_walk_window(qapp, tmp_path)
    w.set_wander_enabled(True)
    w._start_walking()
    assert w._walking is True
    w.set_paused(True)
    assert w._walking is False
    assert w._walk_timer.isActive() is False
    assert w._frame_timer.isActive() is False
    assert w._hold_timer.isActive() is False
    w.set_paused(False)
    assert w._walk_timer.isActive() is False
    assert w._hold_timer.isActive() is True   # 恢复后从站立重新随机


def test_wander_resize_mode_halts_and_exit_resumes(qapp, tmp_path):
    """进入缩放模式 → 停走；退出缩放 → 恢复站立排程。"""
    w = _make_walk_window(qapp, tmp_path)
    w.set_wander_enabled(True)
    w._start_walking()
    assert w._walking is True
    w._enter_resize_mode()
    assert w._walking is False
    assert w._walk_timer.isActive() is False
    assert w._frame_timer.isActive() is False
    w._exit_resize_mode()
    assert w._hold_timer.isActive() is True


def test_wander_disable_stops_everything(qapp, tmp_path):
    """菜单关闭自由走动 → 立即停走，不再排程。"""
    w = _make_walk_window(qapp, tmp_path)
    w.set_wander_enabled(True)
    w._start_walking()
    w.set_wander_enabled(False)
    assert w._wander_enabled is False
    assert w._walking is False
    assert w._walk_timer.isActive() is False
    assert w._frame_timer.isActive() is False
    assert w._hold_timer.isActive() is False
    assert w._actor._frames is None


def test_wander_frame_loops_around(qapp, tmp_path, monkeypatch):
    """帧序列走到末尾自动绕回第 0 帧。"""
    w = _make_walk_window(qapp, tmp_path, n_frames=3)
    monkeypatch.setattr(w, "_wander_bounds", lambda: (0, 5000))
    w.set_wander_enabled(True)
    w._start_walking()
    w.move(3000, 100)
    for _ in range(5):
        w._wander_frame_tick()
    assert w._wander_frame == 5 % 3
    assert w._actor._frame_index == 5 % 3


# ---- 站立循环动画（idel.gif 帧播放） ----

def _make_idle_window(qapp, tmp_path, n_frames=4, with_walk=False):
    """构造带站立循环帧的窗口。with_walk=True 时同时带行走帧（走动开着）。"""
    pm = QPixmap(200, 300)
    pm.fill()
    idle = []
    for _ in range(n_frames):
        f = QPixmap(60, 80)
        f.fill()
        idle.append(f)
    walk = None
    if with_walk:
        walk = []
        for _ in range(3):
            f = QPixmap(60, 80)
            f.fill()
            walk.append(f)
    cfg = Config(tmp_path / "config.json")
    cfg.set("wander.enabled", True)
    w = PetWindow(pm, cfg, idle_frames=idle, idle_delays=[40, 40, 40, 40],
                  walk_frames=walk)
    return w


def test_idle_frames_play_without_walk(qapp, tmp_path):
    """只有站立循环素材（无行走帧）→ 不走动，站立动画独立播放。"""
    w = _make_idle_window(qapp, tmp_path, with_walk=False)
    assert w._wander_enabled is False
    assert w._walking is False
    assert w._actor._frames is not None     # 站立循环已挂载
    assert w._idle_timer.isActive() is True
    assert w._hold_timer.isActive() is False  # 不排行走


def test_idle_frame_advances(qapp, tmp_path):
    """站立循环 tick：按素材延迟推进下一帧并绕回。"""
    w = _make_idle_window(qapp, tmp_path, n_frames=3, with_walk=False)
    assert w._idle_frame == 0
    w._idle_frame_tick()
    assert w._idle_frame == 1
    assert w._actor._frame_index == 1
    w._idle_frame_tick()
    w._idle_frame_tick()
    assert w._idle_frame == 0   # 3 帧循环绕回


def test_idle_walk_switch_frames(qapp, tmp_path):
    """站立↔行走状态切换时动画源随之切换，站立循环让位给行走帧再恢复。"""
    w = _make_idle_window(qapp, tmp_path, with_walk=True)
    assert w._wander_enabled is True
    idle_len = len(w._idle_frames)
    assert len(w._actor._frames) == idle_len    # 初始：站立循环
    assert w._idle_timer.isActive() is True

    w._start_walking()
    assert len(w._actor._frames) == len(w._walk_frames)  # 切到行走帧
    assert w._idle_timer.isActive() is False              # 站立 timer 让位
    assert w._frame_timer.isActive() is True

    w._enter_idle()
    assert len(w._actor._frames) == idle_len              # 回到站立循环
    assert w._idle_timer.isActive() is True
    assert w._frame_timer.isActive() is False


def test_idle_halt_freezes_and_resume_plays(qapp, tmp_path):
    """暂停监控：站立循环冻结回静态；恢复：站立循环继续（无走动也如此）。"""
    w = _make_idle_window(qapp, tmp_path, with_walk=False)
    assert w._idle_timer.isActive() is True
    w.set_paused(True)
    assert w._actor._frames is None          # 冻结回静态首帧
    assert w._idle_timer.isActive() is False
    w.set_paused(False)
    assert w._actor._frames is not None      # 恢复站立循环
    assert w._idle_timer.isActive() is True


def test_idle_walk_stop_wander_keeps_idle(qapp, tmp_path):
    """菜单关掉自由走动：行走停止，站立循环保留（宠物安静但活着）。"""
    w = _make_idle_window(qapp, tmp_path, with_walk=True)
    w._start_walking()
    assert w._walking is True
    w.set_wander_enabled(False)
    assert w._wander_enabled is False
    assert w._walking is False
    assert w._walk_timer.isActive() is False
    assert w._hold_timer.isActive() is False
    assert len(w._actor._frames) == len(w._idle_frames)  # 回站立循环
    assert w._idle_timer.isActive() is True
