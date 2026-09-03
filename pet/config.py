import copy
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "refresh_interval_ms": 1000,
    "window": {
        "pos": [100, 100],
        "scale": 1.0,
        # 自由宽高比：scale_x/scale_y 独立；None 表示未设置，回退到 scale
        "scale_x": None,
        "scale_y": None,
    },
    "breathing_animation": False,
    "wander": {"enabled": True},
    "enabled_plugins": ["system_monitor"],
    "launch_slots": [None] * 8,  # 快捷环 8 个槽位：路径或 null
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


def _is_number(value) -> bool:
    """数字（排除 bool，bool 是 int 子类）。"""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _value_ok(value, default) -> bool:
    """按默认值的类型与取值约束校验加载值；非法视为缺失（走默认值）。"""
    if default is None:
        # schema 显式标 None 的字段（如 window.scale_x/y）：仅接受 None 或数字
        return value is None or _is_number(value)
    if isinstance(default, bool):
        return isinstance(value, bool)
    if isinstance(default, (int, float)):
        return _is_number(value) and value > 0
    if isinstance(default, list):
        if not isinstance(value, list):
            return False
        if not default:
            return True
        if default[0] is None:
            # 含空槽位的列表（如 launch_slots）：长度一致且每项为路径或 null
            return len(value) == len(default) and all(x is None or isinstance(x, str) for x in value)
        if isinstance(default[0], str):
            return all(isinstance(x, str) for x in value)
        return len(value) == len(default) and all(_is_number(x) for x in value)
    if isinstance(default, str):
        return isinstance(value, str)
    return True


def _sanitize(value, default):
    """把加载值与默认配置逐字段比对，非法值回退为默认值（默认值兜底）。"""
    if isinstance(default, dict):
        base = default if not isinstance(value, dict) else value
        return {k: _sanitize(base.get(k, v), v) for k, v in default.items()}
    if _value_ok(value, default):
        return copy.deepcopy(value)
    return copy.deepcopy(default)


class Config:
    def __init__(self, path):
        self.path = Path(path)
        loaded = {}
        if self.path.exists():
            try:
                parsed = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                parsed = {}
            if isinstance(parsed, dict):  # 顶层非对象（如数组/标量）整体按缺失处理
                loaded = parsed
        self.data = _sanitize(_deep_merge(DEFAULT_CONFIG, loaded), DEFAULT_CONFIG)

    def get(self, key, default=None):
        node = self.data
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key, value):
        parts = key.split(".")
        node = self.data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
