import json
import pytest
from pet.config import Config, DEFAULT_CONFIG


def test_defaults_when_file_missing(tmp_path):
    cfg = Config(tmp_path / "config.json")
    assert cfg.get("refresh_interval_ms") == 1000
    assert cfg.get("window.scale") == 1.0
    assert cfg.get("enabled_plugins") == ["system_monitor"]


def test_merges_missing_fields_with_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"refresh_interval_ms": 500}), encoding="utf-8")
    cfg = Config(p)
    assert cfg.get("refresh_interval_ms") == 500
    assert cfg.get("window.scale") == 1.0


def test_set_and_save(tmp_path):
    p = tmp_path / "config.json"
    cfg = Config(p)
    cfg.set("window.scale", 1.5)
    cfg.set("window.pos", [200, 300])
    cfg.save()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["window"]["scale"] == 1.5
    assert data["window"]["pos"] == [200, 300]
    assert data["refresh_interval_ms"] == 1000  # 默认字段回填


def test_defaults_constants_shape():
    assert DEFAULT_CONFIG["window"]["scale"] == 1.0
    assert DEFAULT_CONFIG["enabled_plugins"] == ["system_monitor"]


def test_launch_slots_default_empty(tmp_path):
    cfg = Config(tmp_path / "config.json")
    slots = cfg.get("launch_slots")
    assert len(slots) == 8
    assert all(s is None for s in slots)


def test_launch_slots_persist_mixed_paths(tmp_path):
    p = tmp_path / "config.json"
    cfg = Config(p)
    cfg.set("launch_slots", ["C:\\a.lnk", None, "D:\\b.exe", None, None, None, None, None])
    cfg.save()
    cfg2 = Config(p)  # 重载：str 与 null 混合应原样保留
    slots = cfg2.get("launch_slots")
    assert slots[0] == "C:\\a.lnk"
    assert slots[1] is None
    assert slots[2] == "D:\\b.exe"
    assert len(slots) == 8


def test_launch_slots_bad_type_falls_back(tmp_path):
    p = tmp_path / "config.json"
    p.write_text('{"launch_slots": "not-a-list"}', encoding="utf-8")
    cfg = Config(p)
    assert cfg.get("launch_slots") == [None] * 8


def test_bad_typed_values_fall_back_to_defaults(tmp_path):
    """验收第 7 条：改坏字段值（错误类型/非法取值）按默认值兜底。"""
    p = tmp_path / "config.json"
    p.write_text(json.dumps({
        "window": {"scale": "abc", "pos": "oops"},
        "refresh_interval_ms": -5,
        "enabled_plugins": None,
    }), encoding="utf-8")
    cfg = Config(p)
    assert cfg.get("window.scale") == 1.0
    assert cfg.get("window.pos") == [100, 100]
    assert cfg.get("refresh_interval_ms") == 1000
    assert cfg.get("enabled_plugins") == ["system_monitor"]


def test_valid_fields_survive_alongside_bad_ones(tmp_path):
    """部分字段坏时，合法字段保留、坏字段兜底。"""
    p = tmp_path / "config.json"
    p.write_text(json.dumps({
        "window": {"scale": "abc", "pos": [50, 60]},
        "refresh_interval_ms": 500,
    }), encoding="utf-8")
    cfg = Config(p)
    assert cfg.get("window.scale") == 1.0
    assert cfg.get("window.pos") == [50, 60]
    assert cfg.get("refresh_interval_ms") == 500


def test_scale_x_y_roundtrip_survives_reload(tmp_path):
    """自由宽高比：window.scale_x/scale_y 持久化后重载不丢。"""
    p = tmp_path / "config.json"
    cfg = Config(p)
    cfg.set("window.scale_x", 1.7)
    cfg.set("window.scale_y", 0.6)
    cfg.save()
    cfg2 = Config(p)
    assert cfg2.get("window.scale_x") == 1.7
    assert cfg2.get("window.scale_y") == 0.6


def test_scale_x_y_default_none_when_absent(tmp_path):
    """旧 config（只有 scale）加载后 scale_x/scale_y 为 None（回退等比 scale）。"""
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"window": {"pos": [1, 2], "scale": 1.5}}), encoding="utf-8")
    cfg = Config(p)
    assert cfg.get("window.scale") == 1.5
    assert cfg.get("window.scale_x") is None
    assert cfg.get("window.scale_y") is None


def test_bad_scale_x_y_fall_back(tmp_path):
    """scale_x/scale_y 非法（非数字）时被过滤为 None，不影响 window.scale。"""
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"window": {"scale_x": "wide", "scale": 1.2}}), encoding="utf-8")
    cfg = Config(p)
    assert cfg.get("window.scale") == 1.2
    assert cfg.get("window.scale_x") is None
    assert cfg.get("window.scale_y") is None



def test_non_dict_config_falls_back_to_defaults(tmp_path):
    """顶层非对象（数组/标量）整体按缺失处理，不崩溃。"""
    p = tmp_path / "config.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    cfg = Config(p)
    assert cfg.get("window.scale") == 1.0
    assert cfg.get("refresh_interval_ms") == 1000
    assert cfg.get("enabled_plugins") == ["system_monitor"]
