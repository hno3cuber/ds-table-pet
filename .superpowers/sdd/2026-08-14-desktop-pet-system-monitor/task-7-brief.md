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

### Task 7: 瑙掕壊鎺т欢 pet/actor.py

**Files:**
- Create: `pet/actor.py`
- Test: `tests/test_actor.py`

**Interfaces:**
- Consumes: `scaled_size`锛圱ask 3锛?- Produces: `ActorWidget(QWidget)`
  - `ActorWidget(pixmap: QPixmap, scale: float = 1.0) -> ActorWidget`
  - `set_scale(scale: float) -> None`锛氭洿鏂扮缉鏀惧苟閲嶇粯锛堢獥鍙ｅ昂瀵哥敱 PetWindow 绠＄悊锛?  - `current_scale() -> float`
  - `set_breathing(enabled: bool)`锛氬懠鍚稿姩鐢伙紙卤2% 缂╂斁 + 杞诲井娴姩锛孮PropertyAnimation锛?  - `set_resize_mode(on: bool)`锛氬紑鍚?鍏抽棴缂╂斁妗嗙粯鍒?  - `handle_at(pos: QPoint) -> int | None`锛氬洓瑙掓墜鏌勫懡涓娴嬶紙瑙掔偣绱㈠紩 0=宸︿笂 1=鍙充笂 2=宸︿笅 3=鍙充笅锛屽懡涓尯鍩?12px锛夛紱闈炵缉鏀炬ā寮忚繑鍥?None
  - `paintEvent`锛氭渶楂樿川閲忓钩婊戠缉鏀剧粯鍒?pixmap锛涚缉鏀炬ā寮忎笅缁樺埗鐧借壊閫夋 + 鍥涜鎵嬫焺锛?脳8 鐧藉潡锛?
- [ ] **Step 1: 鍐欏け璐ユ祴璇?*

`tests/test_actor.py`锛?```python
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
    assert actor.handle_at(QPoint(2, 2)) == 0          # 宸︿笂
    assert actor.handle_at(QPoint(197, 2)) == 1        # 鍙充笂
    assert actor.handle_at(QPoint(2, 297)) == 2        # 宸︿笅
    assert actor.handle_at(QPoint(197, 297)) == 3      # 鍙充笅
    assert actor.handle_at(QPoint(100, 100)) is None   # 涓棿涓嶆槸鎵嬫焺


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

- [ ] **Step 2: 杩愯纭澶辫触**

Run: `pytest tests/test_actor.py -v`
Expected: FAIL锛坄ModuleNotFoundError: pet.actor`锛?
- [ ] **Step 3: 瀹炵幇**

`pet/actor.py`锛?```python
from PySide6.QtCore import QPoint, QPropertyAnimation, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from pet.geometry import scaled_size

_HANDLE = 8          # 鎵嬫焺缁樺埗灏哄
_HIT = 12            # 鎵嬫焺鍛戒腑鍖哄煙
_BREATH_MAX = 0.02   # 鍛煎惛骞呭害 卤2%


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

- [ ] **Step 4: 杩愯纭閫氳繃**

Run: `pytest tests/test_actor.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add pet/actor.py tests/test_actor.py
git commit -m "feat: actor widget with breathing animation and resize handles"
```

---


