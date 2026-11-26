"""用 Edge/Chrome 无头浏览器通过 CDP 截取真实页面（含登录态）。

前置条件：应用已在 --base 指定的地址运行。
用法示例：
    python tools/screenshot.py --base http://127.0.0.1:5001 --out docs/images \
        --shot "login=/login@" --shot "activities=/activities@s1"

依赖：websocket-client（仅开发截图使用，不进入项目运行依赖）。
"""

from __future__ import annotations

import argparse
import base64
import http.cookiejar
import json
import subprocess
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import websocket

EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


def find_browser() -> str:
    for path in EDGE_PATHS:
        if Path(path).exists():
            return path
    raise SystemExit("未找到 Edge/Chrome 可执行文件")


def session_cookie(base: str, username: str) -> tuple[str, str]:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    body = urllib.parse.urlencode({"username": username}).encode()
    opener.open(base + "/login", body, timeout=15).read()
    for cookie in jar:
        if cookie.name.endswith("session"):
            return cookie.name, cookie.value
    raise RuntimeError(f"登录 {username} 未取得 session cookie")


class CDP:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=30)
        self._id = 0

    def send(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        message_id = self._id
        self.ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(f"{method} 失败：{message['error']}")
                return message.get("result", {})

    def close(self) -> None:
        self.ws.close()


def http_json(url: str, method: str = "GET"):
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_debugger(port: int, timeout: float = 20) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            http_json(f"http://127.0.0.1:{port}/json/version")
            return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("浏览器调试端口未就绪")


def wait_ready(cdp: CDP, timeout: float = 15) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = cdp.send(
            "Runtime.evaluate",
            {"expression": "document.readyState", "returnByValue": True},
        )
        if result.get("result", {}).get("value") == "complete":
            return
        time.sleep(0.2)
    raise RuntimeError("页面加载超时")


def capture(base: str, path: str, cookie: tuple[str, str], output: Path, port: int) -> None:
    target = http_json(f"http://127.0.0.1:{port}/json/new?about:blank", method="PUT")
    cdp = CDP(target["webSocketDebuggerUrl"])
    try:
        cdp.send("Page.enable")
        cdp.send("Network.enable")
        cdp.send(
            "Network.setCookie",
            {"name": cookie[0], "value": cookie[1], "url": base + "/", "path": "/"},
        )
        cdp.send("Emulation.setDeviceMetricsOverride",
                 {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False})
        cdp.send("Page.navigate", {"url": base + path})
        wait_ready(cdp)
        time.sleep(0.45)

        metrics = cdp.send("Page.getLayoutMetrics")
        content = metrics.get("cssContentSize") or metrics.get("contentSize") or {}
        height = int(content.get("height") or 1000)
        height = max(900, min(height + 40, 3200))
        cdp.send("Emulation.setDeviceMetricsOverride",
                 {"width": 1440, "height": height, "deviceScaleFactor": 1, "mobile": False})
        time.sleep(0.35)
        result = cdp.send("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        output.write_bytes(base64.b64decode(result["data"]))
        print(f"captured {output.name} ({height}px)")
    finally:
        cdp.close()
        try:
            urllib.request.urlopen(
                f"http://127.0.0.1:{port}/json/close/{target['id']}", timeout=5
            ).read()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:5001")
    parser.add_argument("--out", default="docs/images")
    parser.add_argument("--port", type=int, default=9333)
    parser.add_argument(
        "--shot",
        action="append",
        default=[],
        help="格式 name=path@username，例如 activities=/activities@s1；登录页用 @ 结尾",
    )
    args = parser.parse_args()

    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = Path.home() / "AppData" / "Local" / "Temp" / f"campusevent-shot-{uuid.uuid4().hex[:6]}"

    browser = subprocess.Popen(
        [
            find_browser(),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--disable-extensions",
            f"--remote-debugging-port={args.port}",
            f"--user-data-dir={profile}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        wait_for_debugger(args.port)
        cookies: dict[str, tuple[str, str]] = {}
        for spec in args.shot:
            name, _, target = spec.partition("=")
            path, _, username = target.rpartition("@")
            cookie: tuple[str, str] = ("", "")
            if username:
                if username not in cookies:
                    cookies[username] = session_cookie(args.base, username)
                cookie = cookies[username]
            capture(args.base, path or "/", cookie, output_dir / f"{name}.png", args.port)
    finally:
        browser.terminate()
        try:
            browser.wait(timeout=8)
        except subprocess.TimeoutExpired:
            browser.kill()


if __name__ == "__main__":
    main()
