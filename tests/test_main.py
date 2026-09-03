from PySide6.QtGui import QPixmap
from pet.config import Config
from pet.window import PetWindow
import main


def test_main_loads_pixmap(qapp, tmp_path):
    pm = main.load_pixmap(main.PIXMAP_PATH)
    assert not pm.isNull()


def test_load_pixmap_missing_raises(qapp, tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        main.load_pixmap(str(tmp_path / "不存在.png"))


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


def test_state_saver_is_qobject_and_filters(qapp, tmp_path):
    """回归：_StateSaver 必须继承 QObject，installEventFilter 才接受；
    真机曾报 TypeError（传了非 QObject 的过滤器）。"""
    from PySide6.QtCore import QObject

    cfg = Config(tmp_path / "config.json")
    pm = QPixmap(100, 200)
    pm.fill()
    w = main.build_window(pm, cfg)
    saver = main._StateSaver(w, cfg)
    assert isinstance(saver, QObject)
    w.installEventFilter(saver)  # 不抛 TypeError 即通过


def test_install_sigint_quit_registers_handler(qapp):
    """Ctrl+C 退出：install_sigint_quit 必须替换默认 SIGINT 处理器并返回保活 timer。"""
    import signal

    original = signal.getsignal(signal.SIGINT)
    try:
        wake = main.install_sigint_quit(qapp)
        handler = signal.getsignal(signal.SIGINT)
        assert handler is not signal.default_int_handler
        assert handler is not signal.SIG_DFL
        assert wake is not None
    finally:
        signal.signal(signal.SIGINT, original)


def test_load_default_pixmap(qapp):
    """默认形象 idel.png 能从 picture/ 加载且非空。"""
    pm = main.load_pixmap(main.PIXMAP_PATH)
    assert not pm.isNull()


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


def test_build_window_with_bad_config_values_does_not_raise(qapp, tmp_path):
    """验收第 7 条冒烟链：坏字段值构建 PetWindow 不抛异常，按默认值兜底。"""
    import json
    from PySide6.QtGui import QPixmap
    from pet.config import Config
    p = tmp_path / "config.json"
    p.write_text(json.dumps({
        "window": {"scale": "abc", "pos": "oops"},
        "refresh_interval_ms": -5,
        "enabled_plugins": None,
    }), encoding="utf-8")
    cfg = Config(p)
    pm = QPixmap(100, 200)
    pm.fill()
    w = main.build_window(pm, cfg)
    assert w.current_scale() == 1.0
    assert w.current_pos() == [100, 100]


def test_install_plugins_with_bad_config_values_does_not_raise(qapp, tmp_path):
    """验收第 7 条冒烟链：坏字段值 install_plugins 不抛异常，interval 兜底为默认。"""
    import json
    from PySide6.QtGui import QPixmap
    from pet.config import Config
    p = tmp_path / "config.json"
    p.write_text(json.dumps({
        "window": {"scale": "abc", "pos": "oops"},
        "refresh_interval_ms": -5,
        "enabled_plugins": None,
    }), encoding="utf-8")
    cfg = Config(p)
    pm = QPixmap(100, 100)
    pm.fill()
    w = main.build_window(pm, cfg)
    mgr = main.install_plugins(w, cfg)
    try:
        assert mgr.instances[0].id == "system_monitor"
        assert mgr.instances[0].interval_ms == 1000  # 兜底默认间隔
    finally:
        mgr.stop_all()
