from PySide6.QtCore import Property, QPoint, QPropertyAnimation, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from pet.geometry import scaled_size

_HANDLE = 8          # 手柄绘制尺寸
_HIT = 12            # 手柄命中区域
_BREATH_MAX = 0.02   # 呼吸幅度 ±2%

# 举牌姿态（token.png）中牌子文字的书写区：相对图片尺寸的归一化矩形。
# 由 token.png（1728x2432）实测：牌面 x 512..1203 / y 1115..1483，
# 内缩避开圆角与手指压痕，取保守安全区。
_SIGN_TEXT_L = 0.305
_SIGN_TEXT_R = 0.690
_SIGN_TEXT_T = 0.487
_SIGN_TEXT_B = 0.576
_SIGN_TEXT_COLOR = QColor(43, 62, 92)   # 深墨蓝：白底清晰且贴合冷色角色
_SIGN_MAX_FONT_PX = 90                  # 牌面字号上限（原图像素）
_SIGN_MIN_FONT_PX = 16


class ActorWidget(QWidget):
    def __init__(self, pixmap: QPixmap, scale: float = 1.0, parent=None):
        super().__init__(parent)
        self._pixmap = pixmap
        self._scale = scale
        self.resize(*scaled_size(pixmap.width(), pixmap.height(), scale))
        self._resize_mode = False
        self._breath = 0.0
        self._frames = None       # 行走动画帧序列；None = 静态立绘模式
        self._frame_index = 0
        self._mirror = False      # 朝右走时水平翻转（walk.gif 素材默认朝左）
        self._content_scale = 1.0  # 动画帧相对静态立绘的视觉大小修正（素材角色占比差异）
        self._pose = None         # 举牌姿态图（如 token.png）；非空时优先于动画/静态立绘
        self._sign_text = ""      # 姿态图上牌子里的文字
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

    # 必须用 PySide6 的 Property 注册到 Qt 元对象系统，QPropertyAnimation 才能驱动 breath
    breath = Property(float, get_breath, set_breath)

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

    def set_animation_frames(self, frames, content_scale: float = 1.0):
        """切换到行走动画模式（帧序列），从第 0 帧开始。

        content_scale 对适配后的帧再做等比缩放：不同素材画布里角色占比
        不同（站立留白多、行走画得满），用它把行走角色对齐到站立立绘的
        视觉大小。传 None 或空列表回到静态立绘模式。"""
        self._frames = list(frames) if frames else None
        self._frame_index = 0
        self._content_scale = content_scale if self._frames else 1.0
        self.update()

    def set_frame_index(self, index: int):
        """跳到第 index 帧（自动取模循环）。静态模式忽略。"""
        if self._frames:
            self._frame_index = index % len(self._frames)
            self.update()

    def set_mirror(self, on: bool):
        """水平翻转画面（素材默认朝左，朝右走时镜像）。"""
        if on != self._mirror:
            self._mirror = on
            self.update()

    def set_pose(self, pixmap, text: str = ""):
        """切换到举牌姿态：pixmap 非空时用它替代立绘/动画，并把 text 画在牌子区域。

        传 None 退出姿态，回到原来的动画/静态立绘绘制路径。"""
        self._pose = pixmap
        self._sign_text = text or ""
        self.update()

    def set_sign_text(self, text: str):
        """只更新牌面文字（姿态未激活时忽略）。"""
        if self._pose is not None:
            self._sign_text = text or ""
            self.update()

    def _content_rect(self, src_w: int, src_h: int):
        """动画帧的适配矩形：保持源宽高比放进 widget、贴底水平居中。

        站立立绘（864x1222）与行走画布（720x960）比例不同，整幅拉伸会变形；
        贴底对齐保证切换瞬间脚底高度一致，角色不悬空、不穿地。
        """
        tw, th = self.width(), self.height()
        if tw <= 0 or th <= 0 or src_w <= 0 or src_h <= 0:
            return QRect(0, 0, tw, th)
        scale = min(tw / src_w, th / src_h)
        w = max(1, round(src_w * scale))
        h = max(1, round(src_h * scale))
        # 素材角色占比修正：等比缩小到 content_scale，仍贴底居中（脚不悬空）
        w = max(1, round(w * self._content_scale))
        h = max(1, round(h * self._content_scale))
        return QRect((tw - w) // 2, th - h, w, h)

    def _paint_animation_frame(self, painter: QPainter):
        frame = self._frames[self._frame_index % len(self._frames)]
        rect = self._content_rect(frame.width(), frame.height())
        painter.save()
        if self._mirror:
            # 原点移到目标矩形右缘后水平反向：x 从右往左填充 = 镜像
            painter.translate(rect.left() + rect.width(), rect.top())
            painter.scale(-1.0, 1.0)
            painter.drawPixmap(0, 0, rect.width(), rect.height(), frame)
        else:
            painter.drawPixmap(rect, frame, QRect(frame.rect()))
        painter.restore()

    def _paint_pose(self, painter: QPainter):
        """绘制举牌姿态：整幅姿态图贴底居中适配，再把文字写入牌子区域。"""
        pose = self._pose
        rect = self._content_rect(pose.width(), pose.height())
        painter.drawPixmap(rect, pose, QRect(pose.rect()))
        if not self._sign_text:
            return
        sign = QRect(
            rect.left() + round(rect.width() * _SIGN_TEXT_L),
            rect.top() + round(rect.height() * _SIGN_TEXT_T),
            round(rect.width() * (_SIGN_TEXT_R - _SIGN_TEXT_L)),
            round(rect.height() * (_SIGN_TEXT_B - _SIGN_TEXT_T)),
        )
        self._draw_sign_text(painter, sign, self._sign_text)

    def _draw_sign_text(self, painter: QPainter, rect: QRect, text: str):
        """在牌子区域内绘制文字：多行居中，字号自适应到不溢出不超上限。"""
        lines = text.split("\n")
        size = min(_SIGN_MAX_FONT_PX,
                   max(_SIGN_MIN_FONT_PX, int(rect.height() / max(1, len(lines)) * 0.6)))
        while size > _SIGN_MIN_FONT_PX:
            font = QFont()
            font.setPixelSize(size)
            font.setBold(True)
            metrics = QFontMetricsF(font)
            widest = max(metrics.horizontalAdvance(line) for line in lines)
            total_h = metrics.height() * len(lines)
            if widest <= rect.width() * 0.92 and total_h <= rect.height() * 1.05:
                break
            size -= 2
        font = QFont()
        font.setPixelSize(size)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(_SIGN_TEXT_COLOR)
        painter.drawText(rect, Qt.AlignCenter | Qt.TextWordWrap, text)

    def _paint_static(self, painter: QPainter):
        breath_factor = 1.0 + (self._breath - 0.5) * 2 * _BREATH_MAX
        scaled = QPixmap(self._pixmap.size())
        scaled.fill(Qt.transparent)
        sp = QPainter(scaled)
        sp.setRenderHint(QPainter.SmoothPixmapTransform, True)
        sp.scale(breath_factor, breath_factor)
        sp.drawPixmap(0, 0, self._pixmap)
        sp.end()
        painter.drawPixmap(self.rect(), scaled, scaled.rect())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self._pose is not None:
            self._paint_pose(painter)
        elif self._frames:
            self._paint_animation_frame(painter)
        else:
            self._paint_static(painter)
        if self._resize_mode:
            pen = QPen(QColor(255, 255, 255, 220), 2)
            painter.setPen(pen)
            painter.drawRect(QRect(1, 1, self.width() - 2, self.height() - 2))
            painter.setBrush(QColor(255, 255, 255))
            painter.setPen(Qt.NoPen)
            for origin in self._corner_positions():
                painter.drawRect(QRect(origin, origin + QPoint(_HANDLE, _HANDLE)))
