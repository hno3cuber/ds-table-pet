"""从 PyPI JSON API 拉取指定包的最新稳定 wheel，供离线安装（沙盒里 pip 直接装会因 PEP 714 metadata 下载被拒）。"""
import json
import re
import sys
import urllib.request
from pathlib import Path

PACKAGES = [
    "pyinstaller",
    "pyinstaller-hooks-contrib",
    "altgraph",
    "packaging",
    "pefile",
    "pywin32-ctypes",
    "setuptools",
]

OUT = Path(".wheels")
OUT.mkdir(exist_ok=True)


def fetch_json(url: str, tries: int = 5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if i == tries - 1:
                raise
            import time
            time.sleep(2 * (i + 1))


def best_wheel(data):
    """选平台匹配、非 rc/beta/dev 的最新 cpX/abi3/py3 wheel 或纯 py wheel。"""
    files = data.get("releases", {}).get(data["info"]["version"], [])
    candidates = []
    for f in files:
        name = f["filename"]
        if not name.endswith(".whl"):
            continue
        if not f.get("url"):
            continue
        if re.search(r"(rc|beta|alpha|dev|a\d|b\d|pre)\d*", name, re.I):
            continue
        if "win_amd64" not in name and "py3-none-any" not in name and "none-any" not in name:
            continue
        candidates.append(f)
    if not candidates:
        # 回退：任意 wheel
        candidates = [f for f in files if f.get("url") and f["filename"].endswith(".whl")]
    if not candidates:
        raise RuntimeError(f"no wheel for {data['info']['name']}")
    # 优先 win_amd64，其次通用
    candidates.sort(key=lambda f: (0, 0) if "win_amd64" in f["filename"] else (1, 0))
    return candidates[0]


def download(url: str, dest: Path):
    if dest.exists() and dest.stat().st_size > 1000:
        return
    for i in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                dest.write_bytes(r.read())
            return
        except Exception:
            if i == 4:
                raise
            import time
            time.sleep(2 * (i + 1))


def main():
    for pkg in PACKAGES:
        data = fetch_json(f"https://pypi.org/pypi/{pkg}/json")
        wheel = best_wheel(data)
        dest = OUT / wheel["filename"]
        print(f"-> {pkg} {data['info']['version']} {wheel['filename']}")
        sys.stdout.flush()
        download(wheel["url"], dest)
        print(f"   downloaded {dest.stat().st_size}")
        sys.stdout.flush()
    print("ALL DONE")


if __name__ == "__main__":
    main()
