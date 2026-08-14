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


def test_pause_shows_paused_state(qapp):
    p = SystemMonitorPlugin()
    p.panel(None)
    p.set_paused(True)
    assert p._paused is True
    p.set_paused(False)
    assert p._paused is False


def test_interval_ms_from_constructor():
    p = SystemMonitorPlugin(interval_ms=500)
    assert p.interval_ms == 500
