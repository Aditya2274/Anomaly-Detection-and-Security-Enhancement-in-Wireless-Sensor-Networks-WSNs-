#!/usr/bin/env python3
"""TERF Security Operations Console server — serves the live WSN intrusion detection dashboard. Zero external deps.
Run: python3 frontend/server.py 8000   ->   open http://localhost:8000"""
import os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
class H(BaseHTTPRequestHandler):
    def _ok(self, data, ct='text/html; charset=utf-8', code=200):
        self.send_response(code)
        self.send_header('Content-Type', ct)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        try:
            if p in ('/', '/index.html'):
                self._ok(open(INDEX,'rb').read())
            elif p == '/favicon.ico':
                self._ok(b'', code=204)
            else:
                self._ok(b'not found', code=404)
        except Exception as e:
            self._ok(('err '+str(e)).encode(), code=500)
    def log_message(self,*a): pass
if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv)>1 else 8000
    print('TERF console: http://localhost:%d' % port)
    server = HTTPServer(('0.0.0.0', port), H)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down server...')
        server.server_close()
