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

### Task 3: 缂╂斁鍑犱綍璁＄畻 pet/geometry.py

**Files:**
- Create: `pet/geometry.py`
- Test: `tests/test_geometry.py`

**Interfaces:**
- Produces:
  - `scaled_size(orig_w: int, orig_h: int, scale: float) -> tuple[int, int]`锛堝洓鑸嶄簲鍏ワ紝鏈€灏?1px锛?  - `scale_from_drag(orig_w: int, drag_dx: int, current_scale: float, min_scale: float = 0.3) -> float`锛堟瘮渚嬬敱妯悜浣嶇Щ椹卞姩锛岄攣瀹介珮姣旓紱浣庝簬 min_scale 鏃堕挸鍒讹級

- [ ] **Step 1: 鍐欏け璐ユ祴璇?*

`tests/test_geometry.py`锛?```python
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

- [ ] **Step 2: 杩愯纭澶辫触**

Run: `pytest tests/test_geometry.py -v`
Expected: FAIL锛坄ModuleNotFoundError: pet.geometry`锛?
- [ ] **Step 3: 瀹炵幇**

`pet/geometry.py`锛?```python
def scaled_size(orig_w: int, orig_h: int, scale: float) -> tuple[int, int]:
    return (max(1, round(orig_w * scale)), max(1, round(orig_h * scale)))


def scale_from_drag(orig_w: int, drag_dx: int, current_scale: float, min_scale: float = 0.3) -> float:
    return max(min_scale, current_scale + drag_dx / orig_w)
```

- [ ] **Step 4: 杩愯纭閫氳繃**

Run: `pytest tests/test_geometry.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add pet/geometry.py tests/test_geometry.py
git commit -m "feat: aspect-locked scale geometry helpers"
```

---


