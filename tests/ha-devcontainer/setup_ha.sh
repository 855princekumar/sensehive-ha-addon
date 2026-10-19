#!/bin/bash
# A fresh Home Assistant, set up the way a person does it: the onboarding user,
# the Mosquitto broker add-on, SenseHive from this repository, shown in the
# sidebar. Runs inside the apps devcontainer once Core answers on localhost:80.
#   E2E_USER=e2e E2E_PASSWORD=... bash setup_ha.sh
set -euo pipefail
: "${E2E_USER:?}" "${E2E_PASSWORD:?}"
command -v python3 >/dev/null && python3 -c 'import websocket' 2>/dev/null || \
  { apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-websocket curl >/dev/null; }
CID=http://localhost/

echo "== onboarding"
code=$(curl -sf -X POST localhost/api/onboarding/users -H 'Content-Type: application/json' \
  -d "{\"client_id\":\"$CID\",\"name\":\"E2E\",\"username\":\"$E2E_USER\",\"password\":\"$E2E_PASSWORD\",\"language\":\"en\"}" |
  python3 -c 'import sys,json;print(json.load(sys.stdin)["auth_code"])')
TOKEN=$(curl -sf -X POST localhost/auth/token -d "grant_type=authorization_code&code=$code&client_id=$CID" |
  python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
# A long-lived token for the checks (an access token expires after 30 minutes)
python3 - "$TOKEN" > /root/ha_token <<'PY'
import json, sys, websocket
ws = websocket.create_connection("ws://localhost/api/websocket")
ws.recv()
ws.send(json.dumps({"type": "auth", "access_token": sys.argv[1]}))
assert json.loads(ws.recv())["type"] == "auth_ok"
ws.send(json.dumps({"id": 1, "type": "auth/long_lived_access_token", "client_name": "sensehive-e2e", "lifespan": 7}))
print(json.loads(ws.recv())["result"])
PY
chmod 600 /root/ha_token
auth=(-H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json')
curl -sf -X POST localhost/api/onboarding/core_config "${auth[@]}" -d '{}' >/dev/null
curl -sf -X POST localhost/api/onboarding/analytics "${auth[@]}" -d '{}' >/dev/null
curl -sf -X POST localhost/api/onboarding/integration "${auth[@]}" -d "{\"client_id\":\"$CID\",\"redirect_uri\":\"${CID}?auth_callback=1\"}" >/dev/null || true
echo "   user $E2E_USER onboarded"

echo "== Mosquitto broker add-on"
ha store reload >/dev/null
ha apps install core_mosquitto >/dev/null
ha apps start core_mosquitto >/dev/null
echo "== SenseHive from this repository"
ha apps install local_sensehive >/dev/null
docker exec hassio_cli sh -c 'curl -sf -X POST -H "Authorization: Bearer $SUPERVISOR_TOKEN" -H "Content-Type: application/json" \
  -d "{\"ingress_panel\": true}" http://supervisor/addons/local_sensehive/options' >/dev/null
ha apps start local_sensehive >/dev/null
for i in $(seq 1 60); do
  ha apps info local_sensehive --raw-json | grep -q '"state":"started"' && break; sleep 2
done
ha apps info local_sensehive --raw-json | python3 -c 'import sys,json;d=json.load(sys.stdin)["data"];print("   SenseHive", d["version"], d["state"], "panel" if d["ingress_panel"] else "no panel")'
