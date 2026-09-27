"""系统级空闲时长检测：距上一次键盘/鼠标输入过去了多久。

Windows 用 user32.GetLastInputInfo（ctypes 直调，无第三方依赖）；其它平台
或 API 调用失败时返回 None，调用方据此静默关闭「犯困」动画功能。
"""

import ctypes
import sys
from ctypes import wintypes


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def system_idle_ms():
    """返回距上一次系统级键鼠输入的毫秒数；不可用时返回 None。

    统计范围是整个系统（任意程序收到的键鼠输入都算），因此鼠标移出本窗口
    也算「有输入」。dwTime 是 32 位 tick（约 49.7 天回绕），与 64 位
    GetTickCount64 相减后按 32 位取模抵消回绕，得到正确的较小空闲时长。
    """
    if sys.platform != "win32":
        return None
    try:
        info = _LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(_LASTINPUTINFO)
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            return None
        tick = ctypes.windll.kernel32.GetTickCount64()
        return int((tick - info.dwTime) & 0xFFFFFFFF)
    except Exception:
        return None
