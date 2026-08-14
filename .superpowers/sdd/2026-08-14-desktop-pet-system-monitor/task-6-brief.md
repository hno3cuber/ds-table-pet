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

### Task 6: 绯荤粺鐩戞帶鎻掍欢鏈綋

**Files:**
- Create: `plugins/system_monitor/plugin.py`
- Test: `tests/test_system_monitor_plugin.py`

**Interfaces:**
- Consumes: `CpuGpuCollector`锛圱ask 5锛夈€乣Plugin`锛圱ask 4锛?- Produces: `SystemMonitorPlugin(Plugin)`
  - `SystemMonitorPlugin(interval_ms: int = 1000)`锛氭瀯閫犱笉鍚姩浠讳綍璧勬簮
  - `id = "system_monitor"`銆乣name = "绯荤粺鐩戞帶"`
  - `start()`锛氬惎鍔?collector + `interval_ms` 闂撮殧鐨?QTimer 椹卞姩 `_refresh()`
  - `stop()`锛氬仠 collector 涓?QTimer
  - `poll()` 鈫?collector.snapshot()
  - `panel(parent) -> QWidget`锛氬瀭鐩村竷灞€锛屼袱琛?QLabel锛坄CPU 12%` / `GPU 34%` 鎴?`GPU 涓嶅彲鐢╜锛夛紝鏍峰紡娣辫壊鍗婇€忔槑搴曘€佺櫧瀛椼€佸渾瑙?  - `set_paused(paused)`锛氭殏鍋滄椂 QTimer 鍋溿€佹爣绛炬樉绀恒€屽凡鏆傚仠銆嶏紱鎭㈠鍚庢爣绛炬仮澶?  - `_refresh()`锛氱敤 snapshot 鏇存柊鏍囩锛涙爣绛炬湭鍒涘缓锛坧anel 鏈皟锛夋椂瀹夊叏璺宠繃

- [ ] **Step 1: 鍐欏け璐ユ祴璇?*

`tests/test_system_monitor_plugin.py`锛?```python
from plugins.system_monitor.plugin import SystemMonitorPlugin


def test_plugin_metadata():
    p = SystemMonitorPlugin()
    assert p.id == "system_monitor"
    assert p.name == "绯荤粺鐩戞帶"


def test_poll_returns_snapshot_shape():
    p = SystemMonitorPlugin()
    snap = p.poll()
    assert set(snap.keys()) == {"cpu", "gpu", "gpu_ok"}


def test_panel_creates_widget(qapp):
    p = SystemMonitorPlugin()
    w = p.panel(None)
    assert w is not None
    assert w.layout() is not None
    assert w.layout().count() == 2  # CPU 琛?+ GPU 琛?

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

- [ ] **Step 2: 杩愯纭澶辫触**

Run: `pytest tests/test_system_monitor_plugin.py -v`
Expected: FAIL锛坄ModuleNotFoundError: plugins.system_monitor.plugin`锛?
- [ ] **Step 3: 瀹炵幇**

`plugins/system_monitor/plugin.py`锛?```python
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from pet.plugin import Plugin
from plugins.system_monitor.collector import CpuGpuCollector

_PANEL_STYLE = """
QLabel { color: #ffffff; background: transparent; font-size: 13px; padding: 2px 8px; }
"""


class SystemMonitorPlugin(Plugin):
    id = "system_monitor"
    name = "绯荤粺鐩戞帶"

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
                label.setText("宸叉殏鍋?)
        else:
            if self._timer is not None:
                self._timer.start(1000)
            self._refresh()

    def _refresh(self):
        if not self._labels:
            return
        snap = self.poll()
        cpu_text = f"CPU {snap['cpu']:.0f}%"
        gpu_text = "GPU 涓嶅彲鐢? if not snap["gpu_ok"] else f"GPU {snap['gpu']:.0f}%"
        self._labels[0].setText(cpu_text)
        self._labels[1].setText(gpu_text)
```

- [ ] **Step 4: 杩愯纭閫氳繃**

Run: `pytest tests/test_system_monitor_plugin.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/system_monitor/plugin.py tests/test_system_monitor_plugin.py
git commit -m "feat: system monitor plugin with poll/panel/pause"
```

---


