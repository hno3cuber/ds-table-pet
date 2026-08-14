# Task 11 报告：全量验收与收尾

**状态:** DONE
**Commit:** `352ebb9` (docs: plan completion and acceptance record)
**日期:** 2026-08-14

## 执行摘要

| 步骤 | 结果 |
| --- | --- |
| Step 1 全量测试 | ✅ `54 passed`（brief 预期 43 已过时；验收前基线为 47，修复后新增 7 条回归测试） |
| Step 2 八条验收 | ✅ 第 7、8 条沙盒冒烟验证通过；第 1-6 条依赖真实显示器与真人操作，**标注「待用户真机验收」，未在沙盒假装执行** |
| Step 3 修复验收发现的问题 | ✅ 两处修复（`pet/config.py` 配置类型级兜底、`collector.py` 采集线程防异常）并重跑全量 |
| Step 4 最终提交 | ✅ `352ebb9`，精确 add 7 个文件 |

## 测试摘要

- **验收前基线**：`47 passed`（各任务轮次累计新增，brief 中 "= 43 passed" 为过时数字，以实际运行为准）
- **最终全量**：`54 passed`，exit 0（`47 基线 + 7 本轮新增回归测试`）
- 分布（collect-only 实测）：
  - `test_actor.py: 5`、`test_collector.py: 6`（+1）、`test_config.py: 7`（+3）、`test_geometry.py: 5`、`test_hud.py: 4`、`test_main.py: 7`（+2）、`test_plugins.py: 6`、`test_smoke.py: 1`、`test_system_monitor_plugin.py: 7`（+1）、`test_window.py: 6`
- 命令：`python -m pytest --basetemp="F:\beifen\hanako\桌宠\.pytest-tmp-$PID" -p no:cacheprovider`
- 已知警告：`collector.py:5` pynvml 弃用 FutureWarning（历史噪音，不影响功能）

## Step 2 八条验收明细

| # | 条目 | 结果 |
| --- | --- | --- |
| 1 | 透明底正确显示，无黑/白底块 | ⏳ 待用户真机验收（offscreen 无法验证真实透明） |
| 2 | 拖拽移动跟随 | ⏳ 待用户真机验收 |
| 3 | 悬停面板淡入，CPU%/GPU% 每秒刷新，移开淡出 | ⏳ 待用户真机验收 |
| 4 | 右键菜单三项齐全；暂停后数字停止刷新；恢复继续 | ⏳ 待用户真机验收 |
| 5 | 调整大小：角点框出现，锁比例缩放，松手生效 | ⏳ 待用户真机验收 |
| 6 | 重启后尺寸与位置保持 | ⏳ 待用户真机验收 |
| 7 | 改坏 config.json 字段值后启动不崩溃，默认值兜底 | ✅ 沙盒冒烟通过（详见下） |
| 8 | GPU 读不到时不崩溃，显示「GPU 不可用」 | ✅ 沙盒 monkeypatch 冒烟通过（详见下） |

> 第 1-6 条需要真实显示器、鼠标交互与真人目测，本沙盒 offscreen 环境无法执行。**未做任何「目测通过」的伪装**，请在真机按设计文档 §11 逐条核对（启动方式 `python main.py`）。

### 第 7 条冒烟（坏 config 兜底）

构造链路：坏 `config.json` → `Config` → `build_window(PetWindow)` → `install_plugins`，坏值为 `{"window": {"scale": "abc", "pos": "oops"}, "refresh_interval_ms": -5, "enabled_plugins": null}`。

**修复前（如实记录的失败证据）**：
```
CFG scale='abc' pos='oops' interval=-5 enabled=None
SMOKE7 RESULT: RAISED
ValueError: could not convert string to float: 'abc'   # pet/window.py:15
```
即 `Config.get` 只对「键缺失」兜底，对「键存在但类型错误」原样放行，`PetWindow` 构造即崩。

**修复后**：
```
CFG scale=1.0 pos=[100, 100] interval=1000 enabled=['system_monitor']
build_window OK, scale=1.00 pos=[100, 100]
install_plugins OK, instances=['system_monitor']
SMOKE7 RESULT: PASS
```

### 第 8 条冒烟（GPU 不可用）

monkeypatch `collector.read_gpu` 为抛异常版本（模拟 GPU 读不到），走真实数据路径 `_update()` 与 UI 路径 `_refresh()`。

**修复前（collector 层失败证据）**：
```
collector._update RAISED: RuntimeError: gpu read failed (simulated)
SMOKE8 RESULT: FAIL (collector thread would die)
```
UI 层（经 `snapshot`）本就能显示「GPU 不可用」，但采集线程遇异常会静默死亡，CPU 刷新随之冻结。

**修复后**：
```
collector._update survived; snap={'cpu': 43.8, 'gpu': 0.0, 'gpu_ok': False}
labels=['CPU 44%', 'GPU 不可用']
SMOKE8 RESULT: PASS
```

## Step 3 修复内容

### 1. `pet/config.py`：配置类型级兜底（+42 行）

问题：`Config` 对错误类型的字段值无兜底，`scale="abc"` 在 `PetWindow.__init__` 的 `float(...)` 处抛 `ValueError`；`pos="oops"` 会在 `move(pos[0], pos[1])` 处抛 `TypeError`；`refresh_interval_ms=-5` 会作为负间隔传给 `QTimer.start`；`enabled_plugins=null` 会绕过默认过滤；顶层非对象（如数组）会在 `_deep_merge` 处抛 `AttributeError`。

修复：新增 `_is_number` / `_value_ok` / `_sanitize`，在 `Config.__init__` 合并默认值后按 `DEFAULT_CONFIG` 的类型与取值约束逐字段校验，非法值回退为默认值（数值须为正数；`pos` 须为等长数字列表；`enabled_plugins` 须为字符串列表，长度不限；bool 字段须为 bool）。`get()` 语义不变（仍返回兜底后的健全值）。

### 2. `plugins/system_monitor/collector.py`：`_update()` 防异常（+4 行）

问题：`_update()` 直接调用 `read_gpu()`，若其抛出预期之外的异常（生产路径中 `read_gpu` 内部已吞异常，但 monkeypatch 或未来扩展可能绕过），采集线程死亡。

修复：`read_gpu()` 调用包 try/except，异常时 `gpu=0.0, gpu_ok=False`，线程存活并继续刷新 CPU。

### 回归测试（+7 条）

- `tests/test_config.py` +3：坏类型值兜底 / 合法字段与坏字段并存时保留合法项 / 顶层非对象兜底
- `tests/test_main.py` +2：坏 config 值构建 `PetWindow` 不抛异常；坏 config 值 `install_plugins` 不抛异常且 interval 兜底为 1000
- `tests/test_collector.py` +1：`read_gpu` 抛异常时 `_update` 存活、快照 `gpu_ok=False`
- `tests/test_system_monitor_plugin.py` +1：`gpu_ok=False` 时标签显示「GPU 不可用」

## Step 4 提交

- 精确 add（未用 `git add -A`）：`docs/superpowers/plans/2026-08-14-desktop-pet-system-monitor.md`、`pet/config.py`、`plugins/system_monitor/collector.py`、`tests/test_config.py`、`tests/test_collector.py`、`tests/test_main.py`、`tests/test_system_monitor_plugin.py`
- Commit：`352ebb9a27089af4b5df73dc3295fbb1981f26eb`，message 按 brief 原样 `docs: plan completion and acceptance record`，7 files changed, 169 insertions(+), 17 deletions(-)
- 计划文档 Task 11 段落：4 个 Step 勾选为 `[x]`，第 1-6 条标注「⏳ 待用户真机验收」，第 7/8 条标注 `✅` 及验证方式；docs 其他部分未动

## Concerns

### #1（待用户执行）真机验收 6 条

第 1-6 条（透明背景、拖拽、悬停面板、菜单/暂停、缩放、重启持久化）需真机逐条核对。尤其第 1 条透明背景在真实 GPU/显示器上的表现（offscreen 平台只能验证 `WA_TranslucentBackground` 属性已设置），以及第 5 条角点缩放的交互手感，建议优先验证。预期结果：`python main.py` 启动后窗口透明、拖拽跟随、悬停出 HUD、右键三项菜单、角点锁比例缩放、重启恢复尺寸位置。

### #2（低）pynvml 弃用警告

`collector.py:5` FutureWarning 提示改用 nvidia-ml-py。纯噪音，功能不受影响，本轮未处理（依赖锁定在 `requirements.txt`，不引入新依赖）。

### #3（信息）brief 文件为双重编码乱码

`task-11-brief.md` 磁盘内容是 UTF-8 编码的「乱码文本」（原文先被按 GBK 误读再存回），read 工具与控制台均显示乱码。本任务按用户消息提供的约束 + 计划文档/设计文档可读文本执行，未对 brief 文件做任何修改。如需修复可另开任务转换编码，不影响本次验收结论。

### #4（信息）工作区历史遗留未跟踪文件

`git status` 仍有大量历史遗留的 `.pytest-tmp-*`、`tmp_*`、`.pip-tmp` 等未跟踪目录及 `.superpowers/sdd/` 下的 review/task 报告（含本轮 task-11-report.md 本身），按惯例不纳入提交；`.superpowers/sdd/.../progress.md` 有与本次无关的未提交修改，未触碰、未提交。


## Final Fix Wave（整仓终审修复）

**Commit**: `b482a2a`（fix: final review wave - absolute scale drag, top-level HUD, cleanup）
**来源**: 整仓终审（review-final.txt）2 Critical + 3 Important + 若干 Minor，全部处理。

### C1（Critical）缩放双重累计 → 绝对语义幂等

- 根因：mouseMoveEvent 用相对 press 起点的**总位移** drag_dx，`_apply_resize` 却加在**已更新过**的 `self._scale` 上，连续拖动指数放大、回拖反向放大（move2 实得 2.1、回拖实得 2.2）。
- 修复：`mousePressEvent` 命中角点记录 `self._resize_start_scale = self._scale`；`_apply_resize` 改为 `scale_from_drag(width, drag_dx, self._resize_start_scale)`（几何契约零改动，传起点即绝对语义）；`_finish_resize`/`_exit_resize_mode` 清理置 0。
- 测试：`test_resize_drag_incremental_scale` 扩为三次 move（press → move(145)≈1.5 → move(155)≈1.6 → 回拖 move(105)≈1.1）。反证：临时改回基于当前 scale 累加，第二次 move 失败得 2.1（与审查探针一致）。

### C2（Critical）HUD 整体失效（裁剪 + fade）→ 独立顶层窗口

- 根因一：HudPanel 是子控件，`x = width()+6` 画在父窗口矩形外，child widget 绘制被裁剪，真机一像素不可见。
- 根因二：windowOpacity 只对顶层窗口有效；且 fade_out 后 windowOpacity 不变，finished 回调 `<=0.01` 条件永不满足，HUD 永不消失。
- 修复：HudPanel 构造加 `setWindowFlags(Qt.Tool | FramelessWindowHint | WindowStaysOnTopHint)`（无父构造，接口不变）；PetWindow `self._hud = HudPanel()`；`_position_hud` 改 `self._hud.move(self.mapToGlobal(QPoint(self.width() + 6, 0)))`，并在 moveEvent/resizeEvent/showEvent 同步。
- 测试 +3：`test_hud_is_top_level_window`（isWindow/Tool flag/初始隐藏）、`test_hud_follows_window_position`（move 后全局坐标跟随）、`test_hud_fade_out_hides`（qWait 驱动动画后 isHidden）。现有 test_hud.py 4 条无父子依赖，未改仍过。

### I1（Important）启动 scale 钳制

`self._scale = max(0.3, float(config.get("window.scale", 1.0)))`；新测试 `test_window_min_scale_on_start`（config scale=0.1 → 0.3、宽 30）。config 层类型兜底（Task 11 已做）不受影响。

### I2（Important）退出链路 stop_all

main() 保存 `mgr = install_plugins(...)`，`aboutToQuit` 的 on_close 里 `mgr.stop_all()` 与 save_state 并列，退出时停采集线程。

### I3（Important）enabled 过滤提前

discover 里 enabled 过滤从 factory 实例化之后移到之前，用 `getattr(plugin_class, "id", "")` 类属性过滤，避免实例化被禁插件。test_enabled_filter 仍过。

### Minors

- window.py：Esc 退出缩放清 `_drag_offset = None`（在 _exit_resize_mode 统一清，Esc/菜单路径均覆盖）；`globalPos()` → `globalPosition().toPoint()`；删未使用的 QCursor import。
- test_main.py +1：`load_pixmap` 负向（FileNotFoundError）。
- test_plugins.py +1：PluginClass 存在但非 Plugin 子类被跳过（现有 issubclass 检查已覆盖，补用例锁定）。
- .gitignore +4：`.pytest-tmp-*/`、`.pip-tmp/`、`.pytest_tmp/`、`tmp_*/`（沙盒残留目录防 git add -A 误入）。

### 测试摘要

- 修复前基线：54 passed；修复后全量：**60 passed**（+6：test_window +4、test_main +1、test_plugins +1），无回归。
- 反证实验：C1 双重累计语义下 `test_resize_drag_incremental_scale` 失败（2.1 ≠ 1.6±0.1），确认测试锁定绝对语义。
- 已知警告：pynvml 弃用 FutureWarning（历史噪音）。
