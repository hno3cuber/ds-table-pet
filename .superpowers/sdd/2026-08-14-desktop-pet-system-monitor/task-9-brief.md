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

### Task 9: 涓荤獥鍙?pet/window.py

**Files:**
- Create: `pet/window.py`
- Test: `tests/test_window.py`

**Interfaces:**
- Consumes: `ActorWidget`锛圱ask 7锛夈€乣HudPanel`锛圱ask 8锛夈€乣scaled_size`/`scale_from_drag`锛圱ask 3锛?- Produces: `PetWindow(QWidget)`
  - `PetWindow(pixmap: QPixmap, config: Config) -> PetWindow`
  - 绐楀彛灞炴€э細鏃犺竟妗?+ 缃《 + `WA_TranslucentBackground`锛涘垵濮嬪昂瀵?= `scaled_size(pixmap, config scale)`锛屼綅缃?= config pos
  - 鍛煎惛鍔ㄧ敾璺熼殢 `config.get("breathing_animation", True)`
  - `install_plugin(plugin)`锛氬垱寤哄叾 `panel()` 鎸傚叆 HudPanel锛涙寔鏈夋彃浠跺紩鐢?  - `set_paused(paused)`锛氳浆鍙戠粰鎵€鏈夋彃浠?+ HUD 鏄剧ず鏆傚仠
  - 浜や簰锛氬乏閿嫋鎷界Щ鍔紱鍙抽敭鑿滃崟锛堟殏鍋?鎭㈠銆佽皟鏁村ぇ灏忋€侀€€鍑猴級锛涙偓鍋滄贰鍏ユ贰鍑?HUD锛涚缉鏀炬ā寮忥紙瑙掔偣鎷栨嫿锛孍sc 閫€鍑猴級
  - 缂╂斁閿氱偣锛氫互绐楀彛宸︿笂瑙掍负鍥哄畾閿氾紙Qt resize 榛樿琛屼负锛夛紝鎷栧彸涓嬭浣撻獙鏈€鐩磋锛涘洓涓鍧囧彲鎷?  - `closeEvent` 鐢?main.py 鎺ョ淇濆瓨锛圱ask 10锛夛紝鏈换鍔″彧鎻愪緵 `current_pos()`/`current_scale()` 璇诲彇

- [ ] **Step 1: 鍐欏け璐ユ祴璇?*

`tests/test_window.py`锛?```python
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
    w._begin_resize(3)  # 鎸変笅鍙充笅瑙掓墜鏌?    w._apply_resize(-200)  # 鍚戝乏鎷?200px锛堢浉瀵瑰師瀹?100锛岃Е鍙戞渶灏忛挸鍒讹級
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
        name = "鍋?
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

- [ ] **Step 2: 杩愯纭澶辫触**

Run: `pytest tests/test_window.py -v`
Expected: FAIL锛坄ModuleNotFoundError: pet.window`锛?
- [ ] **Step 3: 瀹炵幇**

`pet/window.py`锛?```python
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

    # ---- 鏌ヨ ----
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

    # ---- 缂╂斁 ----
    def _enter_resize_mode(self):
        """杩涘叆缂╂斁妯″紡锛氭樉绀洪€夋涓庢墜鏌勶紝绛夊緟鐢ㄦ埛鎸夎鐐广€?""
        self._resize_mode = True
        self._actor.set_resize_mode(True)

    def _begin_resize(self, corner: int):
        """鐢ㄦ埛鎸変綇浜嗘煇涓鐐规墜鏌勶紝寮€濮嬩竴娆℃嫋鎷姐€?""
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

    # ---- 榧犳爣浜嬩欢 ----
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

    # ---- 鑿滃崟 ----
    def _show_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        pause_text = "鎭㈠鐩戞帶" if self._paused else "鏆傚仠鐩戞帶"
        action_pause = menu.addAction(pause_text)
        action_resize = menu.addAction("璋冩暣澶у皬")
        menu.addSeparator()
        action_quit = menu.addAction("閫€鍑?)
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

- [ ] **Step 4: 杩愯纭閫氳繃**

Run: `pytest tests/test_window.py -v`
Expected: 4 passed

- [ ] **Step 5: 鎵嬪姩鍐掔儫楠岃瘉锛堟湰浠诲姟 GUI 浜や簰鏃犳硶鑷姩鍖栵紝鍔″繀鐪熸満璺戯級**

Run: `python -c "from PySide6.QtWidgets import QApplication; from PySide6.QtGui import QPixmap; from pet.config import Config; from pet.window import PetWindow; app=QApplication([]); w=PetWindow(QPixmap('picture/ds.png'), Config('config.json')); w.show(); app.exec()"`
Expected: 鐪熷疄绐楀彛鍑虹幇锛岃鑹查€忔槑鏄剧ず锛涙嫋寰楀姩锛涙偓鍋滃嚭闈㈡澘锛涘彸閿彍鍗曞彲鐢紙鏃犻渶鎻掍欢鏁版嵁锛岄潰鏉跨┖浣嗗鍣ㄥ瓨鍦級

- [ ] **Step 6: Commit**

```bash
git add pet/window.py tests/test_window.py
git commit -m "feat: frameless always-on-top pet window with drag/hover/resize"
```

---


