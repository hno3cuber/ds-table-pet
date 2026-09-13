import random
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QVBoxLayout, QWidget

from pet.actor import ActorWidget
from pet.balance import BalanceFetcher
from pet.geometry import (
    anchor_and_topleft,
    corner_resize_size,
    scale_from_corner_drag,
    scaled_size,
    scaled_size_xy,
    wander_step_x,
)
from pet.hud import HudPanel
from pet.launch_ring import LaunchRing

_CLICK_THRESHOLD = 6     # press 与 release 位移小于该值视为「点击」（弹出快捷环）
_MIN_SCALE = 0.1          # 单方向最小缩放系数
_WALK_FRAME_MS = 50           # 动画帧间隔：20fps 播放（素材 25 帧 → 步态循环 1.25s，活泼不拖沓）
_WANDER_MOVE_MS = 25          # 位置刷新间隔：位移与动画解耦，40fps 平滑移动不跳帧
_WALK_STEP_PX = 4             # 每次位置刷新位移 4px（4px/25ms = 160px/s，与步频翻倍同步，步幅不变）
_IDLE_FRAME_MS = 100          # 站立循环默认帧停留（idel.gif 未带延迟信息时回退）
# 行走帧视觉大小修正（实测）：idel.gif 内容高 766.6 / walk.gif 内容高 803.1 →
# 行走角色高约 4.7%，乘 0.955 让两侧角色视觉等高（画布同为 720x960 时即内容高比）
_WALK_VISUAL_SCALE = 0.955
_WANDER_IDLE_MS = (2000, 6000)     # 站立随机时长范围
_WANDER_WALK_MS = (4000, 10000)    # 连续行走随机时长范围
_WANDER_QUIET_MS = (10000, 14000)  # 用户触摸打断后的安静期范围（给操作留空间）


class PetWindow(QWidget):
    def __init__(self, pixmap: QPixmap, config, poses=None,
                 idle_frames=None, idle_delays=None, walk_frames=None):
        super().__init__()
        self._pixmap = pixmap
        self._config = config
        self._press_global = None
        self._launch_ring = LaunchRing(config)
        self._pose_pixmap = None        # 举牌姿态图（token.png），由 main 启动时注入
        self._balance_fetcher = None    # 惰性创建：首次查看余额时实例化
        self._balance_mode = False      # 当前是否处于举牌查余额姿态
        base = float(config.get("window.scale", 1.0))
        # 自由宽高比：scale_x/scale_y 各自独立（缺失/未设置时回退到等比 scale）
        sx = config.get("window.scale_x")
        sy = config.get("window.scale_y")
        if sx is None or sy is None:
            sx = sy = base
        self._scale_x = max(_MIN_SCALE, float(sx))
        self._scale_y = max(_MIN_SCALE, float(sy))
        self._paused = False
        self._resize_mode = False
        self._drag_offset = None
        self._resize_corner = None
        self._resize_start_scale = 0.0
        self._resize_anchor = (0, 0)       # 对角锚点全局坐标（拖角时固定不动）
        self._resize_start_vec = (0, 0)   # press 时光标→锚点的向量（投影基准）
        self._plugins = []
        # 自由走动（随机站/走）：行走帧来自 walk.gif 内存拆帧，无素材则整体关闭
        self._idle_frames = list(idle_frames) if idle_frames else None   # 站立循环帧
        self._idle_delays = list(idle_delays) if idle_delays else None   # 每帧停留（ms）
        self._idle_frame = 0
        self._walk_frames = list(walk_frames) if walk_frames else None
        self._walking = False
        self._wander_dir = -1
        self._wander_frame = 0
        self._breathing = bool(config.get("breathing_animation", True))
        self._wander_enabled = False
        self._idle_timer = QTimer(self)    # 站立循环帧切换：按素材帧延迟播放
        self._idle_timer.setTimerType(Qt.PreciseTimer)
        self._idle_timer.timeout.connect(self._idle_frame_tick)
        self._walk_timer = QTimer(self)    # 行走位置刷新：40fps 平滑移动
        self._walk_timer.setTimerType(Qt.PreciseTimer)  # Windows 默认时钟 15.6ms 粒度会拉低帧率，申请高精度
        self._walk_timer.setInterval(_WANDER_MOVE_MS)
        self._walk_timer.timeout.connect(self._wander_move_tick)
        self._frame_timer = QTimer(self)   # 行走动画帧切换：20fps 播放素材
        self._frame_timer.setTimerType(Qt.PreciseTimer)
        self._frame_timer.setInterval(_WALK_FRAME_MS)
        self._frame_timer.timeout.connect(self._wander_frame_tick)
        self._hold_timer = QTimer(self)  # 站/走时长单发计时：到点后状态轮转
        self._hold_timer.setSingleShot(True)
        self._hold_timer.timeout.connect(self._on_wander_hold)

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._actor = ActorWidget(pixmap, self._scale_y)
        self._actor.set_breathing(self._breathing)
        layout.addWidget(self._actor)

        self._hud = HudPanel()
        self._hud.set_scale(self._scale_y)
        self._hud.fade_in()  # 常驻显示：启动即浮现监测面板，不再依赖鼠标悬停

        w, h = scaled_size_xy(pixmap.width(), pixmap.height(), self._scale_x, self._scale_y)
        self.resize(w, h)
        pos = self._config.get("window.pos", [100, 100])
        self.move(pos[0], pos[1])
        wander_on = bool(config.get("wander.enabled", False)) and bool(self._walk_frames)
        if wander_on:
            self.set_wander_enabled(True)   # 进站立循环并随机排走
        else:
            self._show_idle_animation()     # 不走动也播放站立循环（活着但不溜达）

    # ---- 查询 ----
    def current_scale(self) -> float:
        """纵向缩放系数（自由宽高比时以高度为主观感尺度）。"""
        return self._scale_y

    def current_scales(self) -> tuple[float, float]:
        return (self._scale_x, self._scale_y)

    def current_pos(self):
        p = self.pos()
        return [p.x(), p.y()]

    def set_pose_pixmap(self, pixmap):
        """注入举牌姿态图（token.png）。"""
        self._pose_pixmap = pixmap

    def install_plugin(self, plugin):
        self._plugins.append(plugin)
        self._hud.add_block(plugin.panel(self._hud))

    def set_paused(self, paused: bool):
        self._paused = paused
        for plugin in self._plugins:
            plugin.set_paused(paused)
        self._hud.show_paused(paused)
        if paused:
            self._halt_wander()
        else:
            self._resume_wander()

    # ---- 余额姿态 ----
    def toggle_balance(self):
        """切换举牌查余额姿态：开 → 切姿态并异步查询；关 → 回常态动画。"""
        if self._balance_mode:
            self.exit_balance()
        else:
            self.enter_balance()

    def enter_balance(self):
        """进入举牌姿态：站定，显示查询中，发起异步余额请求。"""
        if self._pose_pixmap is None:
            return
        self._balance_mode = True
        self._halt_wander()                 # 举牌时站定，不再溜达
        self._actor.set_pose(self._pose_pixmap, "查询中…")
        self._actor.set_breathing(False)    # 牌面文字不跟着呼吸缩放
        if self._balance_fetcher is None:
            base_dir = Path(__file__).resolve().parent.parent
            self._balance_fetcher = BalanceFetcher(base_dir, self)
            self._balance_fetcher.finished.connect(self._on_balance_result)
        self._balance_fetcher.fetch()

    def exit_balance(self):
        """退出举牌姿态：恢复动画/静态立绘，并按当前设置恢复走动。"""
        self._balance_mode = False
        self._actor.set_pose(None)
        self._actor.set_breathing(self._breathing)
        self._resume_wander()

    def _on_balance_result(self, text: str, ok: bool):
        """余额返回：仅当仍处于举牌姿态时刷新牌面。"""
        if self._balance_mode:
            self._actor.set_sign_text(text)

    # ---- 缩放（PPT 式角点拖拽：对角固定，宽高自由，Shift 锁等比） ----
    def _enter_resize_mode(self):
        """进入缩放模式：显示选框与手柄，等待用户按角点。"""
        self._halt_wander()  # 用户开始操作本体：行走让位
        self._resize_mode = True
        self._actor.set_resize_mode(True)
        # 本体（含调整框）盖到快捷环之上：环的对角圆与角色四角几何重叠，
        # 同为置顶窗口时后 raise/activate 的在上，否则手柄被环遮住点不到。
        self.raise_()
        self.activateWindow()

    def _begin_resize(self, corner: int, press_global: QPoint):
        """用户按住了某个角点手柄，开始一次拖拽。

        记录 press 瞬间的窗口几何、对角锚点（固定的那个顶点）与
        光标→锚点向量，作为后续缩放的基准。"""
        self._resize_corner = corner
        self._resize_start_scale = self._scale_y
        old_tl = (self.x(), self.y())
        old_size = (self.width(), self.height())
        anchor, _ = anchor_and_topleft(corner, old_tl, old_size, old_size)
        self._resize_anchor = anchor
        self._resize_start_vec = (press_global.x() - anchor[0],
                                  press_global.y() - anchor[1])

    def _apply_resize(self, cursor_global: QPoint, keep_aspect: bool = False):
        """PPT 式角点拖拽：对角锚点不动，窗口朝光标方向伸缩。

        默认宽高自由（各自跟随光标）；keep_aspect（按住 Shift）时按
        原图比例等比缩放。"""
        ow, oh = self._pixmap.width(), self._pixmap.height()
        anchor = self._resize_anchor
        if keep_aspect:
            cur_vec = (cursor_global.x() - anchor[0], cursor_global.y() - anchor[1])
            scale = scale_from_corner_drag(self._resize_start_vec, cur_vec,
                                           self._resize_start_scale, _MIN_SCALE)
            w, h = scaled_size(ow, oh, scale)
            self._scale_x = scale
            self._scale_y = scale
        else:
            min_w = max(1, round(ow * _MIN_SCALE))
            min_h = max(1, round(oh * _MIN_SCALE))
            w, h = corner_resize_size(self._resize_corner, anchor,
                                      (cursor_global.x(), cursor_global.y()),
                                      min_w=min_w, min_h=min_h)
            self._scale_x = w / ow
            self._scale_y = h / oh
        self._actor.set_scale(self._scale_y)
        old_tl = (self.x(), self.y())
        old_size = (self.width(), self.height())
        _, new_tl = anchor_and_topleft(self._resize_corner, old_tl, old_size, (w, h))
        self.setGeometry(new_tl[0], new_tl[1], w, h)
        self._hud.set_scale(self._scale_y)

    def _finish_resize(self):
        self._resize_corner = None
        self._resize_start_scale = 0.0
        self._resize_start_vec = (0, 0)
        self.save_scale()

    def save_scale(self):
        self._config.set("window.scale_x", self._scale_x)
        self._config.set("window.scale_y", self._scale_y)
        self._config.set("window.scale", self._scale_y)  # 兜底兼容字段
        self._config.save()

    def _exit_resize_mode(self):
        self._resize_mode = False
        self._resize_corner = None
        self._resize_start_scale = 0.0
        self._resize_start_vec = (0, 0)
        self._drag_offset = None
        self._actor.set_resize_mode(False)
        self.unsetCursor()
        self._resume_wander()  # 退出缩放：重新从站立随机

    # ---- 快捷环 ----
    def _toggle_launch_ring(self):
        ring = self._launch_ring
        if ring.isVisible():
            ring.hide()
        else:
            center = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
            pet_radius = max(self.width(), self.height()) // 2
            ring.layout_for(center, pet_radius)
            ring.show()

    # ---- 鼠标事件 ----
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._interrupt_wander()
            self._show_menu(event.globalPosition().toPoint())
            return
        if event.button() != Qt.LeftButton:
            return
        local = event.position().toPoint()
        if self._resize_mode:
            corner = self._actor.handle_at(local)
            if corner is not None:
                self._begin_resize(corner, event.globalPosition().toPoint())
                self._drag_offset = None
                return
        self._interrupt_wander()  # 用户伸手：停走进入安静期
        self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        self._press_global = event.globalPosition().toPoint()
        self._resize_corner = None

    def mouseMoveEvent(self, event):
        if self._resize_corner is not None:
            keep_aspect = bool(event.modifiers() & Qt.ShiftModifier)
            self._apply_resize(event.globalPosition().toPoint(), keep_aspect)
            return
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if self._resize_corner is not None:
            self._finish_resize()
        # 点击判定：press 与 release 几乎没位移 → 弹出/收起快捷环
        if self._resize_corner is None and self._press_global is not None:
            delta = event.globalPosition().toPoint() - self._press_global
            if delta.manhattanLength() < _CLICK_THRESHOLD:
                self._toggle_launch_ring()
        self._press_global = None
        self._drag_offset = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self._resize_mode:
            self._exit_resize_mode()
        else:
            super().keyPressEvent(event)

    def _position_hud(self):
        self._hud.adjustSize()
        # HUD 是独立顶层窗口，用全局坐标同步到主窗口右缘（轻微重叠，贴着角色）
        self._hud.move(self.mapToGlobal(QPoint(self.width() - 24, 0)))

    def _relayout_launch_ring(self):
        """圆环展开时按当前本体尺寸重新布局：环的大小与位置都依赖
        pet_radius（中心到圆环的距离），本体缩放/移动后必须重新计算。"""
        if self._launch_ring.isVisible():
            center = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
            pet_radius = max(self.width(), self.height()) // 2
            self._launch_ring.layout_for(center, pet_radius)

    def _sync_satellites(self):
        """HUD 与展开的快捷环跟随本体：位置或尺寸变化后重新对齐。"""
        self._position_hud()
        self._relayout_launch_ring()

    def resizeEvent(self, event):
        self._sync_satellites()
        super().resizeEvent(event)

    def moveEvent(self, event):
        self._sync_satellites()
        super().moveEvent(event)

    def showEvent(self, event):
        self._position_hud()
        super().showEvent(event)

    # ---- 菜单 ----
    def _show_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        pause_text = "恢复监控" if self._paused else "暂停监控"
        action_pause = menu.addAction(pause_text)
        action_wander = menu.addAction("自由走动")
        action_wander.setCheckable(True)
        action_wander.setChecked(self._wander_enabled)
        action_resize = menu.addAction("调整大小")
        balance_text = "关闭余额牌" if self._balance_mode else "查看余额"
        action_balance = menu.addAction(balance_text)
        menu.addSeparator()
        action_quit = menu.addAction("退出")
        chosen = menu.exec(global_pos)
        if chosen is action_pause:
            self.set_paused(not self._paused)
        elif chosen is action_wander:
            self.set_wander_enabled(not self._wander_enabled)
            self._config.set("wander.enabled", self._wander_enabled)
            self._config.save()
        elif chosen is action_resize:
            if self._resize_mode:
                self._exit_resize_mode()
            else:
                self._enter_resize_mode()
        elif chosen is action_balance:
            self.toggle_balance()
        elif chosen is action_quit:
            self._quit()

    def _quit(self):
        """退出：窗口全是 Qt.Tool 类型（不触发 quitOnLastWindowClosed），
        必须显式 quit 才会结束事件循环并销毁所有窗口（含 HUD 与快捷环）。"""
        self.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    # ---- 自由走动（随机站/走，边缘掉头） ----

    def set_wander_enabled(self, enabled: bool):
        """开关自由走动。开 → 站立循环 + 随机站走；关 → 停走，仅保留站立循环。

        没有行走帧素材时（旧调用/资源缺失）走动保持关闭；站立循环由 idle 素材
        独立驱动（无 idle 素材则回静态立绘）。"""
        self._wander_enabled = bool(enabled) and bool(self._walk_frames)
        self._walking = False
        self._walk_timer.stop()
        self._hold_timer.stop()
        if self._wander_enabled:
            self._enter_idle()
        else:
            self._show_idle_animation()

    def _show_idle_animation(self):
        """站立显示：有 idle 循环素材则播放（按素材帧延迟），否则回静态立绘。"""
        self._walking = False
        self._walk_timer.stop()
        self._frame_timer.stop()
        self._actor.set_mirror(False)
        if self._idle_frames:
            self._idle_frame = 0
            self._actor.set_animation_frames(self._idle_frames)
            self._actor.set_frame_index(0)
            self._actor.set_breathing(False)   # 帧循环自带动感，不再叠呼吸缩放
            self._idle_timer.start(self._idle_delay_ms())
        else:
            self._idle_timer.stop()
            self._actor.set_animation_frames(None)
            self._actor.set_breathing(self._breathing)

    def _idle_delay_ms(self) -> int:
        """当前站立帧的停留时长：素材帧延迟优先，缺失回退默认。"""
        if self._idle_delays:
            return max(16, self._idle_delays[self._idle_frame % len(self._idle_delays)])
        return _IDLE_FRAME_MS

    def _idle_frame_tick(self):
        """站立循环：切下一帧，并按素材延迟排下一次（节奏不均匀时按帧停留）。"""
        if not self._idle_frames or self._walking:
            return
        n = len(self._idle_frames)
        self._idle_frame = (self._idle_frame + 1) % n
        self._actor.set_frame_index(self._idle_frame)
        self._idle_timer.start(self._idle_delay_ms())

    def _halt_wander(self):
        """临时冻结：停走与站立循环，回静态立绘（暂停监控/缩放模式用）。"""
        self._walking = False
        self._walk_timer.stop()
        self._frame_timer.stop()
        self._idle_timer.stop()
        self._hold_timer.stop()
        self._actor.set_animation_frames(None)
        self._actor.set_mirror(False)
        self._actor.set_breathing(self._breathing)

    def _resume_wander(self):
        """从交互/缩放/暂停恢复：走动开着 → 从站立随机；关着 → 播放站立循环。"""
        if self._wander_enabled:
            self._enter_idle()
        else:
            self._show_idle_animation()

    def _enter_idle(self, delay_ms: int = None):
        """进入站立：播放站立循环，delay 后自动转行走（默认随机时长）。"""
        self._walking = False
        self._frame_timer.stop()
        self._show_idle_animation()
        if delay_ms is None:
            delay_ms = random.randint(*_WANDER_IDLE_MS)
        self._hold_timer.start(max(1, delay_ms))

    def _interrupt_wander(self):
        """用户触摸打断：停走并进入较长的安静期（给用户操作留空间）。"""
        if self._wander_enabled:
            self._enter_idle(random.randint(*_WANDER_QUIET_MS))

    def _start_walking(self):
        """开始行走：随机方向、切走路动画，位移 40fps、动画按素材 10fps 各自驱动。"""
        if not self._walk_frames:
            self._enter_idle()
            return
        self._walking = True
        self._wander_dir = random.choice((-1, 1))
        self._wander_frame = 0
        self._idle_timer.stop()                 # 站立循环让位给行走动画
        self._actor.set_breathing(False)             # 走路时不做呼吸缩放
        self._actor.set_animation_frames(self._walk_frames, _WALK_VISUAL_SCALE)
        self._actor.set_frame_index(0)
        self._actor.set_mirror(self._wander_dir > 0)  # 素材默认朝左；向右走镜像
        self._walk_timer.start()
        self._frame_timer.start()
        self._hold_timer.start(random.randint(*_WANDER_WALK_MS))

    def _on_wander_hold(self):
        """站立/行走时长到点：状态轮转（站→走、走→站）。"""
        if self._walking:
            self._enter_idle()
        else:
            self._start_walking()

    def _wander_bounds(self):
        """可水平移动的范围：当前窗口所在屏幕的可用区域左右缘。"""
        screen = self.screen()
        if screen is None:
            app = QApplication.instance()
            screen = app.primaryScreen() if app else None
        if screen is None:
            return 0, 10000  # 退化：向右放开
        geo = screen.availableGeometry()
        return geo.left(), geo.right()

    def _wander_move_tick(self):
        """位置刷新（40fps）：沿当前方向平滑移动一小步，边缘掉头、镜像跟随。"""
        if not (self._wander_enabled and self._walking):
            return
        left, right = self._wander_bounds()
        x, self._wander_dir = wander_step_x(
            self.x(), self._wander_dir, _WALK_STEP_PX, left, right, self.width()
        )
        self._actor.set_mirror(self._wander_dir > 0)  # 掉头瞬间镜像翻转
        self.move(x, self.y())

    def _wander_frame_tick(self):
        """动画帧切换（100ms，素材节奏）：推进到下一帧，循环。"""
        if not (self._wander_enabled and self._walking):
            return
        n = len(self._walk_frames)
        self._wander_frame = (self._wander_frame + 1) % n
        self._actor.set_frame_index(self._wander_frame)
