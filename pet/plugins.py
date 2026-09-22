import importlib.util
from pathlib import Path

from pet.logging import log_error
from pet.plugin import Plugin


class PluginLoadFailure:
    """加载失败的插件占位：面板上给一行可见提示，不再静默消失。"""

    def __init__(self, entry_name: str, reason: str):
        self.id = f"failed:{entry_name}"
        self.name = f"{entry_name} 加载失败"
        self.reason = reason

    def start(self):
        pass

    def stop(self):
        pass

    def poll(self) -> dict:
        return {}

    def set_paused(self, paused: bool):
        pass

    def panel(self, parent):
        from pet.hud import OutlinedLabel

        label = OutlinedLabel(f"{self.name}", parent)
        label.setToolTip(self.reason)
        return label


class PluginManager:
    def __init__(self, plugins_dir, enabled=None, factory=None):
        self.plugins_dir = Path(plugins_dir)
        self.enabled = list(enabled) if enabled is not None else None
        self.factory = factory or (lambda plugin_class: plugin_class())
        self.instances: list[Plugin] = []

    def discover(self) -> list[Plugin]:
        instances: list[Plugin] = []
        for entry in sorted(self.plugins_dir.iterdir()):
            mod_file = entry / "plugin.py"
            if not entry.is_dir() or not mod_file.exists():
                continue
            spec = importlib.util.spec_from_file_location(f"plugin_{entry.name}", mod_file)
            if spec is None or spec.loader is None:
                continue
            try:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                plugin_class = getattr(module, "PluginClass", None)
                if plugin_class is None or not issubclass(plugin_class, Plugin):
                    continue
                # 用类属性 id 过滤（factory 实例化之前），避免实例化被禁用插件
                if self.enabled is not None and getattr(plugin_class, "id", "") not in self.enabled:
                    continue
                inst = self.factory(plugin_class)
            except Exception as e:
                # 吞掉会让故障彻底无声（打包后 stderr 还是黑洞），必须落盘 + 面板可见
                log_error(f"plugin load failed: {entry.name}", e)
                instances.append(PluginLoadFailure(entry.name, f"{type(e).__name__}: {e}"))
                continue
            instances.append(inst)
        self.instances = instances
        return instances

    def start_all(self):
        for inst in self.instances:
            inst.start()

    def stop_all(self):
        for inst in self.instances:
            inst.stop()
