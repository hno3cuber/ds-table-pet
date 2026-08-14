import sys
from pathlib import Path
import pytest
from pet.plugin import Plugin
from pet.plugins import PluginManager

FAKE_PLUGIN_SRC = '''
from pet.plugin import Plugin

class PluginClass(Plugin):
    id = "fake_monitor"
    name = "假插件"

    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def poll(self):
        return {"value": 1}

    def panel(self, parent):
        return None
'''


def _make_fake_plugin(tmp_path: Path, plugin_id: str) -> Path:
    plugin_dir = tmp_path / plugin_id
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.py").write_text(
        FAKE_PLUGIN_SRC.replace("fake_monitor", plugin_id), encoding="utf-8"
    )
    return tmp_path


def test_discover_loads_all(tmp_path):
    d = _make_fake_plugin(tmp_path, "fake_one")
    _make_fake_plugin(tmp_path, "fake_two")
    mgr = PluginManager(d, enabled=None)
    plugins = mgr.discover()
    assert {p.id for p in plugins} == {"fake_one", "fake_two"}


def test_enabled_filter(tmp_path):
    d = _make_fake_plugin(tmp_path, "fake_one")
    _make_fake_plugin(tmp_path, "fake_two")
    mgr = PluginManager(d, enabled=["fake_two"])
    plugins = mgr.discover()
    assert [p.id for p in plugins] == ["fake_two"]


def test_skips_non_plugin_module(tmp_path):
    d = _make_fake_plugin(tmp_path, "fake_one")
    bad = d / "bad_plugin"
    bad.mkdir()
    (bad / "plugin.py").write_text("x = 1\n", encoding="utf-8")
    mgr = PluginManager(d, enabled=None)
    assert [p.id for p in mgr.discover()] == ["fake_one"]


def test_skips_plugin_class_not_subclass(tmp_path):
    """PluginClass 存在但不是 Plugin 子类（如普通 class PluginClass: pass）被跳过。"""
    d = _make_fake_plugin(tmp_path, "fake_one")
    bad = d / "bad_plugin"
    bad.mkdir()
    (bad / "plugin.py").write_text("class PluginClass:\n    pass\n", encoding="utf-8")
    mgr = PluginManager(d, enabled=None)
    assert [p.id for p in mgr.discover()] == ["fake_one"]


def test_start_all_calls_each(tmp_path):
    d = _make_fake_plugin(tmp_path, "fake_one")
    mgr = PluginManager(d, enabled=None)
    plugins = mgr.discover()
    mgr.start_all()
    assert all(p.started for p in plugins)
    mgr.stop_all()
    assert all(p.stopped for p in plugins)


def test_skips_broken_plugins(tmp_path):
    d = _make_fake_plugin(tmp_path, "fake_one")
    broken = d / "broken_plugin"
    broken.mkdir()
    (broken / "plugin.py").write_text("def broken(:\n", encoding="utf-8")
    raising = d / "raising_plugin"
    raising.mkdir()
    (raising / "plugin.py").write_text("raise RuntimeError('boom')\n", encoding="utf-8")
    mgr = PluginManager(d, enabled=None)
    plugins = mgr.discover()
    assert [p.id for p in plugins] == ["fake_one"]


def test_factory_customizes_construction(tmp_path):
    d = _make_fake_plugin(tmp_path, "fake_one")
    calls = []

    def factory(plugin_class):
        calls.append(plugin_class)
        return plugin_class()

    mgr = PluginManager(d, enabled=None, factory=factory)
    plugins = mgr.discover()
    assert len(calls) == 1
    assert plugins[0].id == "fake_one"
