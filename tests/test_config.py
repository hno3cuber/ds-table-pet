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


def test_non_dict_config_falls_back_to_defaults(tmp_path):
    """顶层非对象（数组/标量）整体按缺失处理，不崩溃。"""
    p = tmp_path / "config.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    cfg = Config(p)
    assert cfg.get("window.scale") == 1.0
    assert cfg.get("refresh_interval_ms") == 1000
    assert cfg.get("enabled_plugins") == ["system_monitor"]
