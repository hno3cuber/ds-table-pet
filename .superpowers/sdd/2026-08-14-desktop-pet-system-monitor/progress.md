# SDD ledger — plan: docs/superpowers/plans/2026-08-14-desktop-pet-system-monitor.md

## Setup notes
- 目录非 git 仓库，Task 1 内 `git init`（主工作台直接开发，无 worktree；用户主工作台即此目录）
- 沙盒无法运行 bash 辅助脚本，controller 用 PowerShell 手动完成：task brief 提取、review package 生成
- 无可用子代理 roster，implementer/reviewer 均用会话默认模型

## Preflight scan (interfaces shared across tasks)
| Task pair | Produces → Consumes | Finding |
|---|---|---|
| T2 → T9/T10 | Config.get/set/save → 窗口尺寸位置/插件装配 | clean |
| T3 → T7/T9 | scaled_size/scale_from_drag → ActorWidget/PetWindow | clean |
| T4 → T6/T10 | Plugin/PluginManager(factory) → SystemMonitorPlugin(interval_ms)/install_plugins | clean |
| T5 → T6 | CpuGpuCollector → poll() | clean |
| T7 → T9 | ActorWidget(handle_at/set_resize_mode/current_scale) → PetWindow | clean |
| T8 → T9 | HudPanel(add_block/set_scale/fade_in/out/show_paused) → PetWindow | clean |
| T9 → T10 | PetWindow(install_plugin/set_paused/current_pos/current_scale) → main.py | clean |
| T1 → all | conftest qapp fixture → GUI 测试 | clean |
- 计划文本内部自洽（每任务测试与其代码一致）；无冲突需裁定

## Task log
