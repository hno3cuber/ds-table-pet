from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QVBoxLayout, QWidget

from pet.actor import ActorWidget
from pet.geometry import (
    anchor_and_topleft,
    corner_resize_size,
    scale_from_corner_drag,
    scaled_size,
    scaled_size_xy,
)
from pet.hud import HudPanel
from pet.launch_ring import LaunchRing

_CLICK_THRESHOLD = 6     # press 与 release 位移小于该值视为「点击」（弹出快捷环）
_MIN_SCALE = 0.1          # 单方向最小缩放系数


class PetWindow(QWidget):
    def __init__(self, pixmap: QPixmap, config, poses=None):
        super().__init__()
        self._pixmap = pixmap
        self._config = config
        self._press_global = None
        self._launch_ring = LaunchRing(config)
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

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._actor = ActorWidget(pixmap, self._scale_y)
        self._actor.set_breathing(bool(config.get("breathing_animation", True)))
        layout.addWidget(self._actor)

        self._hud = HudPanel()
        self._hud.set_scale(self._scale_y)
        self._hud.fade_in()  # 常驻显示：启动即浮现监测面板，不再依赖鼠标悬停

        w, h = scaled_size_xy(pixmap.width(), pixmap.height(), self._scale_x, self._scale_y)
        self.resize(w, h)
        pos = self._config.get("window.pos", [100, 100])
        self.move(pos[0], pos[1])

    # ---- 查询 ----
    def current_scale(self) -> float:
        """纵向缩放系数（自由宽高比时以高度为主观感尺度）。"""
        return self._scale_y

    def current_scales(self) -> tuple[float, float]:
        return (self._scale_x, self._scale_y)

    def current_pos(self):
        p = self.pos()
        return [p.x(), p.y()]

    def install_plugin(self, plugin):
        self._plugins.append(plugin)
        self._hud.add_block(plugin.panel(self._hud))

    def set_paused(self, paused: bool):
        self._paused = paused
        for plugin in self._plugins:
            plugin.set_paused(paused)
        self._hud.show_paused(paused)

    # ---- 缩放（PPT 式角点拖拽：对角固定，宽高自由，Shift 锁等比） ----
    def _enter_resize_mode(self):
        """进入缩放模式：显示选框与手柄，等待用户按角点。"""
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
        action_resize = menu.addAction("调整大小")
        menu.addSeparator()
        action_quit = menu.addAction("退出")
        chosen = menu.exec(global_pos)
        if chosen is action_pause:
            self.set_paused(not self._paused)
        elif chosen is action_resize:
            if self._resize_mode:
                self._exit_resize_mode()
            else:
                self._enter_resize_mode()
        elif chosen is action_quit:
            self._quit()

    def _quit(self):
        """退出：窗口全是 Qt.Tool 类型（不触发 quitOnLastWindowClosed），
        必须显式 quit 才会结束事件循环并销毁所有窗口（含 HUD 与快捷环）。"""
        self.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()
