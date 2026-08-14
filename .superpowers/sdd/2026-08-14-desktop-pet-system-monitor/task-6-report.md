# Task 6 Report: 系统监控插件本体

- **状态**: DONE
- **Commit**: `0d29812` (`feat: system monitor plugin with poll/panel/pause`)
- **文件**:
  - 新建 `plugins/system_monitor/plugin.py`
  - 新建 `tests/test_system_monitor_plugin.py`

## 测试摘要

| 测试 | 结果 |
|---|---|
| `test_plugin_metadata` | PASS |
| `test_poll_returns_snapshot_shape` | PASS |
| `test_panel_creates_widget` | PASS |
| `test_refresh_updates_labels` | PASS |
| `test_pause_shows_paused_state` | PASS |
| `test_interval_ms_from_constructor` | PASS |

- 本任务测试: **6 passed**（brief 中「Expected: 5 passed」与实际测试代码不符；实际包含 6 个用例，含 `interval_ms` 测试，以测试代码为准）
- 全量回归: **27 passed**（`python -m pytest --basetemp=... -p no:cacheprovider`，offscreen 平台）
- 唯一 warning: `pynvml` 包已弃用的 FutureWarning（来自 Task 5 的 collector，非本任务引入）

## 实现要点

- `SystemMonitorPlugin(Plugin)`，`id="system_monitor"`、`name="系统监控"`（brief 文件为 GBK/UTF-8 mojibake，已按规格还原中文字符串）
- 构造仅创建 collector 对象与空状态，不启动任何资源（不启动采集线程、不创建 QTimer）
- `start()` 启动 collector + 以 `interval_ms` 驱动的 QTimer 调 `_refresh`；`stop()` 停止两者
- `poll()` 委托 `collector.snapshot()`（线程安全快照）
- `panel()` 返回 QVBoxLayout 两行 QLabel（`CPU x%` / `GPU x%` 或 `GPU 不可用`），深色半透明风格面板
- `set_paused(True)` 停 QTimer、标签显示「已暂停」；恢复后重启 QTimer 并刷新
- `_refresh()` 在标签未创建时安全跳过

## Concerns

1. **对 brief 代码的最小偏离**：brief 的测试 `test_pause_shows_paused_state` 直接丢弃 `panel(None)` 返回值；而 brief 的插件代码不持有面板控件，顶层 QWidget 随即被 GC 销毁，连带 QLabel 的 C++ 对象失效，`set_paused` 抛 `RuntimeError: Internal C++ object already deleted`（实测复现，5 过 1 挂）。按 brief 规格意图（暂停/恢复需更新标签），在插件中持有 `self._widget` 引用，使面板随插件存活。这是使 brief 自身测试通过所需的最小改动，已在插件代码内注释说明。
2. `set_paused(False)` 恢复时 QTimer 以固定 `1000` 重启（brief 原文如此），未使用 `self.interval_ms`；若插件以非默认间隔构造，暂停恢复后间隔会漂移。属 brief 明示行为，未改动，仅记录。
3. `from PySide6.QtCore import Qt, QTimer` 中 `Qt` 未使用（brief 原文如此），保留未动。

## Fix Round 1（代码审查修复）

- **发现（Important）**: `set_paused(False)` 恢复分支用 `self._timer.start(1000)` 固定值，与 `start()` 的 `self._timer.start(self.interval_ms)` 矛盾；以 `interval_ms=500` 构造的插件暂停恢复后刷新间隔静默变回 1000ms。审查者判定为模板笔误（非 brief 设计意图）。
- **修复**: `set_paused(False)` 改为 `self._timer.start(self.interval_ms)`，两条启动路径统一。
- **测试补强**（审查者 Minor 建议）: `test_pause_shows_paused_state` 现以 `interval_ms=500` 构造并预置激活的 QTimer（不启动真实 collector 线程，不依赖硬件），断言：暂停后 `p._timer.isActive() is False`、两标签文本均为「已暂停」；恢复后 `_paused is False` 且 `p._timer.isActive() is True`（验证恢复用自定义间隔重启）。
- **验证**: 本任务 6 passed；全量回归 27 passed，无新 warning。
- **Commit**: `fix: honor interval_ms when resuming from pause`
