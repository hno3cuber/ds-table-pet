from plugins.system_monitor.plugin import SystemMonitorPlugin


def test_plugin_metadata():
    p = SystemMonitorPlugin()
    assert p.id == "system_monitor"
    assert p.name == "系统监控"


def test_poll_returns_snapshot_shape():
    p = SystemMonitorPlugin()
    snap = p.poll()
    assert set(snap.keys()) == {"cpu", "gpu", "gpu_ok"}


def test_panel_creates_widget(qapp):
    p = SystemMonitorPlugin()
    w = p.panel(None)
    assert w is not None
    assert w.layout() is not None
    assert w.layout().count() == 2  # CPU 行 + GPU 行


def test_refresh_updates_labels(qapp):
    from PySide6.QtWidgets import QLabel
    p = SystemMonitorPlugin()
    w = p.panel(None)
    labels = [w.layout().itemAt(i).widget() for i in range(2)]
    p.collector._snapshot = {"cpu": 55.0, "gpu": 70.0, "gpu_ok": True}
    p._refresh()
    assert "55" in labels[0].text()
    assert "70" in labels[1].text()


def test_refresh_shows_gpu_unavailable_when_gpu_ok_false(qapp):
    """验收第 8 条：GPU 不可用时标签显示「GPU 不可用」。"""
    p = SystemMonitorPlugin()
    w = p.panel(None)
    labels = [w.layout().itemAt(i).widget() for i in range(2)]
    p.collector._snapshot = {"cpu": 10.0, "gpu": 0.0, "gpu_ok": False}
    p._refresh()
    assert labels[1].text() == "GPU 不可用"


def test_pause_shows_paused_state(qapp):
    from PySide6.QtCore import QTimer
    p = SystemMonitorPlugin(interval_ms=500)
    w = p.panel(None)
    p._timer = QTimer()
    p._timer.timeout.connect(p._refresh)
    p._timer.start(p.interval_ms)
    assert p._timer.isActive()
    p.set_paused(True)
    assert p._paused is True
    assert p._timer.isActive() is False
    labels = [w.layout().itemAt(i).widget() for i in range(2)]
    assert labels[0].text() == "已暂停"
    assert labels[1].text() == "已暂停"
    p.set_paused(False)
    assert p._paused is False
    assert p._timer.isActive() is True


def test_interval_ms_from_constructor():
    p = SystemMonitorPlugin(interval_ms=500)
    assert p.interval_ms == 500
