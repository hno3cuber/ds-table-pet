"""甩动检测器：从鼠标拖拽轨迹中识别「来回甩」的动作。

纯逻辑模块，不 import Qt，便于脱离界面做单元测试。

判定思路：拖拽位移按「段」累计，每攒够 min_leg_px 记一段方向矢量；
相邻两段矢量点积 < 0（方向大体相反）记一次「反转」。松手时统计最近
window_ms 内的反转次数，达到 reversals 即判定为甩动。

设计意图是「甩完停一会儿再松手就不算数」：用滑动时间窗而不是累计总数，
所以反转记录带时间戳，过期即丢弃。
"""

import math
from collections import deque


class ShakeDetector:
    """甩动检测器：分段累计位移，数时间窗内的方向反转次数。

    用法：拖拽开始时 reset()，拖拽中持续 feed(x, y, t_ms)，
    松手时 release(t_ms) 返回是否判定为甩动。t_ms 建议取单调时钟毫秒
    （如 time.monotonic() * 1000），避免系统校时干扰时间窗。
    """

    def __init__(self, min_leg_px: int = 25, window_ms: int = 1500, reversals: int = 3):
        self._min_leg_px = min_leg_px      # 一段「甩」的最小位移（px），低于视为抖动
        self._window_ms = window_ms        # 反转记录的滑动时间窗（ms）
        self._reversals_needed = reversals # 触发甩动所需的窗内反转次数
        self._last_pos = None              # 上一个采样点 (x, y)；None = 尚未落笔
        self._acc_x = 0.0                  # 当前段累计位移矢量（未满一段时暂存）
        self._acc_y = 0.0
        self._last_leg = None              # 上一段方向矢量 (dx, dy)
        self._reversal_ts = deque()        # 时间窗内的反转时间戳（ms，单调递增）

    def feed(self, x, y, t_ms):
        """喂入一个拖拽采样点。

        与上一个记录点的位移累计进当前段；累计模长达到 min_leg_px 时记一段
        方向矢量，并与上一段做点积：< 0 说明方向大体调头，记一次反转。"""
        if self._last_pos is None:
            self._last_pos = (x, y)  # 落笔：只记位置，不产生位移
            return
        self._acc_x += x - self._last_pos[0]
        self._acc_y += y - self._last_pos[1]
        self._last_pos = (x, y)
        if math.hypot(self._acc_x, self._acc_y) < self._min_leg_px:
            return  # 还没攒够一段，继续累计（来回微抖会相互抵消，永远攒不够）
        leg = (self._acc_x, self._acc_y)
        self._acc_x = 0.0
        self._acc_y = 0.0
        if self._last_leg is not None:
            dot = leg[0] * self._last_leg[0] + leg[1] * self._last_leg[1]
            if dot < 0:
                self._reversal_ts.append(t_ms)
        self._last_leg = leg

    def release(self, t_ms) -> bool:
        """松手判定：丢弃早于 t_ms - window_ms 的反转后，剩余次数达标则触发。"""
        cutoff = t_ms - self._window_ms
        while self._reversal_ts and self._reversal_ts[0] < cutoff:
            self._reversal_ts.popleft()
        return len(self._reversal_ts) >= self._reversals_needed

    def reset(self):
        """清空全部状态：新一轮拖拽开始时调用，不残留上一轮记录。"""
        self._last_pos = None
        self._acc_x = 0.0
        self._acc_y = 0.0
        self._last_leg = None
        self._reversal_ts.clear()
