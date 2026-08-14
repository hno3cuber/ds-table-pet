from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

_PANEL_STYLE = """
QWidget#HudPanel { background: rgba(235, 235, 235, 220); border-radius: 8px; }
QLabel { color: #1a1a1a; background: transparent; }
"""
_BASE_FONT_SIZE = 13.0

# 8 方向描边位移
_OUTLINE_DIRS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


class OutlinedLabel(QLabel):
    """带描边的文本标签：先 8 方向画描边色，再原位画填充色，任何背景下都清晰。"""

    def __init__(self, text="", parent=None, outline=None, fill=None):
        super().__init__(text, parent)
        self.outline = outline or QColor(255, 255, 255, 210)
        self.fill = fill or QColor(26, 26, 26)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setFont(self.font())
        rect = self.rect()
        align = self.alignment()
        for dx, dy in _OUTLINE_DIRS:
            painter.setPen(QPen(self.outline, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawText(rect.translated(dx, dy), align, self.text())
        painter.setPen(QPen(self.fill, 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawText(rect, align, self.text())


class HudPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HudPanel")
        # 独立顶层窗口：child widget 绘制会被裁剪到父窗口矩形内，无法画到窗外；
        # 且 windowOpacity 只对顶层窗口有效。因此 HUD 必须自持窗口。
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(_PANEL_STYLE)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        self._paused_label = OutlinedLabel("已暂停", self)
        self._paused_label.setAlignment(self._paused_label.alignment().AlignCenter)
        layout.addWidget(self._paused_label)
        self._paused_label.hide()
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(150)
        self._fade.setEasingCurve(QEasingCurve.InOutQuad)
        self._fade.finished.connect(lambda: self.hide() if self.windowOpacity() <= 0.01 else None)
        self.hide()

    def add_block(self, widget: QWidget):
        widget.setParent(self)
        self.layout().insertWidget(self.layout().count() - 1, widget)

    def show_paused(self, paused: bool):
        self._paused_label.setVisible(paused)
        for i in range(self.layout().count() - 1):
            item = self.layout().itemAt(i)
            if item.widget() is not None:
                item.widget().setVisible(not paused)

    def set_scale(self, scale: float):
        size = max(9.0, _BASE_FONT_SIZE * scale)
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            widget = item.widget()
            if widget is not None:
                font = widget.font()
                font.setPointSizeF(size)
                widget.setFont(font)

    def fade_in(self):
        self.show()
        self._fade.stop()
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(1.0)
        self._fade.start()

    def fade_out(self):
        self._fade.stop()
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        self._fade.start()
