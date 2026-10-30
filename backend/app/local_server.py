"""
ArogyaSaathi server.
Serves the web app from frontend/ and the JSON API (app/portal/routes.py) on the same origin,
using only the Python standard library plus `cryptography` and `anthropic`.

Run:  python -m app.local_server            (ports from PORT env, default 8000 and 8080)
      python -m app.local_server 9000       (single port)
"""

import json
import os
import socket
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.portal import config, db, routes  # noqa: E402

FRONTEND_DIR = os.path.realpath(os.path.join(os.path.dirname(backend_dir), 'frontend'))
MAX_BODY_BYTES = 1_000_000

MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.webmanifest': 'application/manifest+json',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.webp': 'image/webp',
}

PAGE_ALIASES = {
    '/': 'index.html',
    '/login': 'index.html',
    '/dashboard': 'patient_dashboard.html',
}


class ArogyaHandler(BaseHTTPRequestHandler):
    server_version = 'ArogyaSaathi'
    sys_version = ''

    def _security_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Permissions-Policy', 'microphone=(self), geolocation=(self), camera=()')

    def _send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self._security_headers()
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _read_json(self):
        length = int(self.headers.get('Content-Length') or 0)
        if length > MAX_BODY_BYTES:
            raise ValueError('Request too large')
        if not length:
            return {}
        data = json.loads(self.rfile.read(length).decode('utf-8'))
        return data if isinstance(data, dict) else {}

    def _api(self, method):
        url = urllib.parse.urlparse(self.path)
        query = {k: v[-1] for k, v in urllib.parse.parse_qs(url.query).items()}
        try:
            body = self._read_json() if method == 'POST' else {}
        except (ValueError, UnicodeDecodeError):
            self._send_json(400, {'error': 'Invalid request body.'})
            return True
        try:
            result = routes.handle(method, url.path, query, body, self.headers)
        except Exception as e:  # never leak a stack trace to the client
            print(f'[error] {method} {url.path}: {type(e).__name__}: {e}', file=sys.stderr, flush=True)
            self._send_json(500, {'error': 'Something went wrong on the server. Please try again.'})
            return True
        if result is None:
            return False
        self._send_json(*result)
        return True

    def _static_file(self):
        path = urllib.parse.unquote(urllib.parse.urlparse(self.path).path)
        rel = PAGE_ALIASES.get(path.rstrip('/') or '/', path.lstrip('/'))
        target = os.path.realpath(os.path.join(FRONTEND_DIR, rel))
        # Only files inside frontend/ may be served (blocks ../ traversal to backend secrets)
        if not target.startswith(FRONTEND_DIR + os.sep) or not os.path.isfile(target):
            return None
        return target

    def do_GET(self):
        if self.path.startswith('/api/'):
            if not self._api('GET'):
                self._send_json(404, {'error': 'Route not found'})
            return
        target = self._static_file()
        if not target:
            self._send_json(404, {'error': 'Not found'})
            return
        ext = os.path.splitext(target)[1].lower()
        try:
            with open(target, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', MIME_TYPES.get(ext, 'application/octet-stream'))
            self.send_header('Content-Length', str(len(content)))
            # HTML/JS/CSS revalidate every load so app updates reach phones immediately
            self.send_header('Cache-Control', 'no-cache' if ext in ('.html', '.js', '.css', '.json') else 'public, max-age=86400')
            self._security_headers()
            self.end_headers()
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_HEAD(self):
        target = self._static_file()
        self.send_response(200 if target else 404)
        self.end_headers()

    def do_POST(self):
        if not self._api('POST'):
            self._send_json(404, {'error': 'Route not found'})

    def log_message(self, format, *args):
        pass


class DualStackServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6
    daemon_threads = True

    def server_bind(self):
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except (AttributeError, OSError):
            pass
        super().server_bind()


def create_server(port):
    if config.HOST not in ('::', ''):
        server = ThreadingHTTPServer((config.HOST, port), ArogyaHandler)
        server.daemon_threads = True
        return server
    try:
        return DualStackServer(('::', port), ArogyaHandler)
    except OSError:
        server = ThreadingHTTPServer(('0.0.0.0', port), ArogyaHandler)
        server.daemon_threads = True
        return server


def run(ports):
    db.init()
    if not config.STAFF_SIGNUP_CODE:
        print('⚠️  STAFF_SIGNUP_CODE is not set: ASHA / doctor / officer sign-up is disabled.')
    if not config.ANTHROPIC_API_KEY:
        print('⚠️  ANTHROPIC_API_KEY is not set: the patient AI assistant will reply "not available".')
    servers = []
    for port in ports:
        try:
            server = create_server(port)
        except OSError as e:
            print(f'⚠️  Could not bind to port {port}: {e}')
            continue
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        print(f'🏥 ArogyaSaathi running on http://localhost:{port}', flush=True)
    if not servers:
        print('❌ Could not bind to any port.')
        sys.exit(1)
    print(f'🗄️  Database: {config.DB_PATH}', flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nShutting down...')
        for s in servers:
            s.shutdown()


if __name__ == '__main__':
    run([int(sys.argv[1])] if len(sys.argv) > 1 else config.PORTS)
