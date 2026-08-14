# 桌宠 · 系统监控小管家 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Windows 桌面实现一只透明背景、可拖拽、可 PPT 式缩放、悬停显示 CPU/GPU 占用率的角色桌宠，且架构插件化以便后续扩展。

**Architecture:** 三层：UI 层（PetWindow/ActorWidget/HudPanel）→ 插件层（PluginManager + SystemMonitorPlugin）→ 采集层（CpuGpuCollector 独立线程，psutil/pynvml）。插件实现 `poll()`（数据快照）+ `panel()`（悬停面板控件）两个接口，新功能 = 新插件目录 + config 登记。

**Tech Stack:** Python 3.14.5、PySide6、psutil、pynvml、pytest（测试，offscreen 平台跑 GUI 冒烟）

**Spec:** `docs/superpowers/specs/2026-08-14-desktop-pet-system-monitor-design.md`

## Global Constraints

- 平台：Windows 10；显卡 NVIDIA GTX 1650（仅 N 卡 GPU 监控，pynvml）
- 依赖仅限：PySide6、psutil、pynvml、pytest（dev）
- 不做开机自启、不打包 exe；启动方式 `python main.py`
- 窗口必须：无边框 + 置顶 + `WA_TranslucentBackground` 真透明
- 缩放锁宽高比（按 ds.png 原始比例），最小 30%
- 缩放尺寸与窗口位置写入 `config.json`，重启恢复
- 全部 GUI 测试以 `QT_QPA_PLATFORM=offscreen` 运行，不弹真实窗口
- 每个任务结束时运行其测试并提交（git 仓库，Task 1 初始化）

---

### Task 1: 项目脚手架与测试基础设施

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `pytest.ini`
- Create: `tests/conftest.py`
- Create: `tests/test_smoke.py`
- Create: `pet/__init__.py`, `plugins/__init__.py`, `plugins/system_monitor/__init__.py`

**Interfaces:**
- Produces: pytest 可运行环境；`tests/conftest.py` 提供 `qapp` fixture（session 级 QApplication，offscreen）

- [ ] **Step 1: 初始化 git 仓库与忽略规则**

```bash
git init
```

`.gitignore`：
```
__pycache__/
*.pyc
.venv/
.pytest_cache/
```

- [ ] **Step 2: 写 requirements.txt**

```
PySide6
psutil
pynvml
pytest
```

- [ ] **Step 3: 安装依赖**

Run: `pip install -r requirements.txt`
Expected: 三个运行时包 + pytest 安装成功（PySide6 体积大，等待属正常）

- [ ] **Step 4: 写 pytest 配置与 fixture**

`pytest.ini`：
```ini
[pytest]
testpaths = tests
addopts = -q
```

`tests/conftest.py`：
```python
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
```

`tests/test_smoke.py`：
```python
def test_import_qt(qapp):
    from PySide6.QtWidgets import QWidget
    w = QWidget()
    assert w is not None
```

- [ ] **Step 5: 创建空包**

Run: `New-Item -ItemType Directory -Force pet, plugins, plugins\system_monitor, tests | Out-Null; @("pet\__init__.py", "plugins\__init__.py", "plugins\system_monitor\__init__.py") | ForEach-Object { New-Item -ItemType File -Force $_ | Out-Null }`
Expected: 三个空 `__init__.py` 存在

- [ ] **Step 6: 运行测试确认基础设施可用**

Run: `pytest`
Expected: 1 passed

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: scaffold project with test infra"
```

---

### Task 2: 配置模块 pet/config.py

**Files:**
- Create: `pet/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `Config` 类
  - `Config(path: str | Path) -> Config`
  - `Config.get(key: str, default=None) -> Any`（支持 `window.scale` 点分路径）
  - `Config.set(key: str, value) -> None`
  - `Config.save() -> None`（写回原路径，utf-8）
  - 默认配置常量 `DEFAULT_CONFIG`：`refresh_interval_ms=1000`、`window.pos=[100,100]`、`window.scale=1.0`、`breathing_animation=True`、`enabled_plugins=["system_monitor"]`
  - 行为：文件缺失/字段缺失 → 用默认值兜底，缺失字段在 save 时回填

- [ ] **Step 1: 写失败测试**

`tests/test_config.py`：
```python
import json
import pytest
from pet.config import Config, DEFAULT_CONFIG


def test_defaults_when_file_missing(tmp_path):
    cfg = Config(tmp_path / "config.json")
    assert cfg.get("refresh_interval_ms") == 1000
    assert cfg.get("window.scale") == 1.0
    assert cfg.get("enabled_plugins") == ["system_monitor"]


def test_merges_missing_fields_with_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"refresh_interval_ms": 500}), encoding="utf-8")
    cfg = Config(p)
    assert cfg.get("refresh_interval_ms") == 500
    assert cfg.get("window.scale") == 1.0


def test_set_and_save(tmp_path):
    p = tmp_path / "config.json"
    cfg = Config(p)
    cfg.set("window.scale", 1.5)
    cfg.set("window.pos", [200, 300])
    cfg.save()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["window"]["scale"] == 1.5
    assert data["window"]["pos"] == [200, 300]
    assert data["refresh_interval_ms"] == 1000  # 默认字段回填


def test_defaults_constants_shape():
    assert DEFAULT_CONFIG["window"]["scale"] == 1.0
    assert DEFAULT_CONFIG["enabled_plugins"] == ["system_monitor"]
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_config.py -v`
Expected: FAIL（`ModuleNotFoundError: pet.config`）

- [ ] **Step 3: 实现**

`pet/config.py`：
```python
import copy
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "refresh_interval_ms": 1000,
    "window": {"pos": [100, 100], "scale": 1.0},
    "breathing_animation": True,
    "enabled_plugins": ["system_monitor"],
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


class Config:
    def __init__(self, path):
        self.path = Path(path)
        loaded = {}
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                loaded = {}
        self.data = _deep_merge(DEFAULT_CONFIG, loaded)

    def get(self, key, default=None):
        node = self.data
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key, value):
        parts = key.split(".")
        node = self.data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest tests/test_config.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add pet/config.py tests/test_config.py
git commit -m "feat: config module with default fallback and dotted keys"
```

---

### Task 3: 缩放几何计算 pet/geometry.py

**Files:**
- Create: `pet/geometry.py`
- Test: `tests/test_geometry.py`

**Interfaces:**
- Produces:
  - `scaled_size(orig_w: int, orig_h: int, scale: float) -> tuple[int, int]`（四舍五入，最小 1px）
  - `scale_from_drag(orig_w: int, drag_dx: int, current_scale: float, min_scale: float = 0.3) -> float`（比例由横向位移驱动，锁宽高比；低于 min_scale 时钳制）

- [ ] **Step 1: 写失败测试**

`tests/test_geometry.py`：
```python
import pytest
from pet.geometry import scaled_size, scale_from_drag


def test_scaled_size_rounds_half_up():
    assert scaled_size(100, 200, 1.5) == (150, 300)


def test_scaled_size_min_one_px():
    assert scaled_size(100, 200, 0.005) == (1, 1)


def test_scale_increases_with_drag():
    assert scale_from_drag(100, 50, 1.0) == pytest.approx(1.5)


def test_scale_decreases_with_negative_drag():
    assert scale_from_drag(100, -50, 1.0) == pytest.approx(0.5)


def test_scale_clamps_at_min():
    assert scale_from_drag(100, -999, 1.0, min_scale=0.3) == 0.3
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_geometry.py -v`
Expected: FAIL（`ModuleNotFoundError: pet.geometry`）

- [ ] **Step 3: 实现**

`pet/geometry.py`：
```python
def scaled_size(orig_w: int, orig_h: int, scale: float) -> tuple[int, int]:
    return (max(1, round(orig_w * scale)), max(1, round(orig_h * scale)))


def scale_from_drag(orig_w: int, drag_dx: int, current_scale: float, min_scale: float = 0.3) -> float:
    return max(min_scale, current_scale + drag_dx / orig_w)
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest tests/test_geometry.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add pet/geometry.py tests/test_geometry.py
git commit -m "feat: aspect-locked scale geometry helpers"
```

---

### Task 4: 插件接口与插件管理器

**Files:**
- Create: `pet/plugin.py`
- Create: `pet/plugins.py`
- Test: `tests/test_plugins.py`

**Interfaces:**
- Produces:
  - `pet.plugin.Plugin(ABC)`：属性 `id: str`、`name: str`；方法 `start()/stop()/poll()/panel(parent)/set_paused(paused)`
  - `pet.plugins.PluginManager`
    - `PluginManager(plugins_dir: str | Path, enabled: list[str] | None = None, factory=None) -> PluginManager`
    - `discover() -> list[Plugin]`：扫描 `plugins_dir` 下含 `plugin.py` 的子目录，约定模块内类名 `PluginClass`（必须继承 Plugin，否则跳过）；`enabled=None` 时加载全部，否则只加载 id 在 enabled 中的
    - `factory`：可选 `callable(plugin_class) -> Plugin`，用于向插件构造传参（如从 config 读刷新间隔）；默认 `plugin_class()`
    - `start_all() / stop_all()`：对所有已发现实例调用

- [ ] **Step 1: 写失败测试**

`tests/test_plugins.py`：
```python
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

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_plugins.py -v`
Expected: FAIL（`ModuleNotFoundError: pet.plugin`）

- [ ] **Step 3: 实现**

`pet/plugin.py`：
```python
from abc import ABC, abstractmethod


class Plugin(ABC):
    id: str = ""
    name: str = ""

    @abstractmethod
    def start(self):
        """启动后台采集等资源。"""

    @abstractmethod
    def stop(self):
        """停止并回收资源。"""

    @abstractmethod
    def poll(self) -> dict:
        """返回最新数据快照（线程安全读）。"""

    @abstractmethod
    def panel(self, parent):
        """返回悬停面板上的数据块控件。"""

    def set_paused(self, paused: bool):
        """默认空实现；需要响应暂停的插件自行覆盖。"""
```

`pet/plugins.py`：
```python
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

- [ ] **Step 4: 运行确认通过**

Run: `pytest tests/test_plugins.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add pet/plugin.py pet/plugins.py tests/test_plugins.py
git commit -m "feat: plugin ABC and directory-based plugin manager"
```

---

### Task 5: CPU/GPU 采集器

**Files:**
- Create: `plugins/system_monitor/collector.py`
- Test: `tests/test_collector.py`

**Interfaces:**
- Produces: `CpuGpuCollector`
  - `CpuGpuCollector(interval_s: float = 1.0) -> CpuGpuCollector`
  - `start() -> None`（启动 daemon 线程，先预热一次 `read_cpu` 规避首调返回 0）
  - `stop() -> None`（停线程并等待结束）
  - `snapshot() -> dict`：`{"cpu": float, "gpu": float, "gpu_ok": bool}`（拷贝，线程安全）
  - `read_cpu() -> float`：`psutil.cpu_percent(interval=None)`
  - `read_gpu() -> tuple[float, bool]`：pynvml 读 util.gpu；异常返回 `(0.0, False)`

- [ ] **Step 1: 写失败测试**

`tests/test_collector.py`：
```python
import time
import pytest
from plugins.system_monitor.collector import CpuGpuCollector


def test_update_writes_snapshot(monkeypatch):
    c = CpuGpuCollector()
    monkeypatch.setattr(c, "read_cpu", lambda: 12.0)
    monkeypatch.setattr(c, "read_gpu", lambda: (34.0, True))
    c._update()
    snap = c.snapshot()
    assert snap["cpu"] == 12.0
    assert snap["gpu"] == 34.0
    assert snap["gpu_ok"] is True


def test_gpu_failure_reported(monkeypatch):
    c = CpuGpuCollector()
    monkeypatch.setattr(c, "read_cpu", lambda: 1.0)
    monkeypatch.setattr(c, "read_gpu", lambda: (0.0, False))
    c._update()
    assert c.snapshot()["gpu_ok"] is False


def test_snapshot_is_copy(monkeypatch):
    c = CpuGpuCollector()
    monkeypatch.setattr(c, "read_cpu", lambda: 5.0)
    monkeypatch.setattr(c, "read_gpu", lambda: (6.0, True))
    c._update()
    snap = c.snapshot()
    snap["cpu"] = 99.0
    assert c.snapshot()["cpu"] == 5.0


def test_start_stop_lifecycle():
    c = CpuGpuCollector(interval_s=0.01)
    c.start()
    time.sleep(0.05)
    c.stop()
    assert c._thread is not None
    assert not c._thread.is_alive()


def test_read_gpu_returns_false_on_error(monkeypatch):
    c = CpuGpuCollector()
    import plugins.system_monitor.collector as collector_mod
    monkeypatch.setattr(collector_mod.pynvml, "nvmlInit", lambda: (_ for _ in ()).throw(RuntimeError("no gpu")))
    val, ok = c.read_gpu()
    assert val == 0.0
    assert ok is False
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_collector.py -v`
Expected: FAIL（`ModuleNotFoundError: plugins.system_monitor.collector`）

- [ ] **Step 3: 实现**

`plugins/system_monitor/collector.py`：
```python
import threading
import time

import psutil
import pynvml


class CpuGpuCollector:
    def __init__(self, interval_s: float = 1.0):
        self.interval_s = interval_s
        self._snapshot = {"cpu": 0.0, "gpu": 0.0, "gpu_ok": False}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._nvml_handle = None

    def read_cpu(self) -> float:
        return psutil.cpu_percent(interval=None)

    def read_gpu(self) -> tuple[float, bool]:
        try:
            if self._nvml_handle is None:
                pynvml.nvmlInit()
                self._nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(self._nvml_handle)
            return float(util.gpu), True
        except Exception:
            return 0.0, False

    def _update(self):
        cpu = self.read_cpu()
        gpu, gpu_ok = self.read_gpu()
        with self._lock:
            self._snapshot = {"cpu": cpu, "gpu": gpu, "gpu_ok": gpu_ok}

    def _loop(self):
        self.read_cpu()  # 预热：psutil 首次调用返回 0
        while not self._stop.is_set():
            time.sleep(self.interval_s)
            self._update()

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="cpu-gpu-collector")
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._snapshot)
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest tests/test_collector.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/system_monitor/collector.py tests/test_collector.py
git commit -m "feat: cpu/gpu collector thread with psutil and pynvml"
```

---

### Task 6: 系统监控插件本体

**Files:**
- Create: `plugins/system_monitor/plugin.py`
- Test: `tests/test_system_monitor_plugin.py`

**Interfaces:**
- Consumes: `CpuGpuCollector`（Task 5）、`Plugin`（Task 4）
- Produces: `SystemMonitorPlugin(Plugin)`
  - `SystemMonitorPlugin(interval_ms: int = 1000)`：构造不启动任何资源
  - `id = "system_monitor"`、`name = "系统监控"`
  - `start()`：启动 collector + `interval_ms` 间隔的 QTimer 驱动 `_refresh()`
  - `stop()`：停 collector 与 QTimer
  - `poll()` → collector.snapshot()
  - `panel(parent) -> QWidget`：垂直布局，两行 QLabel（`CPU 12%` / `GPU 34%` 或 `GPU 不可用`），样式深色半透明底、白字、圆角
  - `set_paused(paused)`：暂停时 QTimer 停、标签显示「已暂停」；恢复后标签恢复
  - `_refresh()`：用 snapshot 更新标签；标签未创建（panel 未调）时安全跳过

- [ ] **Step 1: 写失败测试**

`tests/test_system_monitor_plugin.py`：
```python
from plugins.system_monitor.plugin import SystemMonitorPlugin


def test_plugin_metadata():
    p = SystemMonitorPlugin()
    assert p.id == "system_monitor"
    assert p.name == "系统监控"


def test_poll_returns_snapshot_shape():
    p = SystemMonitorPlugin()
    snap = p.poll()
    assert set(snap.keys()) == {"cpu", "gpu", "gpu_ok"}


def test_panel_creates_widget(qapp):
    p = SystemMonitorPlugin()
    w = p.panel(None)
    assert w is not None
    assert w.layout() is not None
    assert w.layout().count() == 2  # CPU 行 + GPU 行


def test_refresh_updates_labels(qapp):
    from PySide6.QtWidgets import QLabel
    p = SystemMonitorPlugin()
    w = p.panel(None)
    labels = [w.layout().itemAt(i).widget() for i in range(2)]
    p.collector._snapshot = {"cpu": 55.0, "gpu": 70.0, "gpu_ok": True}
    p._refresh()
    assert "55" in labels[0].text()
    assert "70" in labels[1].text()


def test_pause_shows_paused_state(qapp):
    p = SystemMonitorPlugin()
    p.panel(None)
    p.set_paused(True)
    assert p._paused is True
    p.set_paused(False)
    assert p._paused is False


def test_interval_ms_from_constructor():
    p = SystemMonitorPlugin(interval_ms=500)
    assert p.interval_ms == 500
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_system_monitor_plugin.py -v`
Expected: FAIL（`ModuleNotFoundError: plugins.system_monitor.plugin`）

- [ ] **Step 3: 实现**

`plugins/system_monitor/plugin.py`：
```python
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from pet.plugin import Plugin
from plugins.system_monitor.collector import CpuGpuCollector

_PANEL_STYLE = """
QLabel { color: #ffffff; background: transparent; font-size: 13px; padding: 2px 8px; }
"""


class SystemMonitorPlugin(Plugin):
    id = "system_monitor"
    name = "系统监控"

    def __init__(self, interval_ms: int = 1000):
        self.interval_ms = interval_ms
        self.collector = CpuGpuCollector()
        self._timer = None
        self._labels = []
        self._paused = False

    def start(self):
        self.collector.start()
        if self._timer is None:
            self._timer = QTimer()
            self._timer.timeout.connect(self._refresh)
            self._timer.start(self.interval_ms)

    def stop(self):
        self.collector.stop()
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def poll(self) -> dict:
        return self.collector.snapshot()

    def panel(self, parent) -> QWidget:
        widget = QWidget(parent)
        widget.setStyleSheet(_PANEL_STYLE)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        self._labels = [QLabel("CPU --", widget), QLabel("GPU --", widget)]
        for label in self._labels:
            layout.addWidget(label)
        self._refresh()
        return widget

    def set_paused(self, paused: bool):
        self._paused = paused
        if paused:
            if self._timer is not None:
                self._timer.stop()
            for label in self._labels:
                label.setText("已暂停")
        else:
            if self._timer is not None:
                self._timer.start(1000)
            self._refresh()

    def _refresh(self):
        if not self._labels:
            return
        snap = self.poll()
        cpu_text = f"CPU {snap['cpu']:.0f}%"
        gpu_text = "GPU 不可用" if not snap["gpu_ok"] else f"GPU {snap['gpu']:.0f}%"
        self._labels[0].setText(cpu_text)
        self._labels[1].setText(gpu_text)
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest tests/test_system_monitor_plugin.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/system_monitor/plugin.py tests/test_system_monitor_plugin.py
git commit -m "feat: system monitor plugin with poll/panel/pause"
```

---

### Task 7: 角色控件 pet/actor.py

**Files:**
- Create: `pet/actor.py`
- Test: `tests/test_actor.py`

**Interfaces:**
- Consumes: `scaled_size`（Task 3）
- Produces: `ActorWidget(QWidget)`
  - `ActorWidget(pixmap: QPixmap, scale: float = 1.0) -> ActorWidget`
  - `set_scale(scale: float) -> None`：更新缩放并重绘（窗口尺寸由 PetWindow 管理）
  - `current_scale() -> float`
  - `set_breathing(enabled: bool)`：呼吸动画（±2% 缩放 + 轻微浮动，QPropertyAnimation）
  - `set_resize_mode(on: bool)`：开启/关闭缩放框绘制
  - `handle_at(pos: QPoint) -> int | None`：四角手柄命中检测（角点索引 0=左上 1=右上 2=左下 3=右下，命中区域 12px）；非缩放模式返回 None
  - `paintEvent`：最高质量平滑缩放绘制 pixmap；缩放模式下绘制白色选框 + 四角手柄（8×8 白块）

- [ ] **Step 1: 写失败测试**

`tests/test_actor.py`：
```python
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
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_actor.py -v`
Expected: FAIL（`ModuleNotFoundError: pet.actor`）

- [ ] **Step 3: 实现**

`pet/actor.py`：
```python
from PySide6.QtCore import QPoint, QPropertyAnimation, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from pet.geometry import scaled_size

_HANDLE = 8          # 手柄绘制尺寸
_HIT = 12            # 手柄命中区域
_BREATH_MAX = 0.02   # 呼吸幅度 ±2%


class ActorWidget(QWidget):
    def __init__(self, pixmap: QPixmap, scale: float = 1.0, parent=None):
        super().__init__(parent)
        self._pixmap = pixmap
        self._scale = scale
        self._resize_mode = False
        self._breath = 0.0
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

    breath = property(get_breath, set_breath)

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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.Antialiasing, True)
        breath_factor = 1.0 + (self._breath - 0.5) * 2 * _BREATH_MAX
        target = self.rect().size()
        scaled = QPixmap(self._pixmap.size())
        scaled.fill(Qt.transparent)
        sp = QPainter(scaled)
        sp.setRenderHint(QPainter.SmoothPixmapTransform, True)
        sp.scale(breath_factor, breath_factor)
        sp.drawPixmap(0, 0, self._pixmap)
        sp.end()
        painter.drawPixmap(self.rect(), scaled, scaled.rect())
        if self._resize_mode:
            pen = QPen(QColor(255, 255, 255, 220), 2)
            painter.setPen(pen)
            painter.drawRect(QRect(1, 1, self.width() - 2, self.height() - 2))
            painter.setBrush(QColor(255, 255, 255))
            painter.setPen(Qt.NoPen)
            for origin in self._corner_positions():
                painter.drawRect(QRect(origin, origin + QPoint(_HANDLE, _HANDLE)))
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest tests/test_actor.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add pet/actor.py tests/test_actor.py
git commit -m "feat: actor widget with breathing animation and resize handles"
```

---

### Task 8: 悬停面板 pet/hud.py

**Files:**
- Create: `pet/hud.py`
- Test: `tests/test_hud.py`

**Interfaces:**
- Consumes: 插件 `panel(parent)` 返回的控件（Task 6）
- Produces: `HudPanel(QWidget)`
  - `HudPanel(parent=None) -> HudPanel`
  - `add_block(widget: QWidget) -> None`：把插件数据块挂入
  - `show_paused(paused: bool) -> None`：显示/清除「已暂停」覆盖标签
  - `fade_in() / fade_out() -> None`：QPropertyAnimation 透明度 0→1 / 1→0，fade_out 完成后 hide
  - `set_scale(scale: float) -> None`：按比例缩放字体（13px × scale，最小 9px）
  - 样式：深色半透明底、圆角、白字（随插件块自带，面板仅容器）

- [ ] **Step 1: 写失败测试**

`tests/test_hud.py`：
```python
from PySide6.QtWidgets import QLabel, QWidget
from pet.hud import HudPanel


def test_hud_creates(qapp):
    hud = HudPanel()
    assert hud is not None


def test_add_block_appears_in_layout(qapp):
    hud = HudPanel()
    block = QLabel("CPU 12%")
    hud.add_block(block)
    assert hud.layout().count() == 1


def test_show_paused_sets_overlay(qapp):
    hud = HudPanel()
    hud.show_paused(True)
    assert hud._paused_label.isHidden() is False
    hud.show_paused(False)
    assert hud._paused_label.isHidden() is True


def test_set_scale_font(qapp):
    hud = HudPanel()
    block = QLabel("CPU 12%")
    hud.add_block(block)
    base = block.font().pointSizeF() or 13.0
    hud.set_scale(2.0)
    assert block.font().pointSizeF() >= base
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_hud.py -v`
Expected: FAIL（`ModuleNotFoundError: pet.hud`）

- [ ] **Step 3: 实现**

`pet/hud.py`：
```python
from PySide6.QtCore import QEasingCurve, QPropertyAnimation
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
        self.setAttribute(self.WA_TranslucentBackground, True)
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
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest tests/test_hud.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add pet/hud.py tests/test_hud.py
git commit -m "feat: hover hud panel with fade and scale"
```

---

### Task 9: 主窗口 pet/window.py

**Files:**
- Create: `pet/window.py`
- Test: `tests/test_window.py`

**Interfaces:**
- Consumes: `ActorWidget`（Task 7）、`HudPanel`（Task 8）、`scaled_size`/`scale_from_drag`（Task 3）
- Produces: `PetWindow(QWidget)`
  - `PetWindow(pixmap: QPixmap, config: Config) -> PetWindow`
  - 窗口属性：无边框 + 置顶 + `WA_TranslucentBackground`；初始尺寸 = `scaled_size(pixmap, config scale)`，位置 = config pos
  - 呼吸动画跟随 `config.get("breathing_animation", True)`
  - `install_plugin(plugin)`：创建其 `panel()` 挂入 HudPanel；持有插件引用
  - `set_paused(paused)`：转发给所有插件 + HUD 显示暂停
  - 交互：左键拖拽移动；右键菜单（暂停/恢复、调整大小、退出）；悬停淡入淡出 HUD；缩放模式（角点拖拽，Esc 退出）
  - 缩放锚点：以窗口左上角为固定锚（Qt resize 默认行为），拖右下角体验最直觉；四个角均可拖
  - `closeEvent` 由 main.py 接管保存（Task 10），本任务只提供 `current_pos()`/`current_scale()` 读取

- [ ] **Step 1: 写失败测试**

`tests/test_window.py`：
```python
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
    w._apply_resize(-200)  # 向左拖 200px（相对原宽 100，触发最小钳制）
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
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_window.py -v`
Expected: FAIL（`ModuleNotFoundError: pet.window`）

- [ ] **Step 3: 实现**

`pet/window.py`：
```python
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor, QPixmap
from PySide6.QtWidgets import QMenu, QVBoxLayout, QWidget

from pet.actor import ActorWidget
from pet.geometry import scale_from_drag, scaled_size
from pet.hud import HudPanel


class PetWindow(QWidget):
    def __init__(self, pixmap: QPixmap, config):
        super().__init__()
        self._pixmap = pixmap
        self._config = config
        self._scale = float(config.get("window.scale", 1.0))
        self._paused = False
        self._resize_mode = False
        self._drag_offset = None
        self._resize_corner = None
        self._plugins = []

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._actor = ActorWidget(pixmap, self._scale)
        self._actor.set_breathing(bool(config.get("breathing_animation", True)))
        layout.addWidget(self._actor)

        self._hud = HudPanel(self)
        self._hud.set_scale(self._scale)

        w, h = scaled_size(pixmap.width(), pixmap.height(), self._scale)
        self.resize(w, h)
        pos = self._config.get("window.pos", [100, 100])
        self.move(pos[0], pos[1])

    # ---- 查询 ----
    def current_scale(self) -> float:
        return self._scale

    def current_pos(self):
        p = self.pos()
        return [p.x(), p.y()]

    def install_plugin(self, plugin):
        self._plugins.append(plugin)
        self._hud.add_block(plugin.panel(self._hud))

    def set_paused(self, paused: bool):
        self._paused = paused
        for plugin in self._plugins:
            plugin.set_paused(paused)
        self._hud.show_paused(paused)

    # ---- 缩放 ----
    def _enter_resize_mode(self):
        """进入缩放模式：显示选框与手柄，等待用户按角点。"""
        self._resize_mode = True
        self._actor.set_resize_mode(True)

    def _begin_resize(self, corner: int):
        """用户按住了某个角点手柄，开始一次拖拽。"""
        self._resize_corner = corner

    def _apply_resize(self, drag_dx: int):
        self._scale = scale_from_drag(self._pixmap.width(), drag_dx, self._scale)
        self._actor.set_scale(self._scale)
        w, h = scaled_size(self._pixmap.width(), self._pixmap.height(), self._scale)
        self.resize(w, h)
        self._hud.set_scale(self._scale)

    def _finish_resize(self):
        self._resize_corner = None
        self._config.set("window.scale", self._scale)
        self._config.save()

    def _exit_resize_mode(self):
        self._resize_mode = False
        self._resize_corner = None
        self._actor.set_resize_mode(False)
        self.unsetCursor()

    # ---- 鼠标事件 ----
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._show_menu(event.globalPos())
            return
        if event.button() != Qt.LeftButton:
            return
        local = event.position().toPoint()
        if self._resize_mode:
            corner = self._actor.handle_at(local)
            if corner is not None:
                self._resize_corner = corner
                self._drag_offset = None
                return
        self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        self._resize_corner = None

    def mouseMoveEvent(self, event):
        if self._resize_corner is not None:
            self._apply_resize(event.globalPosition().toPoint().x() - self.x())
            return
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if self._resize_corner is not None:
            self._finish_resize()
        self._drag_offset = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self._resize_mode:
            self._exit_resize_mode()
        else:
            super().keyPressEvent(event)

    def enterEvent(self, event):
        self._hud.fade_in()
        self._position_hud()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hud.fade_out()
        super().leaveEvent(event)

    def _position_hud(self):
        self._hud.adjustSize()
        x = self.width() + 6
        y = 0
        self._hud.move(x, y)

    def resizeEvent(self, event):
        self._position_hud()
        super().resizeEvent(event)

    # ---- 菜单 ----
    def _show_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        pause_text = "恢复监控" if self._paused else "暂停监控"
        action_pause = menu.addAction(pause_text)
        action_resize = menu.addAction("调整大小")
        menu.addSeparator()
        action_quit = menu.addAction("退出")
        chosen = menu.exec(global_pos)
        if chosen is action_pause:
            self.set_paused(not self._paused)
        elif chosen is action_resize:
            if self._resize_mode:
                self._exit_resize_mode()
            else:
                self._enter_resize_mode()
        elif chosen is action_quit:
            self.close()
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest tests/test_window.py -v`
Expected: 4 passed

- [ ] **Step 5: 手动冒烟验证（本任务 GUI 交互无法自动化，务必真机跑）**

Run: `python -c "from PySide6.QtWidgets import QApplication; from PySide6.QtGui import QPixmap; from pet.config import Config; from pet.window import PetWindow; app=QApplication([]); w=PetWindow(QPixmap('picture/ds.png'), Config('config.json')); w.show(); app.exec()"`
Expected: 真实窗口出现，角色透明显示；拖得动；悬停出面板；右键菜单可用（无需插件数据，面板空但容器存在）

- [ ] **Step 6: Commit**

```bash
git add pet/window.py tests/test_window.py
git commit -m "feat: frameless always-on-top pet window with drag/hover/resize"
```

---

### Task 10: 入口与装配 main.py

**Files:**
- Create: `main.py`
- Create: `config.json`（首次运行自动生成）
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes: 全部模块
- Produces: `main.py`
  - 读取 `config.json`（不存在则默认生成）
  - 加载 `picture/ds.png`（缺失时报错退出）
  - 创建 `PetWindow`，`PluginManager("plugins", enabled=config["enabled_plugins"]).discover()` 后逐个 `install_plugin`
  - `closeEvent`：保存窗口位置与缩放尺寸
  - `main()` 函数可 import 测试；`app.setQuitOnLastWindowClosed(True)`

- [ ] **Step 1: 写失败测试**

`tests/test_main.py`：
```python
from PySide6.QtGui import QPixmap
from pet.config import Config
from pet.window import PetWindow
import main


def test_main_loads_pixmap(tmp_path):
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
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_main.py -v`
Expected: FAIL（`ModuleNotFoundError: main`）

- [ ] **Step 3: 实现**

`main.py`：
```python
import sys

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from pet.config import Config
from pet.plugins import PluginManager
from pet.window import PetWindow

CONFIG_PATH = "config.json"
PIXMAP_PATH = "picture/ds.png"


def load_pixmap(path: str) -> QPixmap:
    pm = QPixmap(path)
    if pm.isNull():
        raise FileNotFoundError(f"角色图片加载失败: {path}")
    return pm


def build_window(pixmap: QPixmap, config: Config) -> PetWindow:
    return PetWindow(pixmap, config)


def install_plugins(window: PetWindow, config: Config):
    interval_ms = int(config.get("refresh_interval_ms", 1000))

    def factory(plugin_class):
        if getattr(plugin_class, "id", None) == "system_monitor":
            return plugin_class(interval_ms=interval_ms)
        return plugin_class()

    mgr = PluginManager("plugins", enabled=config.get("enabled_plugins", None), factory=factory)
    plugins = mgr.discover()
    for plugin in plugins:
        window.install_plugin(plugin)
    mgr.start_all()
    return mgr


def save_state(window: PetWindow, config: Config):
    config.set("window.pos", window.current_pos())
    config.set("window.scale", window.current_scale())
    config.save()


def main():
    app = QApplication(sys.argv)
    config = Config(CONFIG_PATH)
    pixmap = load_pixmap(PIXMAP_PATH)
    window = build_window(pixmap, config)
    install_plugins(window, config)
    window.show()
    window.installEventFilter(_StateSaver(window, config))

    def on_close():
        save_state(window, config)

    app.aboutToQuit.connect(on_close)
    sys.exit(app.exec())


class _StateSaver:
    """在窗口 closeEvent 后兜底保存状态。"""

    def __init__(self, window: PetWindow, config: Config):
        self.window = window
        self.config = config

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent

        if obj is self.window and event.type() == QEvent.Close:
            save_state(self.window, self.config)
        return False


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest tests/test_main.py -v`
Expected: 3 passed

- [ ] **Step 5: 新增插件工厂测试**

`tests/test_main.py` 追加：
```python
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


- [ ] **Step 5: 真机验收（关键步骤）**

Run: `python main.py`
Expected:
- 角色透明底正确显示在屏幕指定位置（config 的 pos）
- 悬停浮现 CPU%/GPU% 面板，每秒刷新
- 拖拽移动、右键菜单「暂停/恢复」「调整大小」「退出」全部可用
- 调整大小后退出，重启 `python main.py`，尺寸与位置保持
- 关闭后 `config.json` 中出现更新后的 `pos` 与 `scale`

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: main entry with plugin assembly and state persistence"
```

---

### Task 11: 全量验收与收尾

**Files:**
- Modify: `docs/superpowers/plans/2026-08-14-desktop-pet-system-monitor.md`（本文件，验收结果勾选后更新）

**Interfaces:**
- 无新接口；运行完整验收清单

- [x] **Step 1: 全量测试**

Run: `pytest`
Expected: 全部通过（config 4 + geometry 5 + plugins 5 + collector 5 + system_monitor 6 + actor 5 + hud 4 + window 5 + main 4 = 43 passed）
实际：54 passed（43 为过时预期；本轮验收前基线为 47 passed，Step 3 修复后新增 7 条回归测试，最终 54 passed，全部通过）

- [x] **Step 2: 按设计文档第 11 节执行 8 条验收**

Run: `python main.py` 逐条核对：
1. 透明底正确显示，无黑/白底块 ⏳ 待用户真机验收
2. 拖拽移动跟随 ⏳ 待用户真机验收
3. 悬停面板淡入，CPU%/GPU% 每秒刷新，移开淡出 ⏳ 待用户真机验收
4. 右键菜单三项齐全；暂停后数字停止刷新；恢复继续 ⏳ 待用户真机验收
5. 调整大小：角点框出现，锁比例缩放，松手生效 ⏳ 待用户真机验收
6. 重启后尺寸与位置保持 ⏳ 待用户真机验收
7. 改坏 config.json 字段值后启动不崩溃，默认值兜底 ✅（沙盒冒烟：坏值构造 Config + build_window + install_plugins 全链路不抛异常，兜底默认值；修复见 Step 3）
8. GPU 读不到时不崩溃，显示「GPU 不可用」✅（沙盒冒烟：monkeypatch `read_gpu` 抛异常后 collector 存活、标签显示「GPU 不可用」；修复见 Step 3）

- [x] **Step 3: 修复验收中发现的问题并重跑对应测试**

验收冒烟发现两处问题并已修复：
- `pet/config.py`：Config 对错误类型的字段值（如 `scale="abc"`、`pos="oops"`、`refresh_interval_ms=-5`、`enabled_plugins=null`、顶层非对象）无类型级兜底，`PetWindow` 构造会抛 `ValueError`。新增 `_sanitize/_value_ok` 按默认配置类型校验并回退默认值。
- `plugins/system_monitor/collector.py`：`_update()` 不保护 `read_gpu()`，异常会杀死采集线程。新增 try/except 兜底，异常时标记 `gpu_ok=False`。
重跑：全量 54 passed，两条冒烟均 PASS。

- [x] **Step 4: 最终提交**

```bash
git add 精确文件（plan 文档 + 修复源码 + 回归测试）
git commit -m "docs: plan completion and acceptance record"
```
