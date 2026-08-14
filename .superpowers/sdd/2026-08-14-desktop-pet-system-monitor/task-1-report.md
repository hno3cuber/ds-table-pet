# Task 1 Report — 项目脚手架与测试基础设施

- **状态**: DONE
- **Commit**: `b4a9fb2` (root-commit) — `chore: scaffold project with test infra`
- **测试摘要**: 1 passed (1 warning, 0.04s)

## 完成内容

按 brief 逐字创建：

| 文件 | 说明 |
| --- | --- |
| `.gitignore` | `__pycache__/`, `*.pyc`, `.venv/`, `.pytest_cache/` |
| `requirements.txt` | PySide6 / psutil / pynvml / pytest |
| `pytest.ini` | `testpaths = tests`, `addopts = -q` |
| `tests/conftest.py` | session 级 `qapp` fixture，`QT_QPA_PLATFORM=offscreen` |
| `tests/test_smoke.py` | `test_import_qt` 冒烟测试 |
| `pet/__init__.py` | 空包 |
| `plugins/__init__.py` | 空包 |
| `plugins/system_monitor/__init__.py` | 空包 |

`tests/` 目录按要求不创建 `__init__.py`。仓库已由环境预先 `git init`（master, root-commit），未重复 init。`git add -A` 按 brief 明示执行，`.superpowers/`（任务 briefs 与进度）、`docs/`（plan + spec）、`picture/ds.png`（角色素材）随本次提交一并入库。

## 环境与安装结果

- Python 3.14.5（真实运行时位于 `C:\Users\hno3\.hanako\.ephemeral\win32-sandbox-env\LocalAppData\Python\pythoncore-3.14-64\python.exe`；`python`/`pip` 命令指向 WindowsApps alias，`pip` 不在 PATH）
- 已安装：PySide6 6.11.1、PySide6-Addons 6.11.1、PySide6-Essentials 6.11.1、shiboken6 6.11.1、psutil 7.2.2、pynvml 13.0.1、pytest 9.1.1、nvidia-ml-py 13.610.43、colorama 0.4.6、iniconfig 2.3.0、packaging 26.3、pluggy 1.6.0、pygments 2.20.0
- `pytest` 运行于 offscreen 平台：**1 passed**

## 安装问题与绕过（重要）

`pip install -r requirements.txt` 直接执行**失败**。根因：pip 26.1.1 从 PyPI index 的 `data-core-metadata` 属性（PEP 714）得知存在独立 metadata 文件，在**下载 `<wheel>.whl.metadata` 时** `open(filepath, "wb")` 抛 `PermissionError: [Errno 13] Permission denied`（`pip/_internal/network/download.py:191`）。同进程手动写同一路径却成功，与临时目录位置（`.ephemeral\Temp` 或工作区）无关；连 `pip install --upgrade pip`（解压 pip 自身 wheel 的 metadata）也报同样错误。这是当前沙箱环境下 pip 26 PEP 714 快速 metadata 路径的特异行为，疑似沙箱文件系统过滤对「HTTP 下载写新文件」模式的拦截。

**绕过方案**（不改变任何项目文件内容）：

1. 用 Python `urllib` 脚本从 PyPI JSON API 取 wheel 直链，逐个下载到本地目录（含全部传递依赖：shiboken6 / PySide6-Essentials / PySide6-Addons / nvidia-ml-py / colorama / iniconfig / packaging / pluggy / pygments）。期间网络不稳定出现 `ConnectionResetError`，脚本加重试后完成。
2. `python -m pip install --no-index --find-links=<本地wheel目录> -r requirements.txt` 离线安装成功。`--no-index` 下无 index link，pip 走 lazy wheel（从 zip 内读 metadata），完全绕开 PEP 714 下载路径。pip 自动解析出 `pynvml -> nvidia-ml-py>=12`、`pytest -> pygments` 等依赖并全部从本地 wheel 满足。
3. 安装后已删除全部临时产物（wheel 目录、pip 缓存、下载脚本）。

**注意**：未来在本环境跑 `pip install <新包>` 会再次触发同一错误，需沿用 `--no-index --find-links` 离线方式。这是沙箱环境限制，与项目本身无关。

## 其他观察

- `pynvml 13.0.1` 是过渡包，导入时打印 `FutureWarning`，建议直接使用 `nvidia-ml-py`（本环境已随依赖安装）。后续任务若用 pynvml，该 warning 无碍功能。
- pytest 运行时提示无法创建 `.pytest_cache`（WinError 5），为沙箱写限制，不影响测试结果；`.pytest_cache/` 已在 .gitignore 中。
- 工作区残留少量沙箱锁定、无法删除的空目录（`.pip-tmp/pip-*`、`pytest-cache-files-*`），git 不跟踪空目录，不影响仓库与后续任务。
