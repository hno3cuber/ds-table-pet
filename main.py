import os
import signal
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtWidgets import QApplication

from pet.config import Config
from pet.plugins import PluginManager
from pet.window import PetWindow


def _resource_base() -> Path:
    """资源根：打包后为 PyInstaller 解包目录（_MEIPASS），开发时为项目根。"""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).parent


def _config_dir() -> Path:
    """配置目录：打包后为 exe 启动目录（可写、可持久化），开发时为项目根。"""
    if hasattr(sys, "_MEIPASS"):
        return Path.cwd()
    return Path(__file__).parent


CONFIG_PATH = str(_config_dir() / "config.json")
PLUGINS_DIR = str(_resource_base() / "plugins")
PIXMAP_PATH = str(_resource_base() / "picture" / "idel.gif")   # 站立循环动画（首帧兼作窗口尺寸基准）
WALK_PATH = str(_resource_base() / "picture" / "walk.gif")


def load_pixmap(path: str) -> QPixmap:
    pm = QPixmap(path)
    if pm.isNull():
        raise FileNotFoundError(f"角色图片加载失败: {path}")
    return pm


def load_gif_frames(path: str) -> tuple:
    """把 GIF 逐帧读进内存（不落盘切片），返回 (frames, delays) 元组。

    frames — QPixmap 帧列表；delays — 每帧对应延迟（ms），动画节奏不均匀的
    素材按帧保留。文件缺失/不可读/无帧时返回空列表，调用方据此禁用。
    """
    reader = QImageReader(path)
    frames, delays = [], []
    if reader.canRead():
        # read() 对动画格式逐帧顺序推进；nextImageDelay 在 read 前读取当前帧延迟
        while True:
            delay = reader.nextImageDelay()
            image = reader.read()
            if image.isNull():
                break
            frames.append(QPixmap.fromImage(image))
            delays.append(delay)
    return frames, delays


def build_window(pixmap: QPixmap, config: Config, idle_frames=None,
                 idle_delays=None, walk_frames=None) -> PetWindow:
    return PetWindow(pixmap, config, idle_frames=idle_frames,
                     idle_delays=idle_delays, walk_frames=walk_frames)


def install_plugins(window: PetWindow, config: Config):
    interval_ms = int(config.get("refresh_interval_ms", 1000))

    def factory(plugin_class):
        if getattr(plugin_class, "id", None) == "system_monitor":
            return plugin_class(interval_ms=interval_ms)
        return plugin_class()

    mgr = PluginManager(PLUGINS_DIR, enabled=config.get("enabled_plugins", None), factory=factory)
    plugins = mgr.discover()
    for plugin in plugins:
        window.install_plugin(plugin)
    mgr.start_all()
    return mgr


def save_state(window: PetWindow, config: Config):
    config.set("window.pos", window.current_pos())
    window.save_scale()


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
    pixmap = load_pixmap(PIXMAP_PATH)
    idle_frames, idle_delays = load_gif_frames(PIXMAP_PATH)  # 站立循环动画
    walk_frames, _ = load_gif_frames(WALK_PATH)              # 空 → 无行走，wander 自动关
    window = build_window(pixmap, config, idle_frames=idle_frames,
                          idle_delays=idle_delays, walk_frames=walk_frames)
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
