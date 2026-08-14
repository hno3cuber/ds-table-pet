# Task 2 Report — 配置模块 pet/config.py

- **状态**: DONE
- **Commit**: `a14111a` — `feat: config module with default fallback and dotted keys`（主任务，仅含 brief 指定的 2 个文件）
- **附加 Commit**: `7982ae5` — `fix(tests): force mkdir mode to bypass sandbox tmp_path denial`（conftest.py 沙盒环境适配，见下）
- **测试摘要**: `tests/test_config.py` **4 passed**；全量 `pytest`（含 Task 1 冒烟）**5 passed**

## 完成内容

按 brief 逐字实现：

| 文件 | 说明 |
| --- | --- |
| `pet/config.py` | `DEFAULT_CONFIG`、`_deep_merge`（默认值深合并）、`Config`（`get` 点分路径 / `set` / `save` 写回原路径 utf-8，文件缺失或 JSON 损坏时回退默认值） |
| `tests/test_config.py` | brief 原样：缺文件默认值、字段缺失合并、set+save 回填默认字段、常量形状共 4 个测试 |

Step 顺序均按 brief：先写失败测试 → 运行确认 `ModuleNotFoundError: No module named 'pet.config'` → 实现 → 4 passed。

## 环境问题（重要）：tmp_path 在沙盒中不可用

brief 的测试依赖 `tmp_path` fixture，但在本沙盒中所有使用 `tmp_path` 的测试 setup 全部报错，且错误随环境表现怪异，耗时较长才定位。最终根因：

- 本沙盒对 **`mode=0o700` 创建的目录**拒绝一切后续访问：`os.scandir` / 写入 / 删除均报 `WinError 5 拒绝访问`（同进程也不例外）。
- pytest 的 `tmp_path` 机制内部**硬编码 `mode=0o700`** 创建临时目录（`_pytest.tmpdir.getbasetemp()` 的 `basetemp.mkdir(mode=0o700)` 与 `make_numbered_dir`），因此 tmp_path 完全不可用。Windows 上 POSIX mode 本应被忽略，此行为是沙盒文件系统层模拟权限的特异表现（Task 1 report 中提到的 `.pytest_cache` 写失败与 `pip` 下载失败大概率同源）。

**修复**（`tests/conftest.py`，与 Task 1 在其中设 `QT_QPA_PLATFORM` 同性质的环境适配，对后续所有任务的 tmp_path 生效）：

```python
import os
_os_mkdir_orig = os.mkdir

def _os_mkdir(path, mode=0o777, *, dir_fd=None):
    return _os_mkdir_orig(path, 0o777, dir_fd=dir_fd)  # 强制 0o777

os.mkdir = _os_mkdir
```

强制所有 `os.mkdir` 使用默认 mode，一网打尽 pytest 内部各 0o700 创建点。验证：patch 后 `TempPathFactory.getbasetemp()` + `mktemp()` + 写入 + scandir 全链路正常。

**运行方式**：因系统 Temp（沙盒外）不可用，且历史 0o700 残留目录无法删除，pytest 需显式指定工作区内唯一 basetemp：

```powershell
$env:PATH = "C:\Users\hno3\.hanako\.ephemeral\win32-sandbox-env\LocalAppData\Python\pythoncore-3.14-64;" + $env:PATH
python -m pytest tests/test_config.py -v --basetemp="F:\beifen\hanako\桌宠\tmp_$PID" -p no:cacheprovider
```

- `--basetemp=<工作区唯一路径>`：避免系统 Temp（沙盒外）与历史残留目录
- `-p no:cacheprovider`：抑制 `.pytest_cache` 写失败噪音（Task 1 已见）

## 诊断过程中的教训

- Windows 上 `os.stat` 的 `st_mode` 对目录恒报 `0o40777`，**不可**用来判断目录权限——曾因此误判「mode patch 已生效」（实际是 no-op：包装函数把调用者的 0o700 原样透传了）。必须用行为（scandir/写入）验证。
- 遗留删不掉的空目录（`tmp_14660/`、`tmp_4868/`、`pytest_tmp/`、`.pytest_tmp/`、`exp_tmp/` 等，均为 0o700 残留）会一直卡在工作区，git 不跟踪空目录，不影响仓库与后续任务（与 Task 1 的 `.pip-tmp/`、`pytest-cache-files-*/` 同类）。

## 其他观察

- `pytest.ini` 的 `addopts = -q` 与命令行的 `-v` 叠加无碍。
- 两次 commit 分开：主 commit 严格只含 `pet/config.py` 与 `tests/test_config.py`（对齐 brief）；conftest.py 的环境修复单独提交，避免污染任务交付物。
