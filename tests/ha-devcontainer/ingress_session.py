import json, websocket
token = open("/root/ha_token").read().strip()
ws = websocket.create_connection("ws://localhost/api/websocket")
ws.recv()
ws.send(json.dumps({"type": "auth", "access_token": token}))
assert json.loads(ws.recv())["type"] == "auth_ok"
ws.send(json.dumps({"id": 1, "type": "supervisor/api", "endpoint": "/ingress/session", "method": "post"}))
res = json.loads(ws.recv())
print(res["result"]["session"])
