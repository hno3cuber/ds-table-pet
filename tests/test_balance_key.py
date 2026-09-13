"""API Key 读取逻辑测试（不依赖 PySide6，不触碰真实磁盘）。

load_api_key 只依赖 os.environ 与一个 key 文件。受限沙盒下新建目录不可写，
故用假的 Path 替身（stub）模拟 key 文件的存在与内容，聚焦读取分支本身。
"""
import ast
import os
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "pet" / "balance.py"


def _load_key_fn():
    source = _SRC.read_text(encoding="utf-8")
    tree = ast.parse(source)
    # 白名单：只取 load_api_key 依赖的模块级常量赋值，跳过所有 import（含 PySide6）
    wanted = {"_ENV_VAR", "KEY_FILENAME"}
    assigns = []
    for n in tree.body:
        if isinstance(n, ast.Assign):
            targets = [t.id for t in n.targets if isinstance(t, ast.Name)]
            if wanted & set(targets):
                assigns.append(ast.get_source_segment(source, n))
    fn = next(
        (n for n in tree.body
         if isinstance(n, ast.FunctionDef) and n.name == "load_api_key"),
        None,
    )
    assert fn is not None, "未找到 load_api_key 定义"
    parts = assigns + [ast.get_source_segment(source, fn)]
    namespace = {"os": os, "Path": Path}
    exec("\n\n".join(parts), namespace)  # noqa: S102 - 测试用受控源码
    return namespace["load_api_key"], namespace["_ENV_VAR"], namespace["KEY_FILENAME"]


load_api_key, ENV_VAR, KEY_FILENAME = _load_key_fn()


class _FakePath:
    """假 Path：可控 exists/read_text，替代真实文件系统。"""

    def __init__(self, content=None, error=None):
        self._content = content
        self._error = error

    def __truediv__(self, other):
        return self

    def exists(self):
        return self._content is not None

    def read_text(self, encoding="utf-8"):
        if self._error is not None:
            raise self._error
        return self._content


class TestLoadApiKey(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop(ENV_VAR, None)

    def tearDown(self):
        os.environ.pop(ENV_VAR, None)
        if self._saved is not None:
            os.environ[ENV_VAR] = self._saved

    def _call(self, fake):
        """把模块级 Path 临时替换为假实现，执行后还原。"""
        module = load_api_key.__globals__
        original = module["Path"]
        module["Path"] = lambda _base: fake
        try:
            return load_api_key("ignored_base_dir")
        finally:
            module["Path"] = original

    def test_env_takes_priority(self):
        os.environ[ENV_VAR] = "env-key"
        self.assertEqual(self._call(_FakePath("file-key")), "env-key")

    def test_file_fallback(self):
        self.assertEqual(self._call(_FakePath("file-key\n")), "file-key")

    def test_skip_comment_lines(self):
        content = "# comment\n\n  real-key  \n"
        self.assertEqual(self._call(_FakePath(content)), "real-key")

    def test_missing_file(self):
        self.assertEqual(self._call(_FakePath(None)), "")

    def test_unreadable_file(self):
        self.assertEqual(self._call(_FakePath("x", error=OSError("nope"))), "")


if __name__ == "__main__":
    unittest.main()
