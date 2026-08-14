# 妗屽疇 路 绯荤粺鐩戞帶灏忕瀹?瀹炵幇璁″垝

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 鍦?Windows 妗岄潰瀹炵幇涓€鍙€忔槑鑳屾櫙銆佸彲鎷栨嫿銆佸彲 PPT 寮忕缉鏀俱€佹偓鍋滄樉绀?CPU/GPU 鍗犵敤鐜囩殑瑙掕壊妗屽疇锛屼笖鏋舵瀯鎻掍欢鍖栦互渚垮悗缁墿灞曘€?
**Architecture:** 涓夊眰锛歎I 灞傦紙PetWindow/ActorWidget/HudPanel锛夆啋 鎻掍欢灞傦紙PluginManager + SystemMonitorPlugin锛夆啋 閲囬泦灞傦紙CpuGpuCollector 鐙珛绾跨▼锛宲sutil/pynvml锛夈€傛彃浠跺疄鐜?`poll()`锛堟暟鎹揩鐓э級+ `panel()`锛堟偓鍋滈潰鏉挎帶浠讹級涓や釜鎺ュ彛锛屾柊鍔熻兘 = 鏂版彃浠剁洰褰?+ config 鐧昏銆?
**Tech Stack:** Python 3.14.5銆丳ySide6銆乸sutil銆乸ynvml銆乸ytest锛堟祴璇曪紝offscreen 骞冲彴璺?GUI 鍐掔儫锛?
**Spec:** `docs/superpowers/specs/2026-08-14-desktop-pet-system-monitor-design.md`

## Global Constraints

- 骞冲彴锛歐indows 10锛涙樉鍗?NVIDIA GTX 1650锛堜粎 N 鍗?GPU 鐩戞帶锛宲ynvml锛?- 渚濊禆浠呴檺锛歅ySide6銆乸sutil銆乸ynvml銆乸ytest锛坉ev锛?- 涓嶅仛寮€鏈鸿嚜鍚€佷笉鎵撳寘 exe锛涘惎鍔ㄦ柟寮?`python main.py`
- 绐楀彛蹇呴』锛氭棤杈规 + 缃《 + `WA_TranslucentBackground` 鐪熼€忔槑
- 缂╂斁閿佸楂樻瘮锛堟寜 ds.png 鍘熷姣斾緥锛夛紝鏈€灏?30%
- 缂╂斁灏哄涓庣獥鍙ｄ綅缃啓鍏?`config.json`锛岄噸鍚仮澶?- 鍏ㄩ儴 GUI 娴嬭瘯浠?`QT_QPA_PLATFORM=offscreen` 杩愯锛屼笉寮圭湡瀹炵獥鍙?- 姣忎釜浠诲姟缁撴潫鏃惰繍琛屽叾娴嬭瘯骞舵彁浜わ紙git 浠撳簱锛孴ask 1 鍒濆鍖栵級

---

### Task 4: 鎻掍欢鎺ュ彛涓庢彃浠剁鐞嗗櫒

**Files:**
- Create: `pet/plugin.py`
- Create: `pet/plugins.py`
- Test: `tests/test_plugins.py`

**Interfaces:**
- Produces:
  - `pet.plugin.Plugin(ABC)`锛氬睘鎬?`id: str`銆乣name: str`锛涙柟娉?`start()/stop()/poll()/panel(parent)/set_paused(paused)`
  - `pet.plugins.PluginManager`
    - `PluginManager(plugins_dir: str | Path, enabled: list[str] | None = None, factory=None) -> PluginManager`
    - `discover() -> list[Plugin]`锛氭壂鎻?`plugins_dir` 涓嬪惈 `plugin.py` 鐨勫瓙鐩綍锛岀害瀹氭ā鍧楀唴绫诲悕 `PluginClass`锛堝繀椤荤户鎵?Plugin锛屽惁鍒欒烦杩囷級锛沗enabled=None` 鏃跺姞杞藉叏閮紝鍚﹀垯鍙姞杞?id 鍦?enabled 涓殑
    - `factory`锛氬彲閫?`callable(plugin_class) -> Plugin`锛岀敤浜庡悜鎻掍欢鏋勯€犱紶鍙傦紙濡備粠 config 璇诲埛鏂伴棿闅旓級锛涢粯璁?`plugin_class()`
    - `start_all() / stop_all()`锛氬鎵€鏈夊凡鍙戠幇瀹炰緥璋冪敤

- [ ] **Step 1: 鍐欏け璐ユ祴璇?*

`tests/test_plugins.py`锛?```python
import sys
from pathlib import Path
import pytest
from pet.plugin import Plugin
from pet.plugins import PluginManager

FAKE_PLUGIN_SRC = '''
from pet.plugin import Plugin

class PluginClass(Plugin):
    id = "fake_monitor"
    name = "鍋囨彃浠?

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


def test_start_all_calls_each(tmp_path):
    d = _make_fake_plugin(tmp_path, "fake_one")
    mgr = PluginManager(d, enabled=None)
    plugins = mgr.discover()
    mgr.start_all()
    assert all(p.started for p in plugins)
    mgr.stop_all()
    assert all(p.stopped for p in plugins)


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
```

- [ ] **Step 2: 杩愯纭澶辫触**

Run: `pytest tests/test_plugins.py -v`
Expected: FAIL锛坄ModuleNotFoundError: pet.plugin`锛?
- [ ] **Step 3: 瀹炵幇**

`pet/plugin.py`锛?```python
from abc import ABC, abstractmethod


class Plugin(ABC):
    id: str = ""
    name: str = ""

    @abstractmethod
    def start(self):
        """鍚姩鍚庡彴閲囬泦绛夎祫婧愩€?""

    @abstractmethod
    def stop(self):
        """鍋滄骞跺洖鏀惰祫婧愩€?""

    @abstractmethod
    def poll(self) -> dict:
        """杩斿洖鏈€鏂版暟鎹揩鐓э紙绾跨▼瀹夊叏璇伙級銆?""

    @abstractmethod
    def panel(self, parent):
        """杩斿洖鎮仠闈㈡澘涓婄殑鏁版嵁鍧楁帶浠躲€?""

    def set_paused(self, paused: bool):
        """榛樿绌哄疄鐜帮紱闇€瑕佸搷搴旀殏鍋滅殑鎻掍欢鑷瑕嗙洊銆?""
```

`pet/plugins.py`锛?```python
import importlib.util
from pathlib import Path

from pet.plugin import Plugin


class PluginManager:
    def __init__(self, plugins_dir, enabled=None, factory=None):
        self.plugins_dir = Path(plugins_dir)
        self.enabled = list(enabled) if enabled is not None else None
        self.factory = factory or (lambda plugin_class: plugin_class())
        self.instances: list[Plugin] = []

    def discover(self) -> list[Plugin]:
        instances: list[Plugin] = []
        for entry in sorted(self.plugins_dir.iterdir()):
            mod_file = entry / "plugin.py"
            if not entry.is_dir() or not mod_file.exists():
                continue
            spec = importlib.util.spec_from_file_location(f"plugin_{entry.name}", mod_file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            plugin_class = getattr(module, "PluginClass", None)
            if plugin_class is None or not issubclass(plugin_class, Plugin):
                continue
            inst = self.factory(plugin_class)
            if self.enabled is not None and inst.id not in self.enabled:
                continue
            instances.append(inst)
        self.instances = instances
        return instances

    def start_all(self):
        for inst in self.instances:
            inst.start()

    def stop_all(self):
        for inst in self.instances:
            inst.stop()
```

- [ ] **Step 4: 杩愯纭閫氳繃**

Run: `pytest tests/test_plugins.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add pet/plugin.py pet/plugins.py tests/test_plugins.py
git commit -m "feat: plugin ABC and directory-based plugin manager"
```

---


