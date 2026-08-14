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
