"""Servidor de chat HTTP para red local (solo biblioteca estándar)."""
import argparse
import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .page import PAGE

MAX_MESSAGES = 500
MAX_TEXT = 2000
MAX_NAME = 32


class ChatRoom:
    """Mensajes, borradores "en vivo" y lista de hosts conectados."""

    DRAFT_TTL = 30.0   # s sin actividad para ocultar un borrador
    CLIENT_TTL = 40.0  # s sin peticiones para considerar desconectado

    def __init__(self):
        self.messages = []
        self.next_id = 1
        self.drafts = {}   # cid -> {cid, name, text, ip, ts}
        self.clients = {}  # cid -> {cid, name, ip, seen}
        self.seq = {}      # cid -> último seq visto (descarta peticiones viejas)
        self.version = 0   # cambia con cada mensaje, borrador o conexión
        self.cond = threading.Condition()

    # --- internos (llamar con el lock tomado) ---
    def _bump(self):
        self.version += 1
        self.cond.notify_all()

    def _fresh(self, cid, seq):
        if seq <= self.seq.get(cid, -1):
            return False
        self.seq[cid] = seq
        return True

    def _touch(self, cid, name, ip):
        """Marca al cliente como activo. True si es nuevo o cambió de nombre."""
        now = time.time()
        c = self.clients.get(cid)
        if c is None or c["name"] != name:
            self.clients[cid] = {"cid": cid, "name": name, "ip": ip, "seen": now}
            if cid in self.drafts:
                self.drafts[cid]["name"] = name
            return True
        c["seen"] = now
        return False

    def _prune(self):
        limit = time.time() - self.CLIENT_TTL
        gone = [cid for cid, c in self.clients.items() if c["seen"] < limit]
        for cid in gone:
            del self.clients[cid]
            self.drafts.pop(cid, None)
            self.seq.pop(cid, None)
        return bool(gone)

    # --- API ---
    def add(self, cid, seq, name, text, ip):
        with self.cond:
            self._fresh(cid, seq)
            self._touch(cid, name, ip)
            msg = {"id": self.next_id, "cid": cid, "name": name, "text": text,
                   "ip": ip, "ts": time.time()}
            self.next_id += 1
            self.messages.append(msg)
            del self.messages[:-MAX_MESSAGES]
            self.drafts.pop(cid, None)
            self._bump()
            return msg

    def set_draft(self, cid, seq, name, text, ip):
        with self.cond:
            changed = self._touch(cid, name, ip)
            if self._fresh(cid, seq):
                if text:
                    self.drafts[cid] = {"cid": cid, "name": name, "text": text,
                                        "ip": ip, "ts": time.time()}
                    changed = True
                elif self.drafts.pop(cid, None) is not None:
                    changed = True
            if changed:
                self._bump()

    def leave(self, cid):
        with self.cond:
            if self.clients.pop(cid, None) is not None:
                self.drafts.pop(cid, None)
                self._bump()

    def poll(self, since, version, cid, name, ip, wait=25.0):
        """Long-polling: espera hasta que algo cambie (o `wait` s)."""
        with self.cond:
            if self._touch(cid, name, ip) | self._prune():
                self._bump()
            self.cond.wait_for(lambda: self.version != version, timeout=wait)
            if cid in self.clients:  # solo refresca; no revive ni renombra
                self.clients[cid]["seen"] = time.time()
            limit = time.time() - self.DRAFT_TTL
            return {
                "v": self.version,
                "messages": [m for m in self.messages if m["id"] > since],
                "drafts": [d for d in self.drafts.values() if d["ts"] > limit],
                "clients": sorted(
                    ({"cid": c["cid"], "name": c["name"], "ip": c["ip"]}
                     for c in self.clients.values()),
                    key=lambda c: (c["ip"], c["name"])),
            }


def make_handler(room):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = urlparse(self.path)
            q = parse_qs(url.query)
            ip = self.client_address[0]

            def qint(key):
                try:
                    return int(q.get(key, ["0"])[0])
                except ValueError:
                    return 0

            def qstr(key, limit):
                return q.get(key, [""])[0].strip()[:limit]

            if url.path == "/":
                self._send(200, PAGE, "text/html; charset=utf-8")
            elif url.path == "/whoami":
                self._send(200, json.dumps({"ip": ip}))
            elif url.path == "/poll":
                cid = qstr("cid", 64) or ip
                name = qstr("name", MAX_NAME) or ip
                self._send(200, json.dumps(
                    room.poll(qint("since"), qint("v"), cid, name, ip)))
            else:
                self._send(404, '{"error":"not found"}')

        def do_POST(self):
            path = urlparse(self.path).path
            if path not in ("/send", "/typing", "/leave"):
                return self._send(404, '{"error":"not found"}')
            ip = self.client_address[0]
            try:
                length = min(int(self.headers.get("Content-Length", 0)), 16384)
                data = json.loads(self.rfile.read(length) or b"{}")
                cid = str(data.get("cid", ""))[:64] or ip
                seq = int(data.get("seq", 0))
                name = str(data.get("name", "")).strip()[:MAX_NAME] or ip
                text = str(data.get("text", ""))[:MAX_TEXT]
            except (ValueError, TypeError, json.JSONDecodeError):
                return self._send(400, '{"error":"bad request"}')

            if path == "/leave":
                room.leave(cid)
                return self._send(200, '{"ok":true}')
            if path == "/typing":
                room.set_draft(cid, seq, name, text, ip)
                return self._send(200, '{"ok":true}')

            text = text.strip()
            if not text:
                room.set_draft(cid, seq, name, "", ip)
                return self._send(400, '{"error":"empty"}')
            msg = room.add(cid, seq, name, text, ip)
            print(f"[{ip}] {name}: {text}", flush=True)
            self._send(200, json.dumps(msg))

    return Handler


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # no envía nada
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def serve(host="0.0.0.0", port=8000):
    room = ChatRoom()
    try:
        server = ThreadingHTTPServer((host, port), make_handler(room))
    except OSError as e:
        raise SystemExit(f"No se pudo abrir el puerto {port}: {e.strerror}. "
                         f"Prueba con otro, ej. python3 -m chat {port + 1}")
    server.daemon_threads = True
    print(f"HTTP Chat escuchando en {host}:{port}")
    print(f"  Local:      http://127.0.0.1:{port}")
    print(f"  Red local:  http://{lan_ip()}:{port}")
    print("Ctrl+C para detener.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido.")
    finally:
        server.server_close()


def main():
    p = argparse.ArgumentParser(prog="httpchat", description="Chat HTTP para red local")
    p.add_argument("-H", "--host", default="0.0.0.0", help="interfaz (default 0.0.0.0)")
    p.add_argument("port_pos", nargs="?", type=int, metavar="PUERTO",
                   help="puerto (ej. 8081); equivale a -p")
    p.add_argument("-p", "--port", type=int, default=8000, help="puerto (default 8000)")
    a = p.parse_args()
    serve(a.host, a.port_pos or a.port)


if __name__ == "__main__":
    main()
