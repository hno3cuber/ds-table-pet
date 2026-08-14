from abc import ABC, abstractmethod


class Plugin(ABC):
    id: str = ""
    name: str = ""

    @abstractmethod
    def start(self):
        """启动后台采集等资源。"""

    @abstractmethod
    def stop(self):
        """停止并回收资源。"""

    @abstractmethod
    def poll(self) -> dict:
        """返回最新数据快照（线程安全读）。"""

    @abstractmethod
    def panel(self, parent):
        """返回悬浮面板上的数据块控件。"""

    def set_paused(self, paused: bool):
        """默认空实现；需要响应暂停的插件自行覆盖。"""
