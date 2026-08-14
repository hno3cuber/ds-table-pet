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

### Task 8: 鎮仠闈㈡澘 pet/hud.py

**Files:**
- Create: `pet/hud.py`
- Test: `tests/test_hud.py`

**Interfaces:**
- Consumes: 鎻掍欢 `panel(parent)` 杩斿洖鐨勬帶浠讹紙Task 6锛?- Produces: `HudPanel(QWidget)`
  - `HudPanel(parent=None) -> HudPanel`
  - `add_block(widget: QWidget) -> None`锛氭妸鎻掍欢鏁版嵁鍧楁寕鍏?  - `show_paused(paused: bool) -> None`锛氭樉绀?娓呴櫎銆屽凡鏆傚仠銆嶈鐩栨爣绛?  - `fade_in() / fade_out() -> None`锛歈PropertyAnimation 閫忔槑搴?0鈫? / 1鈫?锛宖ade_out 瀹屾垚鍚?hide
  - `set_scale(scale: float) -> None`锛氭寜姣斾緥缂╂斁瀛椾綋锛?3px 脳 scale锛屾渶灏?9px锛?  - 鏍峰紡锛氭繁鑹插崐閫忔槑搴曘€佸渾瑙掋€佺櫧瀛楋紙闅忔彃浠跺潡鑷甫锛岄潰鏉夸粎瀹瑰櫒锛?
- [ ] **Step 1: 鍐欏け璐ユ祴璇?*

`tests/test_hud.py`锛?```python
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

- [ ] **Step 2: 杩愯纭澶辫触**

Run: `pytest tests/test_hud.py -v`
Expected: FAIL锛坄ModuleNotFoundError: pet.hud`锛?
- [ ] **Step 3: 瀹炵幇**

`pet/hud.py`锛?```python
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
        self._paused_label = QLabel("宸叉殏鍋?, self)
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

- [ ] **Step 4: 杩愯纭閫氳繃**

Run: `pytest tests/test_hud.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add pet/hud.py tests/test_hud.py
git commit -m "feat: hover hud panel with fade and scale"
```

---


