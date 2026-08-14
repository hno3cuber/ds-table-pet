# Task 3 Report — 缩放几何计算 pet/geometry.py

- **状态**: DONE
- **Commit**: `b19d895` — `feat: aspect-locked scale geometry helpers`（严格只含 brief 指定的 2 个文件：`pet/geometry.py` + `tests/test_geometry.py`）
- **测试摘要**: `tests/test_geometry.py` **5 passed**；全量 `pytest` **10 passed**（Task 1 冒烟 2 + Task 2 config 4 + Task 3 geometry 5，无回归）

## 完成内容

按 brief 逐字实现：

| 文件 | 说明 |
| --- | --- |
| `pet/geometry.py` | `scaled_size(orig_w, orig_h, scale)`：四舍五入取整、`max(1, ...)` 保底 1px；`scale_from_drag(orig_w, drag_dx, current_scale, min_scale=0.3)`：比例由横向位移驱动（`current_scale + drag_dx / orig_w`），`max(min_scale, ...)` 低于 0.3 时钳制 |
| `tests/test_geometry.py` | brief 原样：四舍五入、1px 保底、正向拖拽增大、负向拖拽减小、最小值钳制共 5 个测试 |

Step 顺序均按 brief：先写失败测试 → 运行确认 `ModuleNotFoundError: No module named 'pet.geometry'` → 实现 → 5 passed。

## 运行方式

沿用 Task 1/2 验证过的命令模板（沙盒 Python 入 PATH + 工作区内唯一 basetemp + 禁 cacheprovider；pytest 本体用 `python -m pytest` 调用，因为 pytest 可执行入口不在 PATH，而解释器本体在沙盒 PATH 中）：

```powershell
$env:PATH = "C:\Users\hno3\.hanako\.ephemeral\win32-sandbox-env\LocalAppData\Python\pythoncore-3.14-64;" + $env:PATH
python -m pytest tests/test_geometry.py -v --basetemp="F:\beifen\hanako\桌宠\.pytest-tmp-$PID" -p no:cacheprovider
```

## 本任务特殊说明

- **无新依赖**：纯标准库（`round` / `max`），无 pip install。
- **无新环境坑**：Task 2 的 `tmp_path` 0o700 问题已由 `tests/conftest.py` 修复覆盖（本任务测试不用 `tmp_path`，未触发）；basetemp 按规范用 `$PID` 后缀保持唯一，遗留目录 `\.pytest-tmp-*` 为空目录不被 git 跟踪，不影响仓库。
- **沙盒权限噪音**：`git status` 对 `.pip-tmp/`、`pytest_tmp/`、`exp_tmp/` 等历史 0o700 残留目录报 `Permission denied`，与 Task 1/2 同类，属只读警告，不影响操作；commit 采用 `git add <精确路径>` 只暂存目标文件，规避了这些目录。
- **中文路径 shell 坑**：PowerShell 下 `cd "F:\beifen\hanako\桌宠"` 后执行 git 报「系统找不到指定的路径」（中文路径解析异常），改用 `git -C "F:\beifen\hanako\桌宠"` 形式（不含中文 cd）即正常。后续任务建议统一用 `git -C`。
- **LF→CRLF 警告**：commit 时提示 `LF will be replaced by CRLF`，仓库无 `.gitattributes` 强制规范，与既有文件行为一致，仅提示不构成问题。

## 验证记录

- Step 2 失败确认：`ModuleNotFoundError: No module named 'pet.geometry'`（1 error during collection），符合 brief 预期。
- Step 4 通过确认：`tests/test_geometry.py ..... [100%]`，`5 passed in 0.03s`。
- 全量回归：`10 passed in 0.06s`。
- 提交内容核验：`git show --stat HEAD` 显示仅 `pet/geometry.py`（+6）与 `tests/test_geometry.py`（+22），工作区 `pet/`、`tests/` 干净。
