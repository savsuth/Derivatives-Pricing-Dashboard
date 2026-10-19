"""Local stand-in for Vercel: serves the static page and routes /api/quote to api/quote.py.

Usage: python3 dev_server.py [port]   (default 3000)
"""
import importlib.util
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("quote", ROOT / "api" / "quote.py")
quote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quote)


class Router(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/quote"):
            return quote.handler.do_GET(self)
        return super().do_GET()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    print(f"Serving on http://localhost:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), partial(Router, directory=str(ROOT))).serve_forever()
