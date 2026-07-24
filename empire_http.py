#!/usr/bin/env python3
"""商业帝国 — MCP HTTP Server"""
import sys, os
_empire_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _empire_dir)
os.environ["PYTHONIOENCODING"] = "utf-8"

# Load empire.py game logic
with open(os.path.join(_empire_dir, "empire.py"), encoding="utf-8") as f:
    _src = f.read()
exec(_src[:_src.index("if __name__")])

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, time, uuid, threading

SESSIONS = {}; SESSIONS_LOCK = threading.Lock()
PORT = int(os.environ.get("EMPIRE_PORT", 8765))
API_KEY = os.environ.get("EMPIRE_KEY", "")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, f, *a): pass
    def _cors(self): self.send_header("Access-Control-Allow-Origin", "*")
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status); self.send_header("Content-Type", "application/json"); self._cors()
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_OPTIONS(self):
        self.send_response(204)
        for h, v in [("Access-Control-Allow-Methods","GET,POST,DELETE,OPTIONS"),("Access-Control-Allow-Headers","Content-Type,Authorization,X-API-Key,Mcp-Session-Id,Accept"),("Access-Control-Expose-Headers","Mcp-Session-Id")]:
            self.send_header(h, v)
        self._cors(); self.end_headers()
    def do_GET(self):
        self.send_response(200); self.send_header("Content-type","text/plain; charset=utf-8"); self._cors(); self.end_headers()
        self.wfile.write(f"商业帝国 v5.2 端口{PORT}\n".encode())
    def do_POST(self):
        if API_KEY:
            key = self.headers.get("X-API-Key","") or self.headers.get("Authorization","").replace("Bearer ","")
            if key != API_KEY: self._send_json({"jsonrpc":"2.0","error":{"code":-32001,"message":"Invalid key"}},401); return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}
        method = body.get("method",""); rid = body.get("id")
        gpt = body.get("tool","")
        if gpt: self._send_json({"result":{"content":[{"type":"text","text":call_tool(gpt,body.get("arguments",{}))}]}}); return
        if method == "initialize":
            self._send_json({"jsonrpc":"2.0","id":rid,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"商业帝国","version":"5.2"}}})
        elif method == "tools/list": self._send_json({"jsonrpc":"2.0","id":rid,"result":{"tools":TOOLS}})
        elif method == "tools/call":
            name = body["params"]["name"]; args = body["params"].get("arguments",{})
            text = call_tool(name, args)
            if text is None: text = f"Warning: {name} returned None"
            self._send_json({"jsonrpc":"2.0","id":rid,"result":{"content":[{"type":"text","text":text}]}})
        elif method == "notifications/initialized": self._send_json({"jsonrpc":"2.0"}, session_id=None); return
        elif method == "ping": self._send_json({"jsonrpc":"2.0","id":rid,"result":{}})
        else: self._send_json({"jsonrpc":"2.0","id":rid,"error":{"code":-32601,"message":f"Unknown: {method}"}},400)

if __name__ == "__main__":
    import io
    try: sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except: pass
    print(f"商业帝国 v5.2 HTTP Server 端口{PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
