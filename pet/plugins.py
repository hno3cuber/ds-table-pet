import importlib.util
import sys
from pathlib import Path

from pet.plugin import Plugin


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
                inst = self.factory(plugin_class)
            except Exception as e:
                print(f"[plugin] skip broken plugin: {entry.name}: {e}", file=sys.stderr)
                continue
            if self.enabled is not None and inst.id not in self.enabled:
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
