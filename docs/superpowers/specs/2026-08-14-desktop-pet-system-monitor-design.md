# 桌宠 · 系统监控小管家 设计文档

- 日期：2026-08-14
- 状态：已获用户批准
- 平台：Windows 10（Python 3.14.5，NVIDIA GTX 1650）

## 1. 概述

在 Windows 桌面右下角区域（或任意位置）运行一只透明背景的角色桌宠（素材为 `picture/ds.png`，透明底 PNG），平时以干净角色形态常驻桌面，鼠标悬停时浮现 CPU / GPU 占用率面板。角色可拖拽移动、可右键调整大小（PPT 式角点缩放手柄）。架构采用插件化设计，便于后续追加新功能。

## 2. 目标与非目标

### 目标
- 透明无边框置顶小窗口，显示角色 PNG
- 实时监控 CPU / GPU 占用率，悬停浮现
- 拖拽移动、右键菜单（暂停/恢复、调整大小、退出）
- PPT 式缩放（角点手柄、锁宽高比），尺寸持久化
- 插件化架构：新功能 = 新插件目录 + config 登记，主程序零改动

### 非目标
- 不做开机自启（用户明确不要）
- 不接入 AI 对话、天气、提醒等（留给后续插件）
- 不打包成 exe（本期以 `python main.py` 启动）
- 不支持 AMD / Intel 核显监控（仅 N 卡，经确认硬件为 GTX 1650）

## 3. 架构

三层结构，职责单向依赖：

```
UI 层（窗口 / 角色 / 悬停面板）
   ↑
插件层（插件管理器 ← 具体插件）
   ↑
采集层（后台线程：psutil / pynvml）
```

- **UI 层** 不知道数据从哪来，只渲染插件提供的控件并接收刷新信号
- **插件层** 定义扩展点，具体插件实现 `poll()` 与 `panel()`
- **采集层** 由插件自己持有，独立线程轮询，通过 Qt 信号推送数据，不阻塞 UI

## 4. 目录结构

```
桌宠/
├── main.py                  # 入口：QApplication、读取 config、创建 PetWindow、加载插件
├── config.json              # 配置：刷新间隔、窗口位置、缩放尺寸、启用插件清单
├── requirements.txt         # PySide6、psutil、pynvml
├── pet/
│   ├── __init__.py
│   ├── window.py            # PetWindow：透明置顶窗口、事件分发、右键菜单、缩放模式状态机
│   ├── actor.py             # ActorWidget：角色 PNG 渲染 + 呼吸浮动动画 + 缩放框手柄绘制
│   ├── hud.py               # HudPanel：悬停面板容器，按插件挂数据块，淡入淡出动画
│   └── plugins.py           # PluginManager：扫描/加载/启动/停止插件
├── plugins/
│   └── system_monitor/
│       ├── __init__.py
│       ├── plugin.py        # SystemMonitorPlugin：poll() 数据 + panel() 控件 + 采集线程
│       └── collector.py     # CpuGpuCollector：psutil + pynvml 轮询线程
└── picture/
    └── ds.png               # 角色素材（透明底）
```

## 5. 模块职责

### 5.1 main.py
- 初始化 `QApplication`
- 读取 `config.json`（缺省值兜底，缺失时生成默认配置）
- 创建 `PetWindow`，加载 `picture/ds.png`
- 初始化 `PluginManager`，启动启用清单中的插件
- `exec()` 进入事件循环；退出时保存窗口位置与尺寸到 config

### 5.2 pet/window.py — PetWindow（QWidget）
窗口属性：
- `Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`
- `WA_TranslucentBackground`（真透明，角色 PNG 透明底正确显示）
- 初始尺寸 = 角色原始宽高，若 config 存有缩放尺寸则按比例应用

交互状态机（三种互斥状态）：
1. **正常**：拖拽移动（按住角色本体 move 事件）；悬停显示 HUD；右键弹菜单
2. **缩放模式**：右键菜单「调整大小」进入；角色周围绘制白色选框 + 四角手柄；仅按住角点缩放（锁宽高比），按住本体仍可移动窗口；拖角点松开即应用新尺寸；Esc 或再次选择菜单项退出缩放模式
3. **暂停**：菜单「暂停/恢复」切换；暂停时刷新信号与采集均停止、HUD 显示暂停状态

右键菜单项：`暂停/恢复监控`、`调整大小`、`退出`

### 5.3 pet/actor.py — ActorWidget
- 渲染 `ds.png`（`QPainter`，缩放时按最高质量平滑模式）
- 呼吸动画：`QPropertyAnimation` 对角色做 ±2% 的缓慢缩放 + 轻微上下浮动（可选，默认开）
- 缩放模式下叠加绘制：半透明矩形框 + 四角手柄方块（白色描边）
- 对外暴露 `current_scale`（缩放系数，1.0 为原始尺寸）

### 5.4 pet/hud.py — HudPanel
- 悬停面板，固定位于角色右侧，`enterEvent/leaveEvent` 触发淡入淡出（`QPropertyAnimation`，约 150ms）
- 容器：垂直布局，每个启用插件通过 `panel()` 返回一个控件挂入
- 面板整体随角色缩放（缩放系数传入，控件 `setFixedSize`/字体按比例换算）
- 跟随角色位置（角色移动时面板实时贴住）

### 5.5 pet/plugins.py — PluginManager
- 启动时扫描 `plugins/` 目录，导入每个含 `plugin.py` 的包
- 过滤：`config.json` 中 `enabled_plugins` 清单未列出或不存在则跳过（缺省默认加载全部）
- 提供 `start_all() / stop_all()`；插件实例在 `PetWindow` 上注册 `poll` 信号刷新到其 `panel()` 控件

## 6. 插件接口

```python
class Plugin(ABC):
    id: str                 # 唯一标识，对应 config 中的登记名
    name: str               # 显示名

    @abstractmethod
    def start(self): ...    # 启动后台采集线程
    @abstractmethod
    def stop(self): ...     # 停止并回收线程
    @abstractmethod
    def poll(self) -> dict: # 返回最新数据快照（线程安全读）
    @abstractmethod
    def panel(self, parent) -> QWidget:  # 返回悬停面板上的数据块控件
    def set_paused(self, paused: bool): # 默认空实现
```

后续新功能只需：新建 `plugins/<name>/plugin.py` 实现上述接口 + `config.json` 登记。主程序零改动。

## 7. 数据流

```
CpuGpuCollector 线程（每秒轮询）
  ├─ psutil.cpu_percent(interval=None)   # 连续调用取间隔均值，规避首调返回 0
  └─ pynvml: nvmlDeviceGetUtilizationRates(gpu)
        ↓ 写入线程安全快照（dict）
SystemMonitorPlugin.poll() 返回快照
        ↓ Qt 信号（QTimer 每秒触发，读快照 → emit）
HudPanel 中的数据块控件刷新数字
```

- 刷新间隔来自 `config.json` 的 `refresh_interval_ms`（默认 1000）
- 采集线程为 `threading.Thread(daemon=True)`；UI 刷新用主线程 `QTimer`，避免跨线程碰控件
- GPU 初始化失败（驱动/pynvml 异常）时：面板该行显示「GPU 不可用」，不崩溃

## 8. 交互细节

### 拖拽移动
- 按下：记录窗口全局位置与鼠标全局位置差值
- 移动：窗口 `move()` 跟随
- 仅「正常」与「缩放模式」下按住角色本体时生效

### 缩放（PPT 式）
- 进入：框 + 四角手柄（约 8×8px 白色方块）
- 拖角点：`new_w = 原始宽 × 比例系数`，比例系数由鼠标位移换算，锁宽高比
- 过程中实时重绘角色与窗口大小（窗口 `resize` 跟随，HUD 尺寸按新比例换算）
- 松开：即应用新尺寸，写入 config（`scale` 字段，下次启动按此尺寸），保持缩放模式可继续微调
- 退出模式：Esc 或再次选择「调整大小」菜单项；退出后仍保留已应用的尺寸
- 最小尺寸限制：原始宽高的 30%，最大不限制

### 悬停 HUD
- 进入：淡入（150ms），实时数字每秒刷新
- 移开：淡出后隐藏
- 角色移动时面板跟随

## 9. 配置（config.json）

```json
{
  "refresh_interval_ms": 1000,
  "window": {
    "pos": [100, 100],    # 窗口位置，退出时保存（本期实现）
    "scale": 1.0          # 缩放系数，调整大小后保存，启动时读取
  },
  "breathing_animation": true,
  "enabled_plugins": ["system_monitor"]
}
```

- `scale`：缩放系数（1.0 = 原始尺寸），由「调整大小」写入，启动时读取
- `pos`：窗口位置，退出时保存（本期实现）
- 缺省值兜底：config 不存在或字段缺失时用默认值并回写文件

## 10. 依赖与运行

`requirements.txt`：
```
PySide6
psutil
pynvml
```

运行：`pip install -r requirements.txt` → `python main.py`

## 11. 验证方式（验收清单）

1. `python main.py` 启动，角色透明底正确显示，无黑/白底块
2. 角色可拖拽移动，窗口跟随
3. 鼠标悬停，面板淡入，显示 CPU% / GPU% 且每秒刷新；移开淡出
4. 右键菜单三项齐全；「暂停」后数字停止刷新；「恢复」继续
5. 「调整大小」出现角点框；拖角点锁比例缩放；松手尺寸生效
6. 重启程序，尺寸与位置保持
7. 手动改坏 `config.json` 的字段值，程序不崩溃，按默认值兜底
8. GPU 读不到的异常路径不崩溃（显示「GPU 不可用」）

## 12. 后续扩展示例（验证插件化）

- `plugins/reminder/`：定时提醒插件，复用 `poll/panel` 接口，HUD 追加提醒按钮
- 说明：本期不实现，仅验证接口可扩展性
