"""极简日志：插件加载等运行期事故落盘，便于无控制台的 exe 排查。

打包后 console=False，stderr 直接进黑洞，`print` 的报错用户永远看不见。
因此关键异常同时写一份到启动目录的 ds-table-pet.log（追加、按大小轮转一次）。
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path

LOG_NAME = "ds-table-pet.log"
_MAX_BYTES = 256 * 1024


def log_dir() -> Path:
    """日志目录：打包后取 exe 启动目录（可写），开发时取项目根。"""
    if hasattr(sys, "_MEIPASS"):
        return Path.cwd()
    return Path(__file__).resolve().parent.parent


def _rotate(path: Path):
    try:
        if path.exists() and path.stat().st_size > _MAX_BYTES:
            path.replace(path.with_suffix(path.suffix + ".1"))
    except OSError:
        pass


def log_error(message: str, exc: BaseException | None = None):
    """记录一条错误。任何时候都不抛异常：日志失败不能拖垮主流程。"""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"[{stamp}] {message}"]
    if exc is not None:
        lines.append("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    text = "\n".join(lines)

    print(f"[pet] {text}", file=sys.stderr)
    try:
        path = log_dir() / LOG_NAME
        _rotate(path)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(text + "\n")
    except OSError:
        pass
