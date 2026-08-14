from PySide6.QtGui import QPixmap
from pet.config import Config
from pet.window import PetWindow


def test_window_creates_with_scale(qapp, tmp_path):
    pm = QPixmap(200, 300)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    cfg.set("window.scale", 2.0)
    w = PetWindow(pm, cfg)
    assert w.current_scale() == 2.0
    assert w.width() == 400
    assert w.height() == 600


def test_window_min_scale_after_resize_drag(qapp, tmp_path):
    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    w = PetWindow(pm, cfg)
    w._enter_resize_mode()
    w._begin_resize(3)  # 按下右下角手柄
    w._apply_resize(-200)  # 向左拖 200px（相对原图 100，触发最小钳制）
    assert w.current_scale() >= 0.3


def test_breathing_follows_config(qapp, tmp_path):
    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    cfg.set("breathing_animation", False)
    w = PetWindow(pm, cfg)
    assert w._actor._breath_anim.state() != w._actor._breath_anim.State.Running


def test_install_plugin_adds_block(qapp, tmp_path):
    from PySide6.QtWidgets import QLabel
    from pet.plugin import Plugin
    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")

    class Fake(Plugin):
        id = "fake"
        name = "假"
        def start(self): pass
        def stop(self): pass
        def poll(self): return {}
        def panel(self, parent): return QLabel("X", parent)

    w = PetWindow(pm, cfg)
    w.install_plugin(Fake())
    assert w._hud.layout().count() >= 1


def test_toggle_pause(qapp, tmp_path):
    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, Config(tmp_path / "config.json"))
    w.set_paused(True)
    assert w._paused is True
    w.set_paused(False)
    assert w._paused is False
