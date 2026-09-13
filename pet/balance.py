"""DeepSeek 开放平台余额查询。

密钥来源（优先级从高到低）：
1. 环境变量 DEEPSEEK_API_KEY
2. 项目根目录下的 deepseek_key.txt（首行，UTF-8）

查询接口：GET https://api.deepseek.com/user/balance
返回 JSON 形如：
    {"is_available": true,
     "balance_infos": [{"currency": "CNY",
                        "total_balance": "110.00",
                        "granted_balance": "10.00",
                        "topped_up_balance": "100.00"}]}
"""
import os
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

BALANCE_URL = "https://api.deepseek.com/user/balance"
KEY_FILENAME = "deepseek_key.txt"
_ENV_VAR = "DEEPSEEK_API_KEY"


def load_api_key(base_dir: Path) -> str:
    """读取 API Key：环境变量优先，其次本地密钥文件。都无则返回空串。"""
    env_key = os.environ.get(_ENV_VAR, "").strip()
    if env_key:
        return env_key
    key_file = Path(base_dir) / KEY_FILENAME
    if key_file.exists():
        try:
            for line in key_file.read_text(encoding="utf-8").splitlines():
                token = line.strip()
                if token and not token.startswith("#"):
                    return token
        except OSError:
            return ""
    return ""


class BalanceFetcher(QObject):
    """异步余额查询器。

    finished(text, ok)：text 为可直接展示的余额串（如 "¥110.00"）或错误提示，
    ok 标示成功与否，UI 据此决定文字颜色。
    """

    finished = Signal(str, bool)

    def __init__(self, base_dir: Path, parent=None):
        super().__init__(parent)
        self._base_dir = Path(base_dir)
        self._mgr = QNetworkAccessManager(self)

    def fetch(self):
        key = load_api_key(self._base_dir)
        if not key:
            self.finished.emit(
                f"未配置密钥\n在 {KEY_FILENAME} 或环境变量 {_ENV_VAR} 中填写", False
            )
            return
        request = QNetworkRequest(QUrl(BALANCE_URL))
        request.setRawHeader(b"Authorization", f"Bearer {key}".encode("utf-8"))
        request.setRawHeader(b"Accept", b"application/json")
        reply = self._mgr.get(request)
        reply.finished.connect(lambda: self._on_finished(reply))

    def _on_finished(self, reply: QNetworkReply):
        try:
            if reply.error() != QNetworkReply.NoError:
                self.finished.emit(f"查询失败\n{reply.errorString()}", False)
                return
            raw = bytes(reply.readAll().data())
            self.finished.emit(*_parse_balance(raw))
        finally:
            reply.deleteLater()


def _parse_balance(raw: bytes):
    """解析接口返回，提取 total_balance。返回 (展示文本, 是否成功)。"""
    import json

    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return ("解析失败", False)

    if not isinstance(data, dict):
        return ("数据格式异常", False)

    infos = data.get("balance_infos") or []
    if not isinstance(infos, list) or not infos:
        return ("无余额信息", False)

    info = infos[0]
    currency = str(info.get("currency", "CNY")).upper()
    total = info.get("total_balance", "0")
    symbol = {"CNY": "¥", "USD": "$"}.get(currency, "")
    try:
        amount = f"{float(total):.2f}"
    except (TypeError, ValueError):
        amount = str(total)
    suffix = "" if symbol else f" {currency}"
    return (f"{symbol}{amount}{suffix}", True)
