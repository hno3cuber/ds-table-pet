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

### Task 10: 鍏ュ彛涓庤閰?main.py

**Files:**
- Create: `main.py`
- Create: `config.json`锛堥娆¤繍琛岃嚜鍔ㄧ敓鎴愶級
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes: 鍏ㄩ儴妯″潡
- Produces: `main.py`
  - 璇诲彇 `config.json`锛堜笉瀛樺湪鍒欓粯璁ょ敓鎴愶級
  - 鍔犺浇 `picture/ds.png`锛堢己澶辨椂鎶ラ敊閫€鍑猴級
  - 鍒涘缓 `PetWindow`锛宍PluginManager("plugins", enabled=config["enabled_plugins"]).discover()` 鍚庨€愪釜 `install_plugin`
  - `closeEvent`锛氫繚瀛樼獥鍙ｄ綅缃笌缂╂斁灏哄
  - `main()` 鍑芥暟鍙?import 娴嬭瘯锛沗app.setQuitOnLastWindowClosed(True)`

- [ ] **Step 1: 鍐欏け璐ユ祴璇?*

`tests/test_main.py`锛?```python
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

- [ ] **Step 2: 杩愯纭澶辫触**

Run: `pytest tests/test_main.py -v`
Expected: FAIL锛坄ModuleNotFoundError: main`锛?
- [ ] **Step 3: 瀹炵幇**

`main.py`锛?```python
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
        raise FileNotFoundError(f"瑙掕壊鍥剧墖鍔犺浇澶辫触: {path}")
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
    """鍦ㄧ獥鍙?closeEvent 鍚庡厹搴曚繚瀛樼姸鎬併€?""

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

- [ ] **Step 4: 杩愯纭閫氳繃**

Run: `pytest tests/test_main.py -v`
Expected: 3 passed

- [ ] **Step 5: 鏂板鎻掍欢宸ュ巶娴嬭瘯**

`tests/test_main.py` 杩藉姞锛?```python
def test_install_plugins_passes_interval(qapp, tmp_path):
    import sys
    from pathlib import Path
    from pet.config import Config
    from PySide6.QtGui import QPixmap
    from pet.window import PetWindow
    from pet.plugins import PluginManager

    # 鐢ㄤ复鏃跺亣鎻掍欢鐩綍锛岄伩鍏嶄緷璧栫湡瀹?system_monitor 鍒濆鍖?    fake_dir = tmp_path / "plugins"
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


- [ ] **Step 5: 鐪熸満楠屾敹锛堝叧閿楠わ級**

Run: `python main.py`
Expected:
- 瑙掕壊閫忔槑搴曟纭樉绀哄湪灞忓箷鎸囧畾浣嶇疆锛坈onfig 鐨?pos锛?- 鎮仠娴幇 CPU%/GPU% 闈㈡澘锛屾瘡绉掑埛鏂?- 鎷栨嫿绉诲姩銆佸彸閿彍鍗曘€屾殏鍋?鎭㈠銆嶃€岃皟鏁村ぇ灏忋€嶃€岄€€鍑恒€嶅叏閮ㄥ彲鐢?- 璋冩暣澶у皬鍚庨€€鍑猴紝閲嶅惎 `python main.py`锛屽昂瀵镐笌浣嶇疆淇濇寔
- 鍏抽棴鍚?`config.json` 涓嚭鐜版洿鏂板悗鐨?`pos` 涓?`scale`

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: main entry with plugin assembly and state persistence"
```

---


