"""甩动检测器（pet/shake.py）测试。

shake.py 不依赖 PySide6，可直接 import；仅把项目根补进 sys.path，
保证 `python -m unittest discover -s tests`（start_dir 为 tests/）下也能找到 pet 包。
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pet.shake import ShakeDetector


def drag(det, x, y, t, directions, step_px=30, step_ms=100):
    """模拟一段拖拽：先在 (x, y) 落笔，再按 directions 逐段直拖。

    每个元素是一段方向（(dx, dy) 单位矢量），步长 step_px 恰好超过默认
    min_leg_px=25，一步即记一段；返回末态 (x, y, t) 便于继续喂点。"""
    det.feed(x, y, t)  # 落笔
    for dx, dy in directions:
        x += dx * step_px
        y += dy * step_px
        t += step_ms
        det.feed(x, y, t)
    return x, y, t


class TestShakeDetector(unittest.TestCase):
    def setUp(self):
        self.det = ShakeDetector(min_leg_px=25, window_ms=1500, reversals=3)

    def test_straight_line_no_trigger(self):
        """单向直线拖动：位移再大也没有方向反转，不触发。"""
        x, y, t = drag(self.det, 0, 0, 0, [(1, 0)] * 8)
        self.assertFalse(self.det.release(t))

    def test_three_reversals_trigger(self):
        """右→左→右→左三次反向甩动后立刻松手：触发。"""
        x, y, t = drag(self.det, 0, 0, 0, [(1, 0), (-1, 0), (1, 0), (-1, 0)])
        self.assertTrue(self.det.release(t))

    def test_fewer_reversals_no_trigger(self):
        """只甩出两次反转（不够 reversals=3）：不触发。"""
        x, y, t = drag(self.det, 0, 0, 0, [(1, 0), (-1, 0), (1, 0)])
        self.assertFalse(self.det.release(t))

    def test_reversals_expire_after_window(self):
        """甩完停顿超过 window_ms 再松手：反转记录过期，不触发。"""
        x, y, t = drag(self.det, 0, 0, 0, [(1, 0), (-1, 0), (1, 0), (-1, 0)])
        t += 2000  # 停顿超过 1500ms 时间窗
        self.assertFalse(self.det.release(t))

    def test_tiny_jitter_no_trigger(self):
        """每步位移都小于 min_leg_px 的来回微抖：矢量相互抵消，攒不出一段。"""
        self.det.feed(0, 0, 0)
        x, t = 0, 0
        for i in range(40):
            x += 10 if i % 2 == 0 else -10  # 在 0/10 之间来回，单步 10px < 25px
            t += 16
            self.det.feed(x, 0, t)
        self.assertFalse(self.det.release(t))

    def test_reset_clears_state(self):
        """reset 后上一轮反转记录与位置基准全部清空，新一轮从零开始。"""
        x, y, t = drag(self.det, 0, 0, 0, [(1, 0), (-1, 0), (1, 0), (-1, 0)])
        self.assertTrue(self.det.release(t))  # 前置：确实攒够了反转
        self.det.reset()
        self.assertFalse(self.det.release(t))  # reset 后立即判定：无残留
        # reset 后检测器仍可正常工作：重新甩满三次反转再次触发
        x, y, t = drag(self.det, x, y, t, [(1, 0), (-1, 0), (1, 0), (-1, 0)])
        self.assertTrue(self.det.release(t))


if __name__ == "__main__":
    unittest.main()
