import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from PySide6.QtWidgets import QApplication

# 沙盒环境适配：Windows 上 os.mkdir 的 mode 本应被忽略，但本环境沙盒对
# mode=0o700 创建的目录会拒绝后续访问（scandir/写入/删除均 WinError 5），
# 导致 pytest 的 tmp_path fixture（内部以 0o700 建目录）不可用。
# 统一强制 mode=0o777（即平台默认行为）绕过。
_os_mkdir_orig = os.mkdir


def _os_mkdir(path, mode=0o777, *, dir_fd=None):
    # 强制 0o777：忽略调用方传入的 mode（Windows 上 POSIX mode 本无意义）
    return _os_mkdir_orig(path, 0o777, dir_fd=dir_fd)


os.mkdir = _os_mkdir


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
