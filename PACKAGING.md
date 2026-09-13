# 打包指南（Windows / PyInstaller）

把 ds-table-pet 打包成 Windows 可执行程序（onedir，无控制台窗口）。

> 当前验证环境：Python 3.14.5 / PySide6 6.11.2 / PyInstaller 6.22.3 / Pillow 12.3.0
> 产物：`dist/ds-table-pet/`，双击 `ds-table-pet.exe` 运行。

---

## 一、前置条件

- 已安装 Python（`python --version` 可用）
- 联网（首次需要下载约 300–500 MB 依赖）

## 二、首次打包

### 1. 建虚拟环境（只做一次）

```powershell
cd <项目根目录>   # 含 main.py 的那一层
python -m venv .venv
```

### 2. 安装依赖（只做一次，依赖变化后重跑）

```powershell
.\.venv\Scripts\python.exe -m pip install PySide6 psutil nvidia-ml-py pyinstaller Pillow
```

- `PySide6` — GUI 框架
- `psutil` / `nvidia-ml-py` — system_monitor 插件采集 CPU / NVIDIA 显卡数据
- `pyinstaller` — 打包工具
- `Pillow` — **必需**，用于把 `picture/icon.png` 自动转成 exe 可用的 `.ico`

### 3. 打包

> 若还没有 `ds_table_pet.spec`（本仓不跟踪它），先按第五节「spec 说明」生成一份再继续。

```powershell
.\.venv\Scripts\pyinstaller.exe --noconfirm --clean ds_table_pet.spec
```

看到 `Build complete!` 即成功，产物在 `dist\ds-table-pet\`。

## 三、日常重新打包

改了代码后，直接跑第三步即可：

```powershell
.\.venv\Scripts\pyinstaller.exe --noconfirm --clean ds_table_pet.spec
```

**只有新增了依赖包**时，才需要回到第二节第 2 步补装。

---

## 四、常见坑

### 权限错误（部分受限环境）

若出现类似报错：

```
PermissionError: [Errno 13] Permission denied: '...\Temp\pip-unpack-...\xxx.whl'
```

或 `ensurepip` 报临时目录 `Access is denied`，说明当前命令对临时目录没有写权限。
**解法**：在提权 / 非受限的终端里执行该命令（例如管理员 PowerShell），或由具备相应权限的用户执行。

### 图标格式错误

```
ValueError: Received icon image '...\icon.png' which exists but is not in the correct format.
```

说明环境里缺 `Pillow`。装上即可（见第二节第 2 步），PyInstaller 会自动把 png 转成 ico；
也可自行把 png 转成 `.ico` 后改 spec 中的 `icon=`。

### 打包后缺素材 / 插件

检查 `dist\ds-table-pet\_internal\` 下是否有 `picture\`（四个素材）和 `plugins\system_monitor\`。
缺失通常是 spec 的 `datas` 项被改动所致。

---

## 五、原理速查

| 内容 | 位置 / 说明 |
| --- | --- |
| 打包配置 | `ds_table_pet.spec`（项目根目录，**本仓不纳入版本控制**，见下方“spec 说明”） |
| 入口 | `main.py` |
| exe 图标 | `picture/icon.png`（编译期嵌入 exe，需 Pillow 转换） |
| 运行时资源 | `picture/`、`plugins/` → 打进 `_internal/`，由 `main.py` 的 `sys._MEIPASS` 逻辑定位 |
| 配置文件 | 打包后写在 exe 同目录（可写、可持久化），重打包不会丢 |
| 打包模式 | onedir（一个文件夹）；`console=False` 无控制台窗口 |
| 开机自启 | 未做，如需请自行创建快捷方式到启动目录 |

### spec 说明

本仓库的 `.gitignore` 排除了 `*.spec`，**打包配置不入库**。`ds_table_pet.spec` 仅存在于本地，重打包直接用；
若换了机器、文件丢失，按下表重新生成一份同名 spec 即可：

```python
# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path(SPECPATH)

datas = [
    (str(ROOT / "picture"), "picture"),
    (str(ROOT / "plugins"), "plugins"),
]

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="ds-table-pet",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ROOT / "picture" / "icon.png"),
)

coll = COLLECT(exe, a.binaries, a.datas, name="ds-table-pet")
```

## 六、瘦身（可选）

当前整包约 134 MB，主要是 PySide6。可在 spec 的 `excludes` 中加入用不到的 Qt 模块来减小体积，
但**不要盲目添加**：排除不当会导致运行时缺模块，改动后务必重新冒烟测试（双击运行确认不崩）。
