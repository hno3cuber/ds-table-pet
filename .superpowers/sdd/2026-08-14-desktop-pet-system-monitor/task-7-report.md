# Task 7 Report: 角色控件 pet/actor.py

## 状态

DONE（含一处 brief 内部不自洽的最小修正，详见 Concerns）

## Commit

- `27f026c` feat: actor widget with breathing animation and resize handles
- 仅包含 `pet/actor.py`、`tests/test_actor.py` 两个文件（149 insertions）
- HEAD 之前为 `daa0e84`，本次提交未触碰 `.superpowers/` 与 `docs/`

## 实现内容

- `ActorWidget(QWidget)`：渲染透明 PNG 角色
  - 构造：`ActorWidget(pixmap: QPixmap, scale: float = 1.0, parent=None)`
  - `set_scale(scale)` / `current_scale()`：缩放更新与查询（窗口尺寸由 PetWindow 管理，此处只重绘）
  - `set_breathing(enabled)`：呼吸动画开关，`QPropertyAnimation` 驱动自定义 `breath` 属性（3s 循环，±2% 缩放），关闭时停动画并复位 `_breath = 0.0`
  - `set_resize_mode(on)`：缩放框绘制开关，同时切换 mouse tracking
  - `handle_at(pos) -> int | None`：四角手柄命中检测（8px 方块绘制、12px 命中区、索引 0=左上 1=右上 2=左下 3=右下），非缩放模式返回 None
  - `sizeHint()`：按 `pet.geometry.scaled_size` 返回 `QSize`
  - `paintEvent`：SmoothPixmapTransform + Antialiasing，呼吸因子作用于 pixmap 缩放绘制；缩放模式下绘制白色半透明选框（2px）与四角白色手柄方块

## 测试

- `tests/test_actor.py`：5 个测试（brief 原文逐字使用）
  1. `test_actor_creates`：构造与初始 scale
  2. `test_handle_hit_outside_resize_mode`：非缩放模式命中返回 None
  3. `test_handle_hit_corners_in_resize_mode`：四角命中 + 中间非手柄
  4. `test_scale_change_repaints`：set_scale 后 current_scale 与 sizeHint
  5. `test_breathing_toggle`：呼吸动画启停状态
- TDD 流程：先写测试，确认失败（`ModuleNotFoundError: No module named 'pet.actor'`），再实现，确认通过
- 结果：`5 passed`（brief 中 "Expected: 4 passed" 与实际测试代码数量 5 个不符，按指示以实际测试代码为准）
- 全量回归：`32 passed, 1 warning`（warning 为既有的 pynvml deprecation，与本任务无关）
- 运行方式：`python -m pytest --basetemp="F:\beifen\hanako\桌宠\.pytest-tmp-$PID" -p no:cacheprovider`（offscreen 由 conftest 强制）

## Concerns

1. **brief 内部不自洽（已修正）**：brief 的 `test_handle_hit_corners_in_resize_mode` 假设 widget 尺寸等于 pixmap 尺寸（200×300，坐标如 (197, 297)），但 brief 原实现未设置 widget 几何，offscreen 下 QWidget 默认尺寸为 640×480，导致该测试失败（`assert None == 1`）。
   - 修正：`__init__` 中增加一行 `self.resize(*scaled_size(pixmap.width(), pixmap.height(), scale))`，使 ActorWidget 独立构造时初始尺寸即匹配 pixmap。
   - 不违背接口契约：`set_scale` 仍只重绘不 resize（注释明确"窗口尺寸由 PetWindow 管理"）；`sizeHint` 语义不变；Task 9 PetWindow 的 QVBoxLayout 会接管几何，互不冲突。
   - 测试文件保持 brief 原文未改动，实现文件相对 brief 仅增此一行。

2. **pynvml deprecation warning**：既有问题（collector.py），非本任务引入，未处理。
