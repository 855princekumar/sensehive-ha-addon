"""Minimal stand-in for the Home Assistant Supervisor used by the sandbox test.

- GET /services/mqtt         -> Mosquitto credentials (requires the add-on's SUPERVISOR_TOKEN)
- /api/hassio_ingress/<tok>/ -> reverse proxy to the add-on, like Home Assistant ingress
Runs at 172.30.32.2 inside the test network, the same address as the real Supervisor.
"""
import json
import re
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ['SUPERVISOR_TOKEN']
ADDON_URL = os.environ.get('ADDON_URL', 'http://sensehive:5000')
MQTT = {
    'host': os.environ.get('MQTT_HOST', 'core-mosquitto'),
    'port': int(os.environ.get('MQTT_PORT', '1883')),
    'ssl': False,
    'protocol': '3.1.1',
    'username': os.environ.get('MQTT_USERNAME', 'addons'),
    'password': os.environ.get('MQTT_PASSWORD', ''),
}
INGRESS_PREFIX = '/api/hassio_ingress/'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


opener = urllib.request.build_opener(NoRedirect)


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body=b'', headers=()):
        self.send_response(status)
        for name, value in headers:
            self.send_header(name, value)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle(self):
        if self.path == '/services/mqtt':
            if self.headers.get('Authorization') != f'Bearer {TOKEN}':
                return self._send(401, b'{"result": "error"}', [('Content-Type', 'application/json')])
            body = json.dumps({'result': 'ok', 'data': MQTT}).encode()
            return self._send(200, body, [('Content-Type', 'application/json')])

        if self.path.startswith(INGRESS_PREFIX):
            rest = self.path[len(INGRESS_PREFIX):]
            _token, _, sub_path = rest.partition('/')
            # Only a plain path under the add-on: no scheme, host, '..' or odd characters,
            # so the mock proxy can never be pointed anywhere else.
            if not re.fullmatch(r"[A-Za-z0-9._~/?=&%,:+-]*", sub_path) or '..' in sub_path or sub_path.startswith('/'):
                return self._send(400, b'bad path')
            length = int(self.headers.get('Content-Length') or 0)
            data = self.rfile.read(length) if length else None
            req = urllib.request.Request(f'{ADDON_URL}/{sub_path}', data=data, method=self.command)
            for name in ('Content-Type', 'Cookie', 'Accept'):
                if self.headers.get(name):
                    req.add_header(name, self.headers[name])
            try:
                res = opener.open(req, timeout=15)
            except urllib.error.HTTPError as e:
                res = e
            headers = [(k, v) for k, v in res.headers.items() if k in ('Content-Type', 'Set-Cookie', 'Location', 'Content-Disposition')]
            return self._send(res.status if hasattr(res, 'status') else res.code, res.read(), headers)

        self._send(404, b'not found')

    do_GET = do_POST = do_PUT = do_DELETE = _handle

    def log_message(self, fmt, *args):
        print(f'[supervisor] {self.command} {self.path} -> {fmt % args}', flush=True)


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 80), Handler).serve_forever()
