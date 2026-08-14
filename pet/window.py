from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor, QPixmap
from PySide6.QtWidgets import QMenu, QVBoxLayout, QWidget

from pet.actor import ActorWidget
from pet.geometry import scale_from_drag, scaled_size
from pet.hud import HudPanel


class PetWindow(QWidget):
    def __init__(self, pixmap: QPixmap, config):
        super().__init__()
        self._pixmap = pixmap
        self._config = config
        self._scale = float(config.get("window.scale", 1.0))
        self._paused = False
        self._resize_mode = False
        self._drag_offset = None
        self._resize_corner = None
        self._resize_origin_global_x = 0
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

        self._hud = HudPanel(self)
        self._hud.set_scale(self._scale)

        w, h = scaled_size(pixmap.width(), pixmap.height(), self._scale)
        self.resize(w, h)
        pos = self._config.get("window.pos", [100, 100])
        self.move(pos[0], pos[1])

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
        self._scale = scale_from_drag(self._pixmap.width(), drag_dx, self._scale)
        self._actor.set_scale(self._scale)
        w, h = scaled_size(self._pixmap.width(), self._pixmap.height(), self._scale)
        self.resize(w, h)
        self._hud.set_scale(self._scale)

    def _finish_resize(self):
        self._resize_corner = None
        self._config.set("window.scale", self._scale)
        self._config.save()

    def _exit_resize_mode(self):
        self._resize_mode = False
        self._resize_corner = None
        self._actor.set_resize_mode(False)
        self.unsetCursor()

    # ---- 鼠标事件 ----
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._show_menu(event.globalPos())
            return
        if event.button() != Qt.LeftButton:
            return
        local = event.position().toPoint()
        if self._resize_mode:
            corner = self._actor.handle_at(local)
            if corner is not None:
                self._begin_resize(corner)
                # 记录按下瞬间光标全局 X，作为本次缩放拖拽的增量基准
                self._resize_origin_global_x = event.globalPosition().toPoint().x()
                self._drag_offset = None
                return
        self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        self._resize_corner = None

    def mouseMoveEvent(self, event):
        if self._resize_corner is not None:
            drag_dx = event.globalPosition().toPoint().x() - self._resize_origin_global_x
            self._apply_resize(drag_dx)
            return
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if self._resize_corner is not None:
            self._finish_resize()
        self._drag_offset = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self._resize_mode:
            self._exit_resize_mode()
        else:
            super().keyPressEvent(event)

    def enterEvent(self, event):
        self._hud.fade_in()
        self._position_hud()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hud.fade_out()
        super().leaveEvent(event)

    def _position_hud(self):
        self._hud.adjustSize()
        x = self.width() + 6
        y = 0
        self._hud.move(x, y)

    def resizeEvent(self, event):
        self._position_hud()
        super().resizeEvent(event)

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
