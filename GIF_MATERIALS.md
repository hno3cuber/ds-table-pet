# GIF 素材接入手册（桌宠动画）

> 给以后要自己换/加 GIF 动画的你。核心结论先放这：**不需要切片**，
> 程序用 `QImageReader` 把 gif 逐帧读进内存播放，磁盘上放一个 gif 就行。

---

## 0. 当前素材基线（看懂这条就能开始）

| 文件 | 用途 | 画布 | 帧数 | 播放节奏 |
|---|---|---|---|---|
| `picture/idel.gif` | 站立循环 | 720×960 | 89 | 按素材帧延迟（40~100ms 逐帧） |
| `picture/walk.gif` | 行走动画 | 720×960 | 25 | 固定 50ms（20fps，为了配走速） |

代码里对应四个「播放参数」的落点（都在 `pet/window.py` 顶部常量区）：

```python
_WALK_FRAME_MS = 50    # walk 每帧停留，改它 = 改行走动画速度
_WANDER_MOVE_MS = 25   # 位置刷新间隔，不用动
_WALK_STEP_PX = 4      # 每次位置刷新位移 4px → 160px/s，想快慢改它
_IDLE_FRAME_MS = 100   # idle 无延迟信息时的兜底帧停留
_WALK_VISUAL_SCALE = 0.955  # 行走相对站立的视觉大小修正（见 §4）
```

两个素材**画布同为 720×960**，这是刻意的：idle↔walk 切换时窗口尺寸不变、零跳动。
你以后做素材也优先用这个画布，能省掉一整类问题。

---

## 1. 核心机制：为什么不用切片

`main.py` 里的 `load_gif_frames(path)` 一次把 gif 读成两个列表：

```python
frames, delays = main.load_gif_frames("picture/xxx.gif")
# frames: list[QPixmap]  每一帧
# delays: list[int]      每一帧的停留毫秒（读自 gif 内部）
```

- **均匀节奏**（如行走，为了步速与位移同步）→ 用固定 `QTimer`，忽略 delays，直接 `50ms` 切一帧。
- **不均匀节奏**（如站立的呼吸感，帧延迟 40/100ms 混排）→ 每切一帧后把 timer 的间隔设成下一帧的 delay，代码参考 `pet/window.py` 的 `_idle_delay_ms()` + `_idle_frame_tick()`。

两种 timer 都开了 `Qt.PreciseTimer`。Windows 默认系统时钟粒度 15.6ms，不开它 50ms 的定时器实际只有 ~16fps，会卡。

---

## 2. 场景 A：只换站立动画（最简）

1. 用新文件**直接覆盖** `picture/idel.gif`（文件名别改）。
2. 代码一行不用动，重启即生效。
3. 画布尺寸若变了，窗口像素尺寸会跟着变（窗口 = 画布 × config 里的 scale），旧 config.json 存的是按旧画布算的缩放，看起来比例不对就删 `config.json` 让它重建，或右键重新调大小。
4. 换完看一眼站立和行走的角色**大小是否一致**，不一致按 §4 校准。

## 3. 场景 B：只换行走动画

1. 覆盖 `picture/walk.gif`。
2. 帧数变了没关系（取模循环）。但如果新素材的**步态节奏设计**不同，可能得调 `_WALK_FRAME_MS`（播放速度）和 `_WALK_STEP_PX`（走速），原则：步子别跟位移打架（脚下打滑 = 速度不匹配）。
3. 按 §4 重新校准 `_WALK_VISUAL_SCALE`（不同素材角色占比必然不同）。

## 4. 关键工具：视觉大小校准（bbox 测量）

两个 gif 画布相同，但**角色在画布里的占比**可能不同（站立留白多、动作画得满），直接播会一个角色大一个角色小。用透明像素边界盒量出「角色真实内容高度比」，就是修正系数。

把下面脚本存成临时文件跑（要装着 PySide6）：

```python
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImageReader

app = QApplication([])

def content_height(path):
    r = QImageReader(path)
    heights = []
    while True:
        img = r.read()
        if img.isNull():
            break
        img = img.convertToFormat(QImage.Format_ARGB32)
        w, h = img.width(), img.height()
        alpha = bytes(img.constBits())[3::4]  # alpha 通道抽出来
        miny, maxy = None, -1
        for y in range(h):
            if any(alpha[y * w:(y + 1) * w]):
                if miny is None:
                    miny = y
                maxy = y
        heights.append(maxy - miny + 1)
    return sum(heights) / len(heights)

idle_h = content_height("picture/idel.gif")   # 当前约 766.6
walk_h = content_height("picture/walk.gif")   # 当前约 803.1
print(f"修正系数 = {idle_h / walk_h:.3f}")    # 当前 0.955 → 填进 _WALK_VISUAL_SCALE
```

把算出的值填回 `pet/window.py` 的 `_WALK_VISUAL_SCALE`。
绘制端（`pet/actor.py`）会把这个系数乘到适配矩形上，**保持宽高比 + 贴底居中**，所以角色脚始终落地、不会被裁。

## 5. 场景 C：加一个全新动作（跳跃/坐下/睡觉…）

以「跳跃 jump.gif」为例，完整接线：

**① 素材准备**
透明背景；画布尽量也用 720×960（省一切对齐问题）；脚底画在画布底部、水平居中；别混入多余透明大边。

**② `main.py`：加载**

```python
JUMP_PATH = str(_resource_base() / "picture" / "jump.gif")
# ...
jump_frames, jump_delays = load_gif_frames(JUMP_PATH)
window = build_window(pixmap, config, idle_frames=idle_frames, idle_delays=idle_delays,
                      walk_frames=walk_frames, jump_frames=jump_frames,
                      jump_delays=jump_delays)
```

**③ `pet/window.py`：接收入口**

构造函数加参数，存成字段：

```python
def __init__(self, pixmap, config, poses=None, idle_frames=None, idle_delays=None,
             walk_frames=None, jump_frames=None, jump_delays=None):
    ...
    self._jump_frames = list(jump_frames) if jump_frames else None
    self._jump_delays = list(jump_delays) if jump_delays else None
```

**④ 播放：参考现成的两个「显示方法」抄一个**

站立循环是怎么播的，照抄一份就行：

```python
def _show_jump(self):
    self._walking = False
    self._walk_timer.stop()
    self._frame_timer.stop()
    self._idle_timer.stop()          # 关键：把别的动画 timer 全停干净
    self._actor.set_animation_frames(self._jump_frames)  # actor 通用帧播放
    self._actor.set_frame_index(0)
    self._actor.set_breathing(False)
    # 均匀节奏用固定间隔；要素材节奏就逐帧 delay（参考 _idle_delay_ms）
    self._jump_timer.start(50)
```

`pet/actor.py` 的 `set_animation_frames(frames, content_scale=1.0)` 对任何帧序列通用，
绘制的贴底/镜像/保比例全在里面，新动作基本不用碰 actor。

**⑤ 触发条件：自己定**
菜单项、随机触发、某个事件……触发时调 `_show_jump()`，结束后记得回到 `_enter_idle()` 或 `_show_idle_animation()`。
要动窗口位置（如跳跃）就参考 `_wander_move_tick` 的位移 + `wander_step_x` 掉头那套。
**互斥纪律**：任何两个动画状态之间切换，先停对方的 timer（idle/walk/frame/jump），
否则会出现两个 timer 抢着切 actor 帧。

**⑥ 视觉校准**
跟 §4 一样量一次，若要跟站立对齐就传 `content_scale`（跳跃这类临时动作可放宽，别顶出窗口即可）。

**⑦ 打包**
`大肥鱼桌宠.spec` 里 `datas=[('picture', 'picture'), ...]` 是**整目录收集**，新 gif 放进 `picture/` 自动进包，spec 不用动，重新打包即可。

**⑧ 测试**
项目有完整 pytest 套件（offscreen Qt），新增动画照 `tests/test_window.py` 里
`test_idle_walk_switch_frames`、`test_idle_frame_advances` 的写法补用例，
跑 `py -m pytest tests` 全绿再交。

---

## 6. 常见坑速查

| 症状 | 原因 | 解法 |
|---|---|---|
| 动画一卡一卡 | Windows 时钟粒度 | timer 必须 `Qt.PreciseTimer`（现有代码已开，新加的 timer 记得照抄） |
| 两个状态切换时帧乱跳 | 两个 timer 同时驱动 actor | 切换先互停所有动画 timer |
| 站立/行走角色大小不一致 | 素材画布占比不同 | §4 bbox 测量 → `_WALK_VISUAL_SCALE` |
| 切换动画窗口跳动/变形 | 画布尺寸不一致 | 统一 720×960；否则接受 actor 的保比例贴底留边 |
| 角色周围出现方框 | gif 无透明通道 | 导出时选透明背景 |
| 脚下悬空 / 陷入地面 | 角色在画布里的脚底位置不齐 | 素材把脚底画到画布底边同一条线 |
| 走路脚下打滑 | 动画步幅与位移速度不匹配 | 调 `_WALK_FRAME_MS` 或 `_WALK_STEP_PX` |

## 7. 内存提醒（重要）

gif 在内存里是解压后的：**每帧 ≈ 宽×高×4 字节**。

- 720×960 一帧 ≈ 2.76MB
- 当前 idel.gif 89 帧 ≈ **246MB**（已属偏大，机器吃得下但别再加更离谱的）
- 行走 25 帧 ≈ 69MB

做新素材时心里算一笔：帧数 × 2.76MB（按 720×960 计）。动作类素材建议控制在 30~60 帧。
