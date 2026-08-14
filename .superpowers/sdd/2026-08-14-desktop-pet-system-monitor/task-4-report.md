# Task 4 Report — 插件接口与插件管理器 pet/plugin.py + pet/plugins.py

- **状态**: DONE
- **Commit**: `a4cc2fd` — `feat: plugin ABC and directory-based plugin manager`（严格只含 brief 指定的 3 个文件：`pet/plugin.py` + `pet/plugins.py` + `tests/test_plugins.py`）
- **测试摘要**: `tests/test_plugins.py` **5 passed**；全量 `pytest` **15 passed**（Task 1 冒烟 2 + Task 2 config 4 + Task 3 geometry 5 + Task 4 plugins 5，无回归）

## 完成内容

按 brief 逐字实现（仅两处编码层面还原，见下）：

| 文件 | 说明 |
| --- | --- |
| `pet/plugin.py` | `Plugin(ABC)`：类属性 `id: str`、`name: str`；抽象方法 `start()/stop()/poll() -> dict/panel(parent)`；`set_paused(paused)` 提供默认空实现 |
| `pet/plugins.py` | `PluginManager(plugins_dir, enabled=None, factory=None)`：`discover()` 扫描 `plugins_dir` 下含 `plugin.py` 的子目录，经 `importlib.util.spec_from_file_location` 动态加载，约定类名 `PluginClass` 且必须 `issubclass(Plugin)`，否则跳过；`enabled=None` 加载全部、否则按 `inst.id` 过滤；`factory` 可调用（`callable(plugin_class) -> Plugin`），默认为 `plugin_class()`；`start_all()/stop_all()` 对 `self.instances` 依次调用 |
| `tests/test_plugins.py` | brief 原样 5 个测试：`test_discover_loads_all`、`test_enabled_filter`、`test_skips_non_plugin_module`、`test_start_all_calls_each`、`test_factory_customizes_construction`；`tmp_path` 由 `tests/conftest.py` 的 mode=0o777 修复可用 |

Step 顺序均按 brief：先写失败测试 → 运行确认 `ModuleNotFoundError: No module named 'pet.plugin'`（1 error during collection）→ 实现 → 5 passed。

## 运行方式

沿用 Task 1-3 验证过的命令模板（沙盒 Python 入 PATH + 工作区内唯一 basetemp + 禁 cacheprovider；pytest 用 `python -m pytest` 调用）：

```powershell
$env:PATH = "C:\Users\hno3\.hanako\.ephemeral\win32-sandbox-env\LocalAppData\Python\pythoncore-3.14-64;" + $env:PATH
python -m pytest tests/test_plugins.py -v --basetemp="F:\beifen\hanako\桌宠\.pytest-tmp-$PID" -p no:cacheprovider
```

## 本任务特殊说明

- **brief 文件 mojibake 还原**：`task-4-brief.md` 内容存在编码错乱（UTF-8 字节被按 GBK 误读，如 `name = "鍋囨彃浠?`）。经验证，`"鍋囨彃浠?"` 正是 `"假插件"` 的 UTF-8 字节（E5 81 87 E6 8F 92 E4 BB B6）按 GBK 解码的结果，故在测试源中还原为 `name = "假插件"`。该字段未被任何断言引用，两种写法测试结果等价。
- **测试数量口径**：brief Step 4 注为「Expected: 4 passed」，但 brief 测试代码实含 5 个测试（含 factory 测试），按实际代码与任务说明以 **5 passed** 为准。
- **无新依赖**：纯标准库（`abc` / `importlib.util` / `pathlib`），无 pip install。
- **`import sys`、`import pytest` 未使用**：brief 测试代码原样保留，仅潜在 lint 提示，不影响运行。
- **既有坑沿用**：`git -C` 规避中文路径 cd；`git add` 用精确路径只暂存 3 个目标文件；`.pip-tmp/`、`pytest_tmp/` 等 0o700 残留目录的 `Permission denied` 属只读警告；LF→CRLF 提示与既有文件行为一致。

## 验证记录

- Step 2 失败确认：`ModuleNotFoundError: No module named 'pet.plugin'`（1 error during collection），符合 brief 预期。
- Step 4 通过确认：`tests/test_plugins.py ..... [100%]`，`5 passed in 0.07s`。
- 全量回归：`15 passed in 0.11s`。
- 提交内容核验：`git show --stat HEAD` 显示仅 `pet/plugin.py`（+25）、`pet/plugins.py`（+41）、`tests/test_plugins.py`（+87），共 3 文件 153 insertions。

## Fix Round 1（2026-08-14）— 坏插件隔离

- **审查发现（Important）**：`spec.loader.exec_module(module)` 无异常保护。含语法错误/模块级异常的 plugin.py 会让整个 `discover()` 抛出，其余正常插件全部加载失败，一个坏插件拖垮全体。
- **修复**：`pet/plugins.py` 的 `discover()` 中用 `try/except Exception`（非 bare except）包住 `exec_module`、`PluginClass` 获取/校验及 `factory` 构造整段；任何异常（SyntaxError、ImportError、运行时异常、构造异常）打印 `[plugin] skip broken plugin: {entry.name}: {e}` 到 stderr 并 `continue`，不影响后续插件。
- **新测试**：`tests/test_plugins.py::test_skips_broken_plugins` — 同目录放置语法错误插件（`def broken(:`）与模块级抛异常插件（`raise RuntimeError('boom')`）各一，另加正常插件 `fake_one`（sorted 顺序：坏插件在正常插件前后各一），断言 `discover()` 不抛异常且返回 `["fake_one"]`，加载顺序不受坏插件影响。
- **验证**：
  - `python -m pytest tests/test_plugins.py -v` → `6 passed in 0.13s`（新增 1 个）
  - 全量回归 → `16 passed in 0.16s`（Task 1-4 + 新测试，无回归）
- **Commit**：`fix: isolate broken plugins in discover`（见下）
