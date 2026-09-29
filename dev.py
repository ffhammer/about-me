#!/usr/bin/env python3
"""Dev daemon: rebuild on save + serve site/ + auto-reload open browsers (laptop and phone).

Watches content/, templates/, site/assets/*.css|js and build.py.
The reload snippet is injected only while serving, so built files stay clean.
Usually started via ./dev.sh (runs inside `screen`).
"""
import functools
import importlib
import socket
import threading
import time
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import build

PORT = 8000
ROOT = Path(__file__).resolve().parent
WATCH = [ROOT / "content", ROOT / "templates", ROOT / "build.py", ROOT / "site" / "assets"]
version = str(time.time())  # changes on every rebuild; browsers poll it

RELOAD = b"""<script>(()=>{let v;setInterval(async()=>{try{const r=await fetch('/__version',{cache:'no-store'});
const t=await r.text();if(v&&t!==v)location.reload();v=t}catch(e){}},800)})();</script>"""


def snapshot() -> dict:
    files = {}
    for w in WATCH:
        for p in ([w] if w.is_file() else w.rglob("*")):
            if p.is_file() and p.suffix in {".md", ".html", ".py", ".css", ".js"}:
                files[p] = p.stat().st_mtime
    return files


def rebuild():
    global version
    try:
        importlib.reload(build)  # pick up edits to build.py itself
        built = build.build()
        version = str(time.time())
        print(time.strftime("%H:%M:%S"), "rebuilt", ", ".join(str(p.relative_to(ROOT)) for p in built), flush=True)
    except Exception:
        print(time.strftime("%H:%M:%S"), "BUILD FAILED (page keeps the last good version):", flush=True)
        traceback.print_exc()


def watch():
    last = snapshot()
    while True:
        time.sleep(0.4)
        now = snapshot()
        if now != last:
            last = now
            rebuild()


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the screen quiet
        pass

    def do_GET(self):
        if self.path == "/__version":
            body = version.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        path = Path(self.translate_path(self.path))
        if path.is_dir():
            path = path / "index.html"
        if path.suffix == ".html" and path.is_file():
            if not self.path.split("?")[0].endswith(("/", ".html")):  # /work_at_form -> /work_at_form/
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return
            body = path.read_bytes().replace(b"</body>", RELOAD + b"</body>")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


def lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "localhost"


if __name__ == "__main__":
    rebuild()
    threading.Thread(target=watch, daemon=True).start()
    handler = functools.partial(Handler, directory=str(ROOT / "site"))
    server = ThreadingHTTPServer(("0.0.0.0", PORT), handler)
    print(f"Serving  http://localhost:{PORT}/   phone: http://{lan_ip()}:{PORT}/", flush=True)
    print("Edit content/*.md and save. Ctrl-C to stop.", flush=True)
    server.serve_forever()
