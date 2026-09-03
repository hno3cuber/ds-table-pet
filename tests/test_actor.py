from PySide6.QtGui import QPixmap
from PySide6.QtCore import QPoint
from pet.actor import ActorWidget


def test_actor_creates(qapp):
    pm = QPixmap(200, 300)
    pm.fill()
    actor = ActorWidget(pm, scale=1.0)
    assert actor.current_scale() == 1.0


def test_handle_hit_outside_resize_mode(qapp):
    pm = QPixmap(200, 300)
    pm.fill()
    actor = ActorWidget(pm)
    assert actor.handle_at(QPoint(5, 5)) is None


def test_handle_hit_corners_in_resize_mode(qapp):
    pm = QPixmap(200, 300)
    pm.fill()
    actor = ActorWidget(pm)
    actor.set_resize_mode(True)
    assert actor.handle_at(QPoint(2, 2)) == 0          # 左上
    assert actor.handle_at(QPoint(197, 2)) == 1        # 右上
    assert actor.handle_at(QPoint(2, 297)) == 2        # 左下
    assert actor.handle_at(QPoint(197, 297)) == 3      # 右下
    assert actor.handle_at(QPoint(100, 100)) is None   # 中间不是手柄


def test_scale_change_repaints(qapp):
    pm = QPixmap(200, 300)
    pm.fill()
    actor = ActorWidget(pm, scale=1.0)
    actor.set_scale(2.0)
    assert actor.current_scale() == 2.0
    assert actor.sizeHint().width() == 400


def test_breathing_toggle(qapp):
    pm = QPixmap(200, 300)
    pm.fill()
    actor = ActorWidget(pm)
    actor.set_breathing(False)
    assert actor._breath == 0.0
    assert not actor._breath_anim.state() == actor._breath_anim.State.Running
    actor.set_breathing(True)
    assert actor._breath_anim.state() == actor._breath_anim.State.Running


def test_breath_property_registered_and_driven(qapp):
    """回归：breath 必须注册到 Qt 元对象系统，动画才能驱动它（真机曾报
    QPropertyAnimation: non-existing property breath）。"""
    from PySide6.QtTest import QTest

    pm = QPixmap(200, 300)
    pm.fill()
    actor = ActorWidget(pm)
    # 元对象系统里能找到 breath 属性
    assert actor.metaObject().indexOfProperty("breath") >= 0
    # 动画跑一段时间后，breath 值确实被驱动（非初始 0.0）
    actor.set_breath(0.0)
    actor.set_breathing(True)
    QTest.qWait(120)
    assert actor._breath != 0.0


# ---- 行走动画：帧序列 + 镜像 ----

def _make_frames(n=2, w=100, h=100):
    frames = []
    for i in range(n):
        pm = QPixmap(w, h)
        pm.fill()
        frames.append(pm)
    return frames


def test_set_animation_frames_switches_mode(qapp):
    pm = QPixmap(100, 100)
    pm.fill()
    actor = ActorWidget(pm)
    assert actor._frames is None
    frames = _make_frames()
    actor.set_animation_frames(frames)
    assert actor._frames == frames   # 内部拷贝存储，内容一致即可
    assert actor._frame_index == 0


def test_set_animation_frames_none_returns_to_static(qapp):
    pm = QPixmap(100, 100)
    pm.fill()
    actor = ActorWidget(pm)
    actor.set_animation_frames(_make_frames())
    actor.set_animation_frames(None)
    assert actor._frames is None


def test_frame_index_wraps_around(qapp):
    pm = QPixmap(100, 100)
    pm.fill()
    actor = ActorWidget(pm)
    actor.set_animation_frames(_make_frames(2))
    actor.set_frame_index(0)
    assert actor._frame_index == 0
    actor.set_frame_index(1)
    assert actor._frame_index == 1
    actor.set_frame_index(5)  # 2 帧循环：5 % 2 == 1
    assert actor._frame_index == 1


def test_frame_index_ignored_in_static_mode(qapp):
    pm = QPixmap(100, 100)
    pm.fill()
    actor = ActorWidget(pm)
    actor.set_frame_index(3)  # 静态模式不崩、不进入动画模式
    assert actor._frames is None


def test_mirror_flag(qapp):
    pm = QPixmap(100, 100)
    pm.fill()
    actor = ActorWidget(pm)
    assert actor._mirror is False
    actor.set_mirror(True)
    assert actor._mirror is True
    actor.set_mirror(False)
    assert actor._mirror is False


def test_mirror_flips_rendered_pixels(qapp):
    """镜像 = 水平翻转像素：左白右黑的画面翻成左黑右白。"""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QImage, QPainter

    img = QImage(100, 100, QImage.Format_ARGB32)
    img.fill(Qt.white)
    p = QPainter(img)
    p.fillRect(50, 0, 50, 100, Qt.black)
    p.end()
    pm = QPixmap.fromImage(img)
    frames = [pm]

    actor = ActorWidget(pm, scale=1.0)
    actor.resize(100, 100)
    actor.set_animation_frames(frames)
    actor.show()

    # 未镜像：左白右黑
    left = actor.grab().toImage().pixelColor(25, 50)
    right = actor.grab().toImage().pixelColor(75, 50)
    assert left.red() > 200 and right.red() < 50

    # 镜像：水平翻转 → 左黑右白
    actor.set_mirror(True)
    left = actor.grab().toImage().pixelColor(25, 50)
    right = actor.grab().toImage().pixelColor(75, 50)
    assert left.red() < 50 and right.red() > 200


def test_animation_content_scale_shrinks_character(qapp):
    """content_scale 把适配后的角色等比缩小并保持贴底（对齐站立立绘视觉大小）。"""
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtCore import Qt

    img = QImage(50, 100, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.fillRect(0, 0, 50, 100, QColor(200, 30, 30))
    p.end()
    frame = QPixmap.fromImage(img)

    actor = ActorWidget(frame, scale=1.0)
    actor.resize(100, 100)
    actor.set_animation_frames([frame], content_scale=0.5)
    actor.show()

    assert actor._content_scale == 0.5
    img = actor.grab().toImage()
    # 原适配矩形 25x50 高 100 贴底；×0.5 → 25 宽 50 高，y∈[50,100]
    assert img.pixelColor(50, 30).green() > 150   # 内容顶以上是背景
    assert img.pixelColor(50, 75).red() > 150     # 贴底部分有内容
    assert img.pixelColor(50, 99).red() > 150


def test_animation_frame_bottom_anchored_keeps_aspect(qapp):
    """动画帧按宽高比适配到 widget 内、贴底居中（不等比变形、不悬浮）。
    offscreen grab 输出 RGB32（无 alpha），透明区合成为黑，用 RGB 判断。"""
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtCore import Qt

    # 源图 50x100（竖长条）；widget 被用户拉成 100x100 方形
    img = QImage(50, 100, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.fillRect(0, 0, 50, 100, QColor(200, 30, 30))
    p.end()
    frame = QPixmap.fromImage(img)

    actor = ActorWidget(frame, scale=1.0)  # 初始 50x100
    actor.resize(100, 100)                 # 模拟用户把窗口拉成方形
    actor.set_animation_frames([frame])
    actor.show()

    img = actor.grab().toImage()
    # 适配后宽=50（50/100 取 min），高=100，贴底：x∈[25,75]，y∈[0,100]
    # offscreen 透明区合成为浅灰(239)，内容为 (200,30,30)，用 green 通道区分
    assert img.pixelColor(50, 5).red() > 150     # 顶部中央有内容（高拉满到顶）
    assert img.pixelColor(15, 50).green() > 150 # 水平两侧是背景（保持宽高比不变形）
    assert img.pixelColor(5, 99).green() > 150  # 底角是背景
    assert img.pixelColor(50, 99).red() > 150   # 贴底：底部中央有内容
