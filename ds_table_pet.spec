# -*- mode: python ; coding: utf-8 -*-
"""ds-table-pet PyInstaller 打包配置（onedir，无控制台）。

资源（picture/ 素材与 plugins/ 插件）随包分发：运行时 main.py 通过 sys._MEIPASS
定位资源根，配置则写在 exe 启动目录，方便持久化。
"""

from pathlib import Path

ROOT = Path(SPECPATH)


def _plugin_sources() -> list[tuple[str, str]]:
    """plugins/ 下的插件源文件（不含 __pycache__）。

    datas 直接给目录会把 __pycache__/*.pyc 一并拷进包：那些缓存是给打包机的
    Python 版本编的，既无用处又可能与目标解释器不匹配，故逐文件收集。
    """
    plugins_root = ROOT / "plugins"
    entries: list[tuple[str, str]] = []
    for path in sorted(plugins_root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        entries.append((str(path), str(path.parent.relative_to(ROOT))))
    return entries


datas = [
    (str(ROOT / "picture"), "picture"),
]
datas.extend(_plugin_sources())

# 插件里的 psutil / pynvml 由运行期动态加载（importlib.util.spec_from_file_location），
# 不经 import 语句，静态分析看不到，必须显式声明，否则打包后插件因 ModuleNotFoundError 被静默跳过。
# 注意 nvidia-ml-py 的发行名与导入名不同：import 名是 pynvml。
hiddenimports = ["psutil", "pynvml"]

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 插件入口 plugin.py 由运行期动态加载（不经 import），已由 hiddenimports 补上
    # psutil / pynvml；其余按常规分析 PySide6。
    excludes=["pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ds-table-pet",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # 无控制台窗口（桌宠后台常驻）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "picture" / "icon.png"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ds-table-pet",
)
