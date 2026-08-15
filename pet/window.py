from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMenu, QVBoxLayout, QWidget

from pet.actor import ActorWidget
from pet.geometry import scale_from_drag, scaled_size
from pet.hud import HudPanel
from pet.launch_ring import LaunchRing

_POSE_THRESHOLD = 8      # 拖拽超过该像素才切换姿势，防手抖
_CLICK_THRESHOLD = 6     # press 与 release 位移小于该值视为「点击」（弹出快捷环）


class PetWindow(QWidget):
    def __init__(self, pixmap: QPixmap, config, poses=None):
        super().__init__()
        self._pixmap = pixmap
        self._config = config
        # 姿势图集：normal/up/down；未提供时全部回退到默认图（保持既有调用兼容）
        self._poses = poses if poses else {"normal": pixmap, "up": pixmap, "down": pixmap}
        self._pose = "normal"
        self._drag_start_global = None
        self._press_global = None
        self._launch_ring = LaunchRing(config)
        self._scale = max(0.3, float(config.get("window.scale", 1.0)))
        self._paused = False
        self._resize_mode = False
        self._drag_offset = None
        self._resize_corner = None
        self._resize_origin_global_x = 0
        self._resize_start_scale = 0.0
        self._plugins = []

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._actor = ActorWidget(pixmap, self._scale)
        self._actor.set_breathing(bool(config.get("breathing_animation", True)))
        layout.addWidget(self._actor)

        self._hud = HudPanel()
        self._hud.set_scale(self._scale)
        self._hud.fade_in()  # 常驻显示：启动即浮现监测面板，不再依赖鼠标悬停

        w, h = scaled_size(pixmap.width(), pixmap.height(), self._scale)
        self.resize(w, h)
        pos = self._config.get("window.pos", [100, 100])
        self.move(pos[0], pos[1])

    # ---- 姿势切换（拖拽方向联动） ----
    def _set_pose(self, name: str):
        if self._pose == name:
            return
        self._pose = name
        pixmap = self._poses.get(name) or self._poses["normal"]
        self._actor.set_pixmap(pixmap)

    def _update_pose(self, global_pos: QPoint):
        """按全局位移判定方向：上拖过阈值 → up，下拖过阈值 → down，否则 normal。"""
        if self._drag_start_global is None:
            return
        dy = global_pos.y() - self._drag_start_global.y()
        if dy < -_POSE_THRESHOLD:
            self._set_pose("up")
        elif dy > _POSE_THRESHOLD:
            self._set_pose("down")
        else:
            self._set_pose("normal")

    # ---- 查询 ----
    def current_scale(self) -> float:
        return self._scale

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

    # ---- 缩放 ----
    def _enter_resize_mode(self):
        """进入缩放模式：显示选框与手柄，等待用户按角点。"""
        self._resize_mode = True
        self._actor.set_resize_mode(True)

    def _begin_resize(self, corner: int):
        """用户按住了某个角点手柄，开始一次拖拽。"""
        self._resize_corner = corner

    def _apply_resize(self, drag_dx: int):
        # 以 press 瞬间的 scale 为基准：drag_dx 是相对起点的总位移，绝对语义幂等
        self._scale = scale_from_drag(self._pixmap.width(), drag_dx, self._resize_start_scale)
        self._actor.set_scale(self._scale)
        w, h = scaled_size(self._pixmap.width(), self._pixmap.height(), self._scale)
        self.resize(w, h)
        self._hud.set_scale(self._scale)

    def _finish_resize(self):
        self._resize_corner = None
        self._resize_start_scale = 0.0
        self._config.set("window.scale", self._scale)
        self._config.save()

    def _exit_resize_mode(self):
        self._resize_mode = False
        self._resize_corner = None
        self._resize_start_scale = 0.0
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
                self._begin_resize(corner)
                # 记录按下瞬间光标全局 X 与起始 scale，作为本次缩放拖拽的基准
                self._resize_origin_global_x = event.globalPosition().toPoint().x()
                self._resize_start_scale = self._scale
                self._drag_offset = None
                return
        self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        self._drag_start_global = event.globalPosition().toPoint()
        self._press_global = event.globalPosition().toPoint()
        self._resize_corner = None

    def mouseMoveEvent(self, event):
        if self._resize_corner is not None:
            drag_dx = event.globalPosition().toPoint().x() - self._resize_origin_global_x
            self._apply_resize(drag_dx)
            return
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            self._update_pose(event.globalPosition().toPoint())

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
        self._drag_start_global = None
        self._set_pose("normal")  # 松开恢复默认形象

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self._resize_mode:
            self._exit_resize_mode()
        else:
            super().keyPressEvent(event)

    def _position_hud(self):
        self._hud.adjustSize()
        # HUD 是独立顶层窗口，用全局坐标同步到主窗口右缘（轻微重叠，贴着角色）
        self._hud.move(self.mapToGlobal(QPoint(self.width() - 24, 0)))

    def resizeEvent(self, event):
        self._position_hud()
        super().resizeEvent(event)

    def moveEvent(self, event):
        self._position_hud()
        # 圆环展开时跟随本体移动（相对位置不变）
        if self._launch_ring.isVisible():
            center = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
            pet_radius = max(self.width(), self.height()) // 2
            self._launch_ring.layout_for(center, pet_radius)
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
            self.close()
