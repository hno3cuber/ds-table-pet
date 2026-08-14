from PySide6.QtCore import QPoint, QPropertyAnimation, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from pet.geometry import scaled_size

_HANDLE = 8          # 手柄绘制尺寸
_HIT = 12            # 手柄命中区域
_BREATH_MAX = 0.02   # 呼吸幅度 ±2%


class ActorWidget(QWidget):
    def __init__(self, pixmap: QPixmap, scale: float = 1.0, parent=None):
        super().__init__(parent)
        self._pixmap = pixmap
        self._scale = scale
        self.resize(*scaled_size(pixmap.width(), pixmap.height(), scale))
        self._resize_mode = False
        self._breath = 0.0
        self._breath_anim = QPropertyAnimation(self, b"breath", self)
        self._breath_anim.setDuration(3000)
        self._breath_anim.setStartValue(0.0)
        self._breath_anim.setKeyValueAt(0.5, 1.0)
        self._breath_anim.setEndValue(0.0)
        self._breath_anim.setLoopCount(-1)
        self._breath_anim.start()
        self.set_resize_mode(False)

    def get_breath(self) -> float:
        return self._breath

    def set_breath(self, value: float):
        self._breath = value
        self.update()

    breath = property(get_breath, set_breath)

    def current_scale(self) -> float:
        return self._scale

    def set_scale(self, scale: float):
        self._scale = scale
        self.update()

    def set_breathing(self, enabled: bool):
        if enabled:
            self._breath_anim.start()
        else:
            self._breath_anim.stop()
            self._breath = 0.0
            self.update()

    def set_resize_mode(self, on: bool):
        self._resize_mode = on
        self.setMouseTracking(on)
        self.update()

    def sizeHint(self):
        w, h = scaled_size(self._pixmap.width(), self._pixmap.height(), self._scale)
        return QSize(w, h)

    def _corner_positions(self):
        w = self.width()
        h = self.height()
        return [QPoint(0, 0), QPoint(w - _HANDLE, 0), QPoint(0, h - _HANDLE), QPoint(w - _HANDLE, h - _HANDLE)]

    def handle_at(self, pos: QPoint):
        if not self._resize_mode:
            return None
        for idx, origin in enumerate(self._corner_positions()):
            rect = QRect(origin, origin + QPoint(_HANDLE, _HANDLE)).adjusted(
                -(_HIT - _HANDLE) // 2, -(_HIT - _HANDLE) // 2,
                (_HIT - _HANDLE) // 2, (_HIT - _HANDLE) // 2,
            )
            if rect.contains(pos):
                return idx
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.Antialiasing, True)
        breath_factor = 1.0 + (self._breath - 0.5) * 2 * _BREATH_MAX
        target = self.rect().size()
        scaled = QPixmap(self._pixmap.size())
        scaled.fill(Qt.transparent)
        sp = QPainter(scaled)
        sp.setRenderHint(QPainter.SmoothPixmapTransform, True)
        sp.scale(breath_factor, breath_factor)
        sp.drawPixmap(0, 0, self._pixmap)
        sp.end()
        painter.drawPixmap(self.rect(), scaled, scaled.rect())
        if self._resize_mode:
            pen = QPen(QColor(255, 255, 255, 220), 2)
            painter.setPen(pen)
            painter.drawRect(QRect(1, 1, self.width() - 2, self.height() - 2))
            painter.setBrush(QColor(255, 255, 255))
            painter.setPen(Qt.NoPen)
            for origin in self._corner_positions():
                painter.drawRect(QRect(origin, origin + QPoint(_HANDLE, _HANDLE)))
