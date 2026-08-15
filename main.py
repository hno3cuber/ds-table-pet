import signal
import sys

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from pet.config import Config
from pet.plugins import PluginManager
from pet.window import PetWindow

CONFIG_PATH = "config.json"
PIXMAP_PATH = "picture/ds.png"
# 姿势图集：normal 为默认形象，up/down 为拖拽方向形象
PIXMAP_PATHS = {
    "normal": "picture/ds.png",
    "up": "picture/up.png",
    "down": "picture/down.png",
}


def load_pixmap(path: str) -> QPixmap:
    pm = QPixmap(path)
    if pm.isNull():
        raise FileNotFoundError(f"角色图片加载失败: {path}")
    return pm


def load_poses() -> dict:
    """加载全部姿势图；up/down 缺失时回退到 normal，normal 缺失则报错。"""
    normal = load_pixmap(PIXMAP_PATHS["normal"])
    poses = {"normal": normal}
    for name in ("up", "down"):
        pm = QPixmap(PIXMAP_PATHS[name])
        poses[name] = pm if not pm.isNull() else normal
    return poses


def build_window(pixmap: QPixmap, config: Config, poses=None) -> PetWindow:
    return PetWindow(pixmap, config, poses=poses)


def install_plugins(window: PetWindow, config: Config):
    interval_ms = int(config.get("refresh_interval_ms", 1000))

    def factory(plugin_class):
        if getattr(plugin_class, "id", None) == "system_monitor":
            return plugin_class(interval_ms=interval_ms)
        return plugin_class()

    mgr = PluginManager("plugins", enabled=config.get("enabled_plugins", None), factory=factory)
    plugins = mgr.discover()
    for plugin in plugins:
        window.install_plugin(plugin)
    mgr.start_all()
    return mgr


def save_state(window: PetWindow, config: Config):
    config.set("window.pos", window.current_pos())
    config.set("window.scale", window.current_scale())
    config.save()


def install_sigint_quit(app: QApplication):
    """让终端 Ctrl+C 能干净退出。Qt 事件循环阻塞时，Python 的信号处理要等 Python
    字节码执行才会触发，所以用 200ms 的 QTimer 周期性唤醒主线程，SIGINT 到达后
    app.quit() 走正常退出链路（保存状态 + 停插件）。"""
    wake = QTimer()
    wake.setInterval(200)
    wake.timeout.connect(lambda: None)
    wake.start()
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    return wake


def main():
    app = QApplication(sys.argv)
    config = Config(CONFIG_PATH)
    poses = load_poses()
    window = build_window(poses["normal"], config, poses=poses)
    mgr = install_plugins(window, config)
    window.show()
    window.installEventFilter(_StateSaver(window, config))
    _wake = install_sigint_quit(app)  # 持有引用防 GC

    def on_close():
        save_state(window, config)
        mgr.stop_all()

    app.aboutToQuit.connect(on_close)
    sys.exit(app.exec())


class _StateSaver(QObject):
    """在窗口 closeEvent 后兜底保存状态。必须继承 QObject（installEventFilter 要求过滤器是 QObject）。"""

    def __init__(self, window: PetWindow, config: Config):
        super().__init__()
        self.window = window
        self.config = config

    def eventFilter(self, obj, event):
        if obj is self.window and event.type() == QEvent.Close:
            save_state(self.window, self.config)
        return False


if __name__ == "__main__":
    main()
