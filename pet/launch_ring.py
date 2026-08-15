"""快捷环：点击桌宠弹出一圈快捷方式圆环。

8 个透明圆以桌宠为中心环绕排列。空槽位显示加号，点击加号选择 .lnk/.exe
填入；已有软件时点击即启动，右键清除槽位。点圆环空白处收起。
"""

import math
import os

from PySide6.QtCore import QEvent, QFileInfo, QObject, QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QRegion
from PySide6.QtWidgets import QApplication, QFileDialog, QFileIconProvider, QWidget

RING_COUNT = 8       # 槽位数
RING_R = 30          # 圆圈半径
RING_GAP = 10        # 圆圈与桌宠边缘间距
PAD = 6              # 窗口内边距

_FILL = QColor(255, 255, 255, 40)      # 圆填充：半透明白
_EDGE = QColor(255, 255, 255, 200)     # 圆描边
_PLUS = QColor(255, 255, 255, 230)     # 加号颜色


class _ClickCatcher(QObject):
    """应用级点击监听：圆环展开时，点击圆环窗口以外的空白 → 收起。

    圆环窗口本身有环形蒙版：点圆 → 圆环自己处理；点蒙版空洞（桌宠本体）→
    穿透给本体（本体的 toggle 收起）；点窗口外空白 → 这里统一收起。
    """

    def __init__(self, ring, parent=None):
        super().__init__(parent)
        self._ring = ring

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            ring = self._ring
            if ring.isVisible():
                pos = event.globalPosition().toPoint()
                rect = QRect(ring.pos(), ring.size())
                if not rect.contains(pos):
                    ring.hide()  # 点击圆环窗口外的空白 → 收起
        return False


class LaunchRing(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        slots = config.get("launch_slots", [None] * RING_COUNT)
        self._slots = list(slots) if isinstance(slots, list) else [None] * RING_COUNT
        if len(self._slots) < RING_COUNT:
            self._slots += [None] * (RING_COUNT - len(self._slots))
        self._centers: list[QPoint] = []
        self._icon_provider = QFileIconProvider()
        self._icon_cache: dict = {}
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # 全局空白点击收起（点窗口外空白）
        self._catcher = _ClickCatcher(self, self)
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self._catcher)
        self.hide()

    # ---- 布局 ----
    def layout_for(self, center_global: QPoint, pet_radius: int):
        """以桌宠中心为圆心布局 8 个圆；返回圆心列表（窗口局部坐标）。"""
        ring_radius = pet_radius + RING_GAP + RING_R
        size = 2 * (ring_radius + RING_R + PAD)
        self.resize(size, size)
        self.move(center_global.x() - size // 2, center_global.y() - size // 2)
        cx, cy = size / 2, size / 2
        self._centers = []
        for i in range(RING_COUNT):
            angle = math.radians(i * 360 / RING_COUNT - 90)
            self._centers.append(QPoint(round(cx + ring_radius * math.cos(angle)),
                                        round(cy + ring_radius * math.sin(angle))))
        self._update_mask()
        return self._centers

    def _update_mask(self):
        """环形蒙版：只有 8 个圆本身接收鼠标与绘制，中心空洞处点击穿透到下层
        （桌宠本体），这样点本体收起圆环才能生效。"""
        path = QPainterPath()
        for c in self._centers:
            path.addEllipse(c, RING_R, RING_R)
        region = QRegion()
        for poly in path.toFillPolygons():
            region = region.united(QRegion(poly.toPolygon()))
        self.setMask(region)

    def _hit_index(self, pos: QPoint):
        for i, c in enumerate(self._centers):
            dx = pos.x() - c.x()
            dy = pos.y() - c.y()
            if dx * dx + dy * dy <= RING_R * RING_R:
                return i
        return None

    # ---- 槽位操作 ----
    def _persist(self):
        self._config.set("launch_slots", self._slots)
        self._config.save()

    def _pick(self, index: int):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择软件", "", "快捷方式 / 程序 (*.lnk *.exe)"
        )
        if path:
            self._slots[index] = path
            self._persist()
            self.update()

    def _launch(self, index: int):
        path = self._slots[index]
        if path:
            try:
                os.startfile(path)  # Windows：.lnk 与 .exe 均支持
            except OSError:
                pass  # 目标不存在/被占用时静默，等待用户重新配置

    def _clear_slot(self, index: int):
        self._slots[index] = None
        self._persist()
        self.update()

    # ---- 图标 ----
    def _icon(self, path: str):
        if path not in self._icon_cache:
            self._icon_cache[path] = self._icon_provider.icon(QFileInfo(path))
        return self._icon_cache[path]

    # ---- 事件 ----
    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if event.button() == Qt.RightButton:
            index = self._hit_index(pos)
            if index is not None:
                self._clear_slot(index)
            return
        if event.button() != Qt.LeftButton:
            return
        index = self._hit_index(pos)
        if index is None:
            self.hide()  # 点圆环空白处 → 收起
            return
        if self._slots[index]:
            self._launch(index)
        else:
            self._pick(index)

    # ---- 绘制 ----
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        for i, c in enumerate(self._centers):
            painter.setBrush(_FILL)
            painter.setPen(QPen(_EDGE, 2))
            painter.drawEllipse(c, RING_R, RING_R)
            path = self._slots[i]
            if path:
                pixmap = self._icon(path).pixmap(36, 36)
                painter.drawPixmap(c.x() - 18, c.y() - 18, pixmap)
            else:
                painter.setPen(QPen(_PLUS, 4, Qt.SolidLine, Qt.RoundCap))
                painter.drawLine(c.x() - 12, c.y(), c.x() + 12, c.y())
                painter.drawLine(c.x(), c.y() - 12, c.x(), c.y() + 12)
