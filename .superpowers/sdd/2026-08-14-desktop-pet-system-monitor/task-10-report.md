# Task 10 报告：入口与装配 main.py

**状态:** DONE
**Commit:** `35aa2ba` (feat: main entry with plugin assembly and state persistence)
**日期:** 2026-08-14

## 交付物

- `main.py`（新建）：`load_pixmap`（缺失报错）、`build_window`、`install_plugins`（PluginManager factory 将 `config["refresh_interval_ms"]` 传给 `system_monitor` 插件构造）、`save_state`（pos + scale 写回 config）、`main()`、`_StateSaver` eventFilter。
- `tests/test_main.py`（新建）：brief 全部 4 条测试。

## 执行摘要

| 步骤 | 结果 |
| --- | --- |
| Step 1 写失败测试 | ✅ `tests/test_main.py` 4 条测试（brief 完整代码） |
| Step 2 确认失败 | ✅ `ModuleNotFoundError: No module named 'main'`，与 brief 预期一致 |
| Step 3 实现 main.py | ✅ 按 brief 逐字落地 |
| Step 4 确认通过 | ✅ `4 passed`（单独跑）；全量 `46 passed, 1 warning` |
| Step 5 真机冒烟 | ✅ 构造链路冒烟完成（见下）；完整 `app.exec()` 真机验收**留待 Task 11** |
| Step 6 Commit | ✅ `35aa2ba`，精确 add `main.py`、`tests/test_main.py` |

## 测试摘要

- `tests/test_main.py`：`4 passed`（`test_main_loads_pixmap` / `test_build_window_from_config` / `test_close_saves_position_and_scale` / `test_install_plugins_passes_interval`）
- 全量：`46 passed, 1 warning`（warning 为 pynvml 弃用提示，已知噪音）
- 运行命令：`python -m pytest --basetemp="F:\beifen\hanako\桌宠\.pytest-tmp-$PID" -p no:cacheprovider -p no:cacheprovider`

## 真机冒烟（offscreen 构造链路，未 exec）

沙盒 offscreen 环境无法完成完整 `python main.py`（窗口无法显示、`app.exec()` 阻塞），按约定做构造链路冒烟并如实记录：

```
config on disk before: False        # Config 只读构造，不落盘
pixmap: 910x941 null=False          # load_pixmap 成功加载 picture/ds.png
window: 910x941 scale=1.00 pos=[100, 100]   # build_window 成功
discovered plugins: []              # ⚠️ 见 concerns #1
hud layout count: 1                 # 插件数据块未挂载
config on disk after: False         # 全程未写 config.json
SMOKE DONE
```

`main.py` 的 import、加载、窗口构造、插件装配、状态保存链路在 offscreen 下全部可运行；`install_plugins` 的 factory 传参逻辑由测试覆盖。真机验收（透明显示、HUD 刷新、拖拽/缩放/暂停、重启恢复）留待 Task 11。

## 对 brief 代码的两处偏差说明

1. **`test_main_loads_pixmap` 追加 `qapp` 参数**（其余代码逐字采用）。brief 原代码不带 `qapp`；但 QPixmap 在无 QApplication 时于 offscreen/Windows 直接 fail-fast（0xC0000409 崩溃，已最小复现验证）。`tests/test_main.py` 单独运行时该测试是首个执行，进程内尚无 QApplication，必崩。追加 `qapp` 后（其复用进程级 QApplication 实例，语义正确且与其他三测一致）测试稳定通过。**全量跑时不受影响**（qapp 为 session scope，先由其他测试创建后复用）。
2. **追加测试内乱码注释**（"用临时假插件目录，避免依赖真实 system_monitor 初始化"）恢复为正确 UTF-8 中文；代码本体逐字采用。

## Concerns

### #1（高优先级，影响 Task 11 真机验收）插件发现契约冲突：真实 system_monitor 插件无法被 discover 发现

**现象**：冒烟中 `PluginManager("plugins", ...).discover()` 返回空列表，HUD 未挂载 CPU/GPU 数据块。

**根因**（已实证）：`pet/plugins.py` 的 `discover()` 仅识别模块导出的 `PluginClass`（`getattr(module, "PluginClass", None)`，Task 4 brief 明确约定"模块内类名 PluginClass"）；而 `plugins/system_monitor/plugin.py` 导出的是 `SystemMonitorPlugin`（Task 6 brief 与 spec §5.5 均如此命名）。两任务 brief 的接口契约在计划层面未对齐，实现各自忠实于自己的 brief，导致真实插件被 `continue` 跳过（实证输出：`module exports PluginClass: False` / `exports SystemMonitorPlugin: True`）。`test_plugins.py` 的假插件均用 `PluginClass` 命名，故既有测试全绿，掩盖了此问题。

**建议修复**（Task 11 前处理，二选一）：
- 最小改动：`plugins/system_monitor/plugin.py` 末尾加一行 `PluginClass = SystemMonitorPlugin`（符合 Task 4 契约，不破坏 Task 6 接口，`test_system_monitor_plugin.py` 直接 import 类名不受影响）；
- 或改 `discover()` 兼容"模块内唯一 Plugin 子类"。

**本次未修**：修复涉及 `pet/plugins.py` 或 `plugins/` 下文件，超出本任务 git add 边界（`main.py`、`tests/test_main.py`），且不属本任务 brief 明示范围，故如实上报。

### #2（低）pynvml 弃用警告

`plugins/system_monitor/collector.py:5` 的 `import pynvml` 触发 FutureWarning（建议改用 nvidia-ml-py）。纯噪音，不影响功能，未处理。

### #3（信息）progress.md 与本任务无关的变更

`git status` 显示 `.superpowers/sdd/.../progress.md` 有未提交修改，非本任务所为，未纳入本次 commit。

---

## Fix Round 1（审查 Critical 修复）

**状态:** DONE
**Commit:** `35aa2ba` 之后追加（见文末 commit 记录）

**背景**：审查确认 concerns #1（插件导出契约冲突）为 Critical，影响 Task 11 真机验收第 3/4 条。按审查者认可的方案修复。

### 修复内容

1. **`plugins/system_monitor/plugin.py`**：文件末尾追加 `PluginClass = SystemMonitorPlugin`（别名）。SystemMonitorPlugin 类名保持不动（spec/Task 6 命名），别名对齐 Task 4 的 discover 契约（模块内导出 PluginClass）。
2. **`tests/test_main.py`**：追加 `test_install_plugins_discovers_real_monitor` —— 真实装配集成测试，直接调用 `main.install_plugins`（覆盖此前 install_plugins 本体无测试触达的缺口）：断言真实 plugins 目录被 discover 且仅 1 个实例、id 为 system_monitor、interval_ms 从 config 透传（750）、HUD 布局挂上数据块；`finally` 中 `mgr.stop_all()` 收尾停采集线程。

### 验证

- `tests/test_main.py` + `tests/test_plugins.py`：`11 passed`
- 全量回归：**`47 passed, 1 warning`**（warning 为 pynvml 弃用提示，已知噪音；与预期 47 passed 一致）
- 冒烟复验（offscreen 构造链路）：

```
discovered plugins: ['system_monitor']   # 修复前为 []
interval_ms: 750                        # config 透传生效
hud layout count: 2                     # paused 标签 + 数据块
config on disk: False                   # 全程不落盘
SMOKE RE-VERIFY OK
```

修复前 `discovered plugins: []`，修复后 `['system_monitor']`，契约冲突消除，HUD 可挂载 CPU/GPU 数据块。
