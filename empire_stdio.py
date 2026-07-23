#!/usr/bin/env python3
"""商业帝国 — MCP stdio 服务器"""
import sys, os, json, traceback

_empire_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _empire_dir)

# Load empire.py game logic + shared TOOLS/TOOL_MAP
with open(os.path.join(_empire_dir, "empire.py"), encoding="utf-8") as f:
    _src = f.read()
exec(_src[:_src.index("if __name__")])

def send(msg):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def recv():
    line = sys.stdin.readline()
    if not line: return None
    return json.loads(line.strip())

SERVER_INFO = {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}},
    "serverInfo": {"name": "商业帝国", "version": "5.2"}
}

for msg in iter(recv, None):
    method = msg.get("method", ""); rid = msg.get("id")
    try:
        if method == "initialize":
            send({"jsonrpc": "2.0", "id": rid, "result": SERVER_INFO})
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            send({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            name = msg["params"]["name"]; args = msg["params"].get("arguments", {})
            if name in TOOL_MAP:
                try:
                    text = TOOL_MAP[name](args) or ""
                except Exception as e:
                    text = f"Error: {e}\n{traceback.format_exc()}"
                send({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": text}]}})
            else:
                send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Unknown: {name}"}})
        elif method == "ping":
            send({"jsonrpc": "2.0", "id": rid, "result": {}})
        else:
            send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Unknown method: {method}"}})
    except Exception as e:
        send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32603, "message": str(e)}})
