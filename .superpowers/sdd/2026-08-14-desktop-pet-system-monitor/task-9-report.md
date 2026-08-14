# Task 9 Report: 主窗口 pet/window.py

## 状态

DONE

## Commit

- 哈希：`fe5549f5e1efc24bf7664d97d29e8b22b24c26ee`（short: `fe5549f`）
- message：`feat: frameless always-on-top pet window with drag/hover/resize`
- 变更文件：`pet/window.py`（新增 161 行）、`tests/test_window.py`（新增 64 行）

## 实现摘要

- **PetWindow(QWidget)**：无边框 + 置顶 + `WA_TranslucentBackground` + `WA_DeleteOnClose=False`；初始尺寸 = `scaled_size(pixmap, config scale)`，位置 = `config["window.pos"]`（默认 [100,100]）
- **三态交互**：
  - 正常态：左键按住拖动移动（`_drag_offset` 基于 frameGeometry 计算）
  - 缩放态：`_enter_resize_mode` 显示 ActorWidget 选框+角点手柄；按住角点（`handle_at` 命中）后 `_apply_resize` 拖拽缩放，`Esc` 退出（`_exit_resize_mode` 恢复 cursor）；松开鼠标时 `_finish_resize` 写回 `window.scale` 并 save。缩放锚点为窗口左上角（Qt resize 默认行为），拖右下角体验最直觉；四个角均可拖
  - 暂停态：右键菜单切换 `set_paused`，转发给所有插件 + HUD 显示"已暂停"
- **右键菜单**：暂停/恢复监控、调整大小（进入/退出缩放模式）、退出
- **HUD**：`enterEvent` 淡入 + 定位（窗口右侧 +6px），`leaveEvent` 淡出，`resizeEvent` 跟随重定位
- **呼吸动画**：`self._actor.set_breathing(bool(config.get("breathing_animation", True)))`，显式随 config 控制
- **插件**：`install_plugin` 持有插件引用，创建其 `panel()` 挂入 HudPanel（窗口 show 前调用，无动态 add_block 隐藏问题）

## 测试结果

- `tests/test_window.py`：**5 passed**（brief 含 5 个测试函数，Expected 以实际测试代码为准）
  - `test_window_creates_with_scale`：scale 2.0 → 400x600
  - `test_window_min_scale_after_resize_drag`：右下角 -200px 拖拽 → scale 钳制 ≥ 0.3
  - `test_breathing_follows_config`：breathing_animation=False → 动画不在 Running
  - `test_install_plugin_adds_block`：Fake 插件 panel 挂入 HUD
  - `test_toggle_pause`：set_paused 状态切换
- 失败确认：实现前 `ModuleNotFoundError: No module named 'pet.window'`（收集期 ERROR）
- 全量回归：`tests/` 41 passed（仅 pynvml 弃用 FutureWarning，已知非本任务引入）

## 冒烟验证（offscreen）

`QT_QPA_PLATFORM=offscreen` 下构造 + `show()` 成功：window visible=True、scale 1.0、pos [100,100]、尺寸 910x941（ds.png 原比例）、呼吸动画 Running、HUD 初始隐藏。offscreen 无法真实显示窗口，交互观感（拖拽/缩放/悬停淡入淡出/透明背景）留给 Task 10/11 真机验收。

## Concerns

1. **HudPanel 淡入淡出用 windowOpacity**（集成提醒 1）：窗口级属性会连带 PetWindow 整链透明度，角色会跟着面板一起淡。本任务按 brief 实现且未改 HudPanel；Task 10 真机冒烟时评估观感，若差再切换 QGraphicsOpacityEffect（Task 10 之后处理）
2. **offscreen 限制**：本任务 GUI 交互（拖拽手感、角点命中范围、菜单）无法自动化验证，真机必经
3. **`QCursor` 未使用 import**：brief 代码原文自带，保留（照 brief 逐字实现）
4. **缩放拖拽仅用 x 差值**：`_apply_resize(event.globalPosition().toPoint().x() - self.x())`，拖四角时统一按水平位移计算 scale，符合 brief 实现与 geometry 契约；非右下角拖动时方向体验略反直觉，属设计约定，非缺陷

---

## Fix Round 1 (Critical: 缩放拖拽数学失控)

**Finding**: `mouseMoveEvent` 缩放分支用 `event.globalPosition().toPoint().x() - self.x()` 作为 drag_dx。缩放锚点是窗口左上角（self.x() 全程不变），该值实为光标距窗口左缘的**绝对距离**，而 `scale_from_drag` 契约（Task 3 test_geometry.py 锁定）要求**移动增量**。实测反证：scale 1.0、窗口 100x100、光标移到局部 (145,95) 时 scale 算出 2.45（1.0+145/100），真机表现为拖一下窗口暴涨。

**修复**（几何契约零改动，只改调用点语义）：
1. `__init__` 新增 `self._resize_origin_global_x = 0`
2. `mousePressEvent` 命中角点时改调 `_begin_resize(corner)`，并记录 `self._resize_origin_global_x = event.globalPosition().toPoint().x()`（press 瞬间的增量基准）
3. `mouseMoveEvent` 缩放分支改为 `drag_dx = event.globalPosition().toPoint().x() - self._resize_origin_global_x`（纯增量）

**新测试** `test_resize_drag_incremental_scale`：走真实事件流（QTest 合成 press/move/release，offscreen 下 globalPosition 计算可靠，无需手动 QMouseEvent）。窗口 100x100、scale 1.0，右下角手柄命中区 (95,95) 按下，右移 50px 到局部 (145,95)，断言 `current_scale() ≈ 1.5`（approx 容差 0.1）且 `width() ≈ 150`。

**反证实验**：临时将 mouseMoveEvent 改回绝对距离语义，新测试失败（scale=2.45 ≠ 1.5±0.1），确认测试锁住了增量语义；改回后通过。

**测试结果**：`tests/test_window.py` 6 passed；全量 `tests/` 42 passed，无回归。原 `test_window_min_scale_after_resize_drag`（钳制单元测试）保持不变、仍通过。
