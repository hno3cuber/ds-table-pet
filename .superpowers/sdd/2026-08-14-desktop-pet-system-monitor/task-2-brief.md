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

### Task 2: 閰嶇疆妯″潡 pet/config.py

**Files:**
- Create: `pet/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `Config` 绫?  - `Config(path: str | Path) -> Config`
  - `Config.get(key: str, default=None) -> Any`锛堟敮鎸?`window.scale` 鐐瑰垎璺緞锛?  - `Config.set(key: str, value) -> None`
  - `Config.save() -> None`锛堝啓鍥炲師璺緞锛寀tf-8锛?  - 榛樿閰嶇疆甯搁噺 `DEFAULT_CONFIG`锛歚refresh_interval_ms=1000`銆乣window.pos=[100,100]`銆乣window.scale=1.0`銆乣breathing_animation=True`銆乣enabled_plugins=["system_monitor"]`
  - 琛屼负锛氭枃浠剁己澶?瀛楁缂哄け 鈫?鐢ㄩ粯璁ゅ€煎厹搴曪紝缂哄け瀛楁鍦?save 鏃跺洖濉?
- [ ] **Step 1: 鍐欏け璐ユ祴璇?*

`tests/test_config.py`锛?```python
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
    assert data["refresh_interval_ms"] == 1000  # 榛樿瀛楁鍥炲～


def test_defaults_constants_shape():
    assert DEFAULT_CONFIG["window"]["scale"] == 1.0
    assert DEFAULT_CONFIG["enabled_plugins"] == ["system_monitor"]
```

- [ ] **Step 2: 杩愯纭澶辫触**

Run: `pytest tests/test_config.py -v`
Expected: FAIL锛坄ModuleNotFoundError: pet.config`锛?
- [ ] **Step 3: 瀹炵幇**

`pet/config.py`锛?```python
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

- [ ] **Step 4: 杩愯纭閫氳繃**

Run: `pytest tests/test_config.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add pet/config.py tests/test_config.py
git commit -m "feat: config module with default fallback and dotted keys"
```

---


