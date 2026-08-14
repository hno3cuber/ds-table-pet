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

### Task 1: 椤圭洰鑴氭墜鏋朵笌娴嬭瘯鍩虹璁炬柦

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `pytest.ini`
- Create: `tests/conftest.py`
- Create: `tests/test_smoke.py`
- Create: `pet/__init__.py`, `plugins/__init__.py`, `plugins/system_monitor/__init__.py`

**Interfaces:**
- Produces: pytest 鍙繍琛岀幆澧冿紱`tests/conftest.py` 鎻愪緵 `qapp` fixture锛坰ession 绾?QApplication锛宱ffscreen锛?
- [ ] **Step 1: 鍒濆鍖?git 浠撳簱涓庡拷鐣ヨ鍒?*

```bash
git init
```

`.gitignore`锛?```
__pycache__/
*.pyc
.venv/
.pytest_cache/
```

- [ ] **Step 2: 鍐?requirements.txt**

```
PySide6
psutil
pynvml
pytest
```

- [ ] **Step 3: 瀹夎渚濊禆**

Run: `pip install -r requirements.txt`
Expected: 涓変釜杩愯鏃跺寘 + pytest 瀹夎鎴愬姛锛圥ySide6 浣撶Н澶э紝绛夊緟灞炴甯革級

- [ ] **Step 4: 鍐?pytest 閰嶇疆涓?fixture**

`pytest.ini`锛?```ini
[pytest]
testpaths = tests
addopts = -q
```

`tests/conftest.py`锛?```python
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
```

`tests/test_smoke.py`锛?```python
def test_import_qt(qapp):
    from PySide6.QtWidgets import QWidget
    w = QWidget()
    assert w is not None
```

- [ ] **Step 5: 鍒涘缓绌哄寘**

Run: `New-Item -ItemType Directory -Force pet, plugins, plugins\system_monitor, tests | Out-Null; @("pet\__init__.py", "plugins\__init__.py", "plugins\system_monitor\__init__.py") | ForEach-Object { New-Item -ItemType File -Force $_ | Out-Null }`
Expected: 涓変釜绌?`__init__.py` 瀛樺湪

- [ ] **Step 6: 杩愯娴嬭瘯纭鍩虹璁炬柦鍙敤**

Run: `pytest`
Expected: 1 passed

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: scaffold project with test infra"
```

---


