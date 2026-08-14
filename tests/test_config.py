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
