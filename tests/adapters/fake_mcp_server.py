"""Servidor MCP stdio falso: initialize, tools/list e tools/call (big, small, image, structured)."""
import json
import sys

for line in sys.stdin:
    msg = json.loads(line)
    mid, method = msg.get("id"), msg.get("method")
    if mid is None:
        continue
    if method == "initialize":
        res = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "fake", "version": "0"}}
    elif method == "tools/list":
        res = {"tools": [{"name": n, "inputSchema": {"type": "object"}} for n in ("big", "small", "image", "structured")]}
    elif method == "tools/call":
        name = msg["params"]["name"]
        if name == "big":
            res = {"content": [{"type": "text", "text": "x" * 50000 + "\nsrc/lib.rs:12:5 error[E0308]"}], "isError": True}
        elif name == "image":
            res = {"content": [{"type": "text", "text": "\x01" * 20000},
                               {"type": "image", "data": "QUJD", "mimeType": "image/png"}]}
        elif name == "structured":
            res = {"content": [{"type": "text", "text": "s" * 30000}], "structuredContent": {"v": "s" * 30000}}
        else:
            res = {"content": [{"type": "text", "text": "ok"}]}
    else:
        print(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "no"}}), flush=True)
        continue
    print(json.dumps({"jsonrpc": "2.0", "id": mid, "result": res}), flush=True)
