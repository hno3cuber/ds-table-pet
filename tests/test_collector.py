import time
import pytest
from plugins.system_monitor.collector import CpuGpuCollector


def test_update_writes_snapshot(monkeypatch):
    c = CpuGpuCollector()
    monkeypatch.setattr(c, "read_cpu", lambda: 12.0)
    monkeypatch.setattr(c, "read_gpu", lambda: (34.0, True))
    c._update()
    snap = c.snapshot()
    assert snap["cpu"] == 12.0
    assert snap["gpu"] == 34.0
    assert snap["gpu_ok"] is True


def test_gpu_failure_reported(monkeypatch):
    c = CpuGpuCollector()
    monkeypatch.setattr(c, "read_cpu", lambda: 1.0)
    monkeypatch.setattr(c, "read_gpu", lambda: (0.0, False))
    c._update()
    assert c.snapshot()["gpu_ok"] is False


def test_snapshot_is_copy(monkeypatch):
    c = CpuGpuCollector()
    monkeypatch.setattr(c, "read_cpu", lambda: 5.0)
    monkeypatch.setattr(c, "read_gpu", lambda: (6.0, True))
    c._update()
    snap = c.snapshot()
    snap["cpu"] = 99.0
    assert c.snapshot()["cpu"] == 5.0


def test_start_stop_lifecycle():
    c = CpuGpuCollector(interval_s=0.01)
    c.start()
    time.sleep(0.05)
    c.stop()
    assert c._thread is not None
    assert not c._thread.is_alive()


def test_read_gpu_returns_false_on_error(monkeypatch):
    c = CpuGpuCollector()
    import plugins.system_monitor.collector as collector_mod
    monkeypatch.setattr(collector_mod.pynvml, "nvmlInit", lambda: (_ for _ in ()).throw(RuntimeError("no gpu")))
    val, ok = c.read_gpu()
    assert val == 0.0
    assert ok is False


def test_read_gpu_raising_does_not_kill_update(monkeypatch):
    """验收第 8 条：read_gpu 抛异常时 _update 存活，快照标记 GPU 不可用。"""
    c = CpuGpuCollector()
    monkeypatch.setattr(c, "read_cpu", lambda: 42.0)

    def boom():
        raise RuntimeError("gpu read failed")

    monkeypatch.setattr(c, "read_gpu", boom)
    c._update()  # 不抛异常
    snap = c.snapshot()
    assert snap["cpu"] == 42.0
    assert snap["gpu"] == 0.0
    assert snap["gpu_ok"] is False
