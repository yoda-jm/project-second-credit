#!/usr/bin/env python3
"""Serves a folder the way GitHub Pages does for the web build's tests: static files, no special headers, and gzip for
every client that accepts it (Pages compresses even the .pck packs; the browser unzips them, Godot must not again).
Usage: tools/serve_pages.py <folder> <port>"""
import gzip
import http.server
import socketserver
import sys
from functools import partial


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        if "gzip" not in self.headers.get("Accept-Encoding", ""):
            return super().send_head()
        path = self.translate_path(self.path)
        try:
            with open(path, "rb") as f:
                data = gzip.compress(f.read(), 6)
        except (IsADirectoryError, FileNotFoundError, PermissionError):
            return super().send_head()
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        return None

    def log_message(self, *args):
        pass


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    folder, port = sys.argv[1], int(sys.argv[2])
    Server(("127.0.0.1", port), partial(Handler, directory=folder)).serve_forever()
