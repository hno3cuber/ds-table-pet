from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

_PANEL_STYLE = """
QWidget#HudPanel { background: rgba(20, 20, 30, 200); border-radius: 8px; }
QLabel { color: #ffffff; background: transparent; }
"""
_BASE_FONT_SIZE = 13.0


class HudPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HudPanel")
        self.setStyleSheet(_PANEL_STYLE)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        self._paused_label = QLabel("已暂停", self)
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
