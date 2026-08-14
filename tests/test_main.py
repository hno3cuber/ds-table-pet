from PySide6.QtGui import QPixmap
from pet.config import Config
from pet.window import PetWindow
import main


def test_main_loads_pixmap(qapp, tmp_path):
    pm = main.load_pixmap("picture/ds.png")
    assert not pm.isNull()


def test_build_window_from_config(qapp, tmp_path):
    cfg = Config(tmp_path / "config.json")
    pm = QPixmap(100, 200)
    pm.fill()
    w = main.build_window(pm, cfg)
    assert w is not None


def test_close_saves_position_and_scale(qapp, tmp_path):
    cfg = Config(tmp_path / "config.json")
    pm = QPixmap(100, 200)
    pm.fill()
    w = main.build_window(pm, cfg)
    w.move(321, 123)
    w._scale = 1.7
    main.save_state(w, cfg)
    cfg2 = Config(tmp_path / "config.json")
    assert cfg2.get("window.pos") == [321, 123]
    assert cfg2.get("window.scale") == 1.7


def test_install_plugins_passes_interval(qapp, tmp_path):
    import sys
    from pathlib import Path
    from pet.config import Config
    from PySide6.QtGui import QPixmap
    from pet.window import PetWindow
    from pet.plugins import PluginManager

    # 用临时假插件目录，避免依赖真实 system_monitor 初始化
    fake_dir = tmp_path / "plugins"
    fake_dir.mkdir()
    plugin_dir = fake_dir / "system_monitor"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.py").write_text(
        "from pet.plugin import Plugin\n"
        "class PluginClass(Plugin):\n"
        "    id = 'system_monitor'\n"
        "    name = 'x'\n"
        "    def __init__(self, interval_ms=1000): self.interval_ms = interval_ms\n"
        "    def start(self): pass\n"
        "    def stop(self): pass\n"
        "    def poll(self): return {}\n"
        "    def panel(self, parent): return None\n",
        encoding="utf-8",
    )
    cfg = Config(tmp_path / "config.json")
    cfg.set("refresh_interval_ms", 500)
    pm = QPixmap(100, 100)
    pm.fill()
    w = PetWindow(pm, cfg)

    def factory(plugin_class):
        if getattr(plugin_class, "id", None) == "system_monitor":
            return plugin_class(interval_ms=int(cfg.get("refresh_interval_ms", 1000)))
        return plugin_class()

    mgr = PluginManager(fake_dir, enabled=["system_monitor"], factory=factory)
    plugins = mgr.discover()
    assert plugins[0].interval_ms == 500


def test_install_plugins_discovers_real_monitor(qapp, tmp_path):
    """契约冲突回归测试：真实 plugins 目录能被 discover，interval_ms 从 config 透传。"""
    from PySide6.QtGui import QPixmap
    from pet.config import Config
    from pet.window import PetWindow
    pm = QPixmap(100, 100)
    pm.fill()
    cfg = Config(tmp_path / "config.json")
    cfg.set("refresh_interval_ms", 750)
    w = PetWindow(pm, cfg)
    mgr = main.install_plugins(w, cfg)
    try:
        assert len(mgr.instances) == 1
        assert mgr.instances[0].id == "system_monitor"
        assert mgr.instances[0].interval_ms == 750
        assert w._hud.layout().count() >= 2  # paused 标签 + 数据块
    finally:
        mgr.stop_all()  # 收尾停采集线程，避免测试进程残留
