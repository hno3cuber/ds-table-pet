# Task 5 Report — CPU/GPU 采集器 plugins/system_monitor/collector.py

- **状态**: DONE
- **Commit**: `321ac7f` — `feat: cpu/gpu collector thread with psutil and pynvml`（严格只含 brief 指定的 2 个文件：`plugins/system_monitor/collector.py` + `tests/test_collector.py`）
- **测试摘要**: `tests/test_collector.py` **5 passed**；全量 `pytest` **21 passed**（Task 1 冒烟 2 + Task 2 config 4 + Task 3 geometry 5 + Task 4 plugins 6 + Task 5 collector 5，无回归）

## 完成内容

| 文件 | 说明 |
| --- | --- |
| `plugins/system_monitor/collector.py` | `CpuGpuCollector(interval_s=1.0)`：daemon 线程 `_loop` 按 interval 循环 `_update()`；`_snapshot` 由 `threading.Lock` 保护，`snapshot()` 返回 `dict(_snapshot)` 拷贝（线程安全）；`read_cpu()` 用 `psutil.cpu_percent(interval=None)`；`read_gpu()` 用 pynvml（惰性 init + 取 index 0 设备 util.gpu），异常兜底返回 `(0.0, False)`；`start()` 幂等（已存活线程不重启），`_loop` 进入循环前先 `read_cpu()` 预热规避 psutil 首调返回 0；`stop()` set event + join(timeout=2.0) |
| `tests/test_collector.py` | brief 原样 5 个测试：`test_update_writes_snapshot`、`test_gpu_failure_reported`、`test_snapshot_is_copy`、`test_start_stop_lifecycle`、`test_read_gpu_returns_false_on_error`；全部 monkeypatch 注入假数据，不依赖真实硬件 |

Step 顺序按 brief：先写失败测试 → 运行确认 `ModuleNotFoundError: No module named 'plugins.system_monitor.collector'`（1 error during collection）→ 实现 → 5 passed。

## 运行方式

沿用 Task 1-4 验证过的命令模板（pytest 用 `python -m pytest` 调用，工作区内唯一 basetemp + 禁 cacheprovider；本任务沙盒 Python 已在 PATH 中，无需再 prepend）：

```powershell
python -m pytest tests/test_collector.py -v --basetemp="F:\beifen\hanako\桌宠\.pytest-tmp-$PID" -p no:cacheprovider
```

## Concerns / 偏离说明

- **brief 测试与实现代码存在直接冲突，按测试为准做了最小偏离（唯一一处非逐字实现）**：
  - `tests/test_collector.py::test_start_stop_lifecycle` 断言 `stop()` **之后** `c._thread is not None` 且 `not c._thread.is_alive()`；而 brief 的 collector 实现里 `stop()` 末尾执行 `self._thread = None`，与测试断言矛盾（实测 4 passed / 1 failed）。
  - 处理：保留 brief 测试原文不动（Step 4 期望 5 passed 是验收标准），实现改为 `stop()` join 后**保留** `_thread` 引用（仅去掉置 None 一行，代码内加注释说明）。功能不受影响：`start()` 以 `is_alive()` 判断，已结束线程会正常重建，`_stop` event 每次 start 前 clear。
  - 若后续 review 认为应以 brief 实现原文为准，则需同步改测试断言，二者不能同时保留。
- **pynvml FutureWarning**：`import pynvml` 触发 `FutureWarning: The pynvml package is deprecated. Please install nvidia-ml-py instead.`。属包层面提示（Task 1 已装 pynvml，brief 依赖即 pynvml），仅 warning 不影响功能，未处理。
- **LF→CRLF 提示**：git 警告 working copy 中 LF 将被替换为 CRLF，与既有文件行为一致，无影响。
- **环境坑沿用**：`git -C` 规避中文路径 cd；`git add` 精确路径只暂存 2 个目标文件；PowerShell 5.1 不支持 `&&`，命令用 `;` 串联。

## 验证记录

- Step 2 失败确认：`ModuleNotFoundError: No module named 'plugins.system_monitor.collector'`（1 error during collection），符合 brief 预期。
- Step 4 通过确认：`tests/test_collector.py ..... [100%]`，`5 passed in 0.13s`。
- 全量回归：`21 passed in 0.25s`。
- 提交内容核验：`git show --stat HEAD` 显示仅 `plugins/system_monitor/collector.py`（+70）+ `tests/test_collector.py`（+37），共 2 文件 107 insertions。
