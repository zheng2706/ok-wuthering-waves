"""
ok-ww HTTP API Server.
Exposes ok-ww framework capabilities via REST API.

Usage:
    cd D:\\software\\ok-ww-custom
    D:\\software\\ok-ww\\data\\apps\\ok-ww\\python\\python.exe server.py
"""

import ctypes
import json
import logging
import sys
import os
import traceback
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# CRITICAL: Set DPI awareness BEFORE any window/capture operations.
# Without this, GetClientRect returns logical pixels (e.g., 2560x1440)
# instead of physical pixels (e.g., 3840x2160 at 150% DPI),
# causing PrintWindowCapture to only capture the top-left portion.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Setup logging before any imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.log"),
                            encoding='utf-8'),
    ]
)
logger = logging.getLogger("ww_api")

# Import context (triggers ok-ww framework setup via sys.path)
from ww_context import WWContext

HOST = "127.0.0.1"
PORT = 8270

# Global context instance
ctx: WWContext = None


class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for ok-ww API."""

    def log_message(self, format, *args):
        logger.debug(f"{self.address_string()} {format % args}")

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        # Try UTF-8 first, fall back to GBK (Windows terminal encoding)
        for enc in ('utf-8', 'gbk', 'latin-1'):
            try:
                return json.loads(raw.decode(enc))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        return json.loads(raw.decode('utf-8', errors='replace'))

    def _route(self, method):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        params = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}

        try:
            # GET routes
            if method == 'GET':
                if path == '/status':
                    return self._send_json(ctx.get_status())
                elif path == '/screenshot':
                    x = float(params.get('x', 0))
                    y = float(params.get('y', 0))
                    to_x = float(params.get('to_x', 1))
                    to_y = float(params.get('to_y', 1))
                    return self._send_json(ctx.screenshot(x, y, to_x, to_y))
                elif path == '/task/list':
                    return self._send_json({"tasks": ctx.list_tasks()})
                elif path == '/task/status':
                    return self._send_json(ctx.task_status())
                elif path == '/script/list':
                    return self._send_json({"scripts": ctx.list_scripts()})
                elif path == '/logs':
                    lines = int(params.get('lines', 50))
                    return self._send_json({"lines": ctx.get_logs(lines)})
                elif path == '/refresh':
                    connected = ctx.refresh_connection()
                    return self._send_json({"connected": connected})
                elif path == '/start_game':
                    return self._send_json(ctx.start_game())

            # POST routes
            elif method == 'POST':
                body = self._read_json()

                if path == '/click':
                    result = ctx.click(
                        float(body.get('x', 0.5)),
                        float(body.get('y', 0.5)),
                        float(body.get('after_sleep', 0))
                    )
                    return self._send_json({"ok": result})

                elif path == '/send_key':
                    result = ctx.send_key(
                        body.get('key', ''),
                        float(body.get('after_sleep', 0)),
                        float(body.get('down_time', 0.02))
                    )
                    return self._send_json({"ok": result})

                elif path == '/ocr':
                    boxes = ctx.ocr(
                        float(body.get('x', 0)),
                        float(body.get('y', 0)),
                        float(body.get('to_x', 1)),
                        float(body.get('to_y', 1)),
                        body.get('match')
                    )
                    return self._send_json({"boxes": boxes})

                elif path == '/scroll':
                    result = ctx.scroll(
                        float(body.get('x', 0.5)),
                        float(body.get('y', 0.5)),
                        int(body.get('count', 3))
                    )
                    return self._send_json({"ok": result})

                elif path == '/find_feature':
                    boxes = ctx.find_feature(
                        body.get('name', ''),
                        float(body.get('threshold', 0.8))
                    )
                    return self._send_json({"boxes": boxes})

                elif path == '/screenshot':
                    result = ctx.screenshot(
                        float(body.get('x', 0)),
                        float(body.get('y', 0)),
                        float(body.get('to_x', 1)),
                        float(body.get('to_y', 1))
                    )
                    return self._send_json(result)

                elif path == '/task/start':
                    result = ctx.start_task(body.get('name', ''), config=body.get('config'))
                    return self._send_json(result)

                elif path == '/task/stop':
                    result = ctx.stop_task()
                    return self._send_json(result)

                elif path == '/script/run':
                    result = ctx.run_script(body.get('name', ''))
                    return self._send_json(result)

            # 404
            self._send_json({"error": f"Not found: {method} {path}"}, 404)

        except Exception as e:
            logger.error(f"Error handling {method} {path}: {traceback.format_exc()}")
            self._send_json({"error": str(e)}, 500)

    def do_GET(self):
        logger.info(f"GET {self.path}")
        self._route('GET')

    def do_POST(self):
        logger.info(f"POST {self.path}")
        self._route('POST')


def main():
    global ctx

    logger.info("=" * 50)
    logger.info("ok-ww HTTP API Server starting...")
    logger.info(f"Working dir: {os.getcwd()}")
    logger.info(f"API dir: {os.path.dirname(os.path.abspath(__file__))}")

    # Initialize framework using OK class (identical to GUI init)
    from config import config as app_config
    from ok import OK
    app_config['use_gui'] = False
    ok_inst = OK(app_config)
    ok_inst.do_init()
    logger.info("OK.do_init() completed")

    # Create context wrapper using OK's components
    ctx = WWContext(ok_instance=ok_inst)
    try:
        ctx.initialize()
    except Exception as e:
        logger.error(f"Framework init error (non-fatal): {e}")
        logger.info("Server will start anyway.")

    # Start HTTP server
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((HOST, PORT), APIHandler)
    logger.info(f"Server listening on http://{HOST}:{PORT}")
    logger.info("Endpoints: /status /screenshot /click /send_key /ocr /scroll /find_feature")
    logger.info("           /task/list /task/start /task/stop /task/status")
    logger.info("           /script/list /script/run /logs /refresh")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
