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

### Task 5: CPU/GPU 閲囬泦鍣?
**Files:**
- Create: `plugins/system_monitor/collector.py`
- Test: `tests/test_collector.py`

**Interfaces:**
- Produces: `CpuGpuCollector`
  - `CpuGpuCollector(interval_s: float = 1.0) -> CpuGpuCollector`
  - `start() -> None`锛堝惎鍔?daemon 绾跨▼锛屽厛棰勭儹涓€娆?`read_cpu` 瑙勯伩棣栬皟杩斿洖 0锛?  - `stop() -> None`锛堝仠绾跨▼骞剁瓑寰呯粨鏉燂級
  - `snapshot() -> dict`锛歚{"cpu": float, "gpu": float, "gpu_ok": bool}`锛堟嫹璐濓紝绾跨▼瀹夊叏锛?  - `read_cpu() -> float`锛歚psutil.cpu_percent(interval=None)`
  - `read_gpu() -> tuple[float, bool]`锛歱ynvml 璇?util.gpu锛涘紓甯歌繑鍥?`(0.0, False)`

- [ ] **Step 1: 鍐欏け璐ユ祴璇?*

`tests/test_collector.py`锛?```python
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

- [ ] **Step 2: 杩愯纭澶辫触**

Run: `pytest tests/test_collector.py -v`
Expected: FAIL锛坄ModuleNotFoundError: plugins.system_monitor.collector`锛?
- [ ] **Step 3: 瀹炵幇**

`plugins/system_monitor/collector.py`锛?```python
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
        self.read_cpu()  # 棰勭儹锛歱sutil 棣栨璋冪敤杩斿洖 0
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

- [ ] **Step 4: 杩愯纭閫氳繃**

Run: `pytest tests/test_collector.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/system_monitor/collector.py tests/test_collector.py
git commit -m "feat: cpu/gpu collector thread with psutil and pynvml"
```

---


