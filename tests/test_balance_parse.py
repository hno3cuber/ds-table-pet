"""余额解析逻辑测试（不依赖 PySide6：只加载 balance.py 中的纯函数）。

balance.py 顶层 import 了 PySide6，本测试在无 Qt 环境下无法直接导入，
故用源码抽取的方式单独执行 _parse_balance 的定义。
"""
import ast
import json
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "pet" / "balance.py"


def _load_parse_fn():
    """用 AST 定位 _parse_balance 定义并独立编译执行。

    直接 import balance.py 会拉起 PySide6（测试环境无 Qt），故按语法树
    抽取函数源码段单独执行；用 AST 而非正则，避免受源码排版影响。"""
    source = _SRC.read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(
        (n for n in tree.body
         if isinstance(n, ast.FunctionDef) and n.name == "_parse_balance"),
        None,
    )
    assert node is not None, "未找到 _parse_balance 定义"
    segment = ast.get_source_segment(source, node)
    namespace = {"json": json}
    exec(segment, namespace)  # noqa: S102 - 测试用受控源码
    return namespace["_parse_balance"]


parse_balance = _load_parse_fn()


class TestParseBalance(unittest.TestCase):
    def test_cny_total(self):
        raw = json.dumps({
            "is_available": True,
            "balance_infos": [{
                "currency": "CNY",
                "total_balance": "110.00",
                "granted_balance": "10.00",
                "topped_up_balance": "100.00",
            }],
        }).encode("utf-8")
        self.assertEqual(parse_balance(raw), ("¥110.00", True))

    def test_usd_symbol(self):
        raw = json.dumps({
            "is_available": True,
            "balance_infos": [{"currency": "USD", "total_balance": "5.5"}],
        }).encode("utf-8")
        self.assertEqual(parse_balance(raw), ("$5.50", True))

    def test_unknown_currency_suffix(self):
        raw = json.dumps({
            "is_available": True,
            "balance_infos": [{"currency": "EUR", "total_balance": "3"}],
        }).encode("utf-8")
        self.assertEqual(parse_balance(raw), ("3.00 EUR", True))

    def test_empty_infos(self):
        raw = json.dumps({"is_available": True, "balance_infos": []}).encode("utf-8")
        self.assertEqual(parse_balance(raw), ("无余额信息", False))

    def test_bad_json(self):
        self.assertEqual(parse_balance(b"not json"), ("解析失败", False))

    def test_non_dict(self):
        self.assertEqual(parse_balance(b"[1,2]"), ("数据格式异常", False))


if __name__ == "__main__":
    unittest.main()
