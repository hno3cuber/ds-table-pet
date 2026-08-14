from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget

from pet.hud import OutlinedLabel
from pet.plugin import Plugin
from plugins.system_monitor.collector import CpuGpuCollector

class SystemMonitorPlugin(Plugin):
    id = "system_monitor"
    name = "系统监控"

    def __init__(self, interval_ms: int = 1000):
        self.interval_ms = interval_ms
        self.collector = CpuGpuCollector()
        self._timer = None
        self._widget = None
        self._labels = []
        self._paused = False

    def start(self):
        self.collector.start()
        if self._timer is None:
            self._timer = QTimer()
            self._timer.timeout.connect(self._refresh)
            self._timer.start(self.interval_ms)

    def stop(self):
        self.collector.stop()
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def poll(self) -> dict:
        return self.collector.snapshot()

    def panel(self, parent) -> QWidget:
        widget = QWidget(parent)
        self._widget = widget  # 持有引用，防止顶层控件被 GC 后 QLabel 失效
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        self._labels = [OutlinedLabel("CPU --", widget), OutlinedLabel("GPU --", widget)]
        for label in self._labels:
            layout.addWidget(label)
        self._refresh()
        return widget

    def set_paused(self, paused: bool):
        self._paused = paused
        if paused:
            if self._timer is not None:
                self._timer.stop()
            for label in self._labels:
                label.setText("已暂停")
        else:
            if self._timer is not None:
                self._timer.start(self.interval_ms)
            self._refresh()

    def _refresh(self):
        if not self._labels:
            return
        snap = self.poll()
        cpu_text = f"CPU {snap['cpu']:.0f}%"
        gpu_text = "GPU 不可用" if not snap["gpu_ok"] else f"GPU {snap['gpu']:.0f}%"
        self._labels[0].setText(cpu_text)
        self._labels[1].setText(gpu_text)


# discover() 契约（Task 4）：插件模块需导出 PluginClass；
# 本插件类名 SystemMonitorPlugin 为 spec/Task 6 命名，此处别名对齐两边契约。
PluginClass = SystemMonitorPlugin
