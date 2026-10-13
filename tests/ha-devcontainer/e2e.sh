#!/bin/bash
# End-to-end test of the SenseHive add-on inside a real Home Assistant Supervisor.
# Runs inside the HA devcontainer; Home Assistant Core listens on localhost:80.
# Needs /root/ingress_session.py (HA WebSocket supervisor/api -> /ingress/session) and an onboarded user token.
set -u
PASS=0; FAIL=0
check() { if eval "$2"; then echo "  [PASS] $1"; PASS=$((PASS+1)); else echo "  [FAIL] $1"; FAIL=$((FAIL+1)); fi; }
sv() { docker exec hassio_cli sh -c "curl -s -X $1 -H \"Authorization: Bearer \$SUPERVISOR_TOKEN\" http://supervisor$2"; }

ENTRY=$(ha apps info local_sensehive --raw-json | python3 -c 'import sys,json;print(json.load(sys.stdin)["data"]["ingress_entry"])')
SESSION=$(python3 /root/ingress_session.py)  # created by Home Assistant Core over its WebSocket API, like the frontend
BASE="http://localhost${ENTRY}"
ig() { curl -s -b "ingress_session=${SESSION}" -H 'Content-Type: application/json' -X "$1" "${BASE}$2" ${3:+-d "$3"}; }

echo "Ingress through Home Assistant Core"
check "no ingress session -> rejected by Home Assistant" '[ "$(curl -s -o /dev/null -w "%{http_code}" ${BASE}/)" = "401" ]'
check "dashboard loads through HA ingress, no SenseHive login" 'ig GET / | grep -q "Sense-Hive"'
check "login page not shown (dashboard served directly)" '! ig GET / | grep -q "Sign in to continue"'
check "API reachable through ingress" '[ "$(curl -s -o /dev/null -w "%{http_code}" -b ingress_session=${SESSION} ${BASE}/api/nodes)" = "200" ]'
check "health via ingress reports MQTT connected" 'ig GET /api/health | grep -q "\"mqtt_connected\":true"'

echo "Direct access (not through ingress) still requires login"
ADDON_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' app_local_sensehive)
check "direct API call from host network -> 401" '[ "$(curl -s -o /dev/null -w "%{http_code}" http://${ADDON_IP}:5000/api/nodes)" = "401" ]'
check "port 5000 not published on the host by default" '[ -z "$(docker port app_local_sensehive)" ]'

echo "Data flow through Mosquitto app"
for id in $(ig GET /api/nodes | python3 -c 'import sys,json;print(" ".join(str(n["id"]) for n in json.load(sys.stdin)))'); do ig DELETE /api/nodes/$id >/dev/null; done
check "add topic with tag, node and LWT via ingress" 'ig POST /api/nodes "{\"topic\":\"ha/greenhouse/telemetry\",\"tag\":\"environment\",\"node_name\":\"greenhouse-esp32\",\"lwt_topic\":\"ha/greenhouse/status\"}" | grep -q success'
sleep 2
docker exec -i app_local_sensehive python - <<'PY'
import json, os
env = dict(v.split('=', 1) for v in open('/proc/1/environ').read().split('\0') if '=' in v)
import paho.mqtt.client as mqtt
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.username_pw_set(env['DEFAULT_BROKER_USERNAME'], env['DEFAULT_BROKER_PASSWORD'])
c.connect(env['DEFAULT_BROKER_HOST'], int(env['DEFAULT_BROKER_PORT']))
c.loop_start()
for i in range(5):
    c.publish('ha/greenhouse/telemetry', json.dumps({'temperature': 21 + i, 'readings': [1, 2, 3], 'meta': {'fw': '2.%d' % i}}), qos=1).wait_for_publish()
c.publish('ha/greenhouse/status', 'online', qos=1, retain=True).wait_for_publish()
c.loop_stop(); c.disconnect()
PY
sleep 3
NODES=$(ig GET /api/nodes)
check "5 messages logged from Mosquitto" 'echo "$NODES" | python3 -c "import sys,json;n=json.load(sys.stdin)[0];sys.exit(0 if n[\"entry_count\"]==5 else 1)"'
check "LWT online -> topic active" 'echo "$NODES" | grep -q "\"status\":\"active\""'
check "nested JSON stored intact" 'echo "$NODES" | python3 -c "import sys,json;n=json.load(sys.stdin)[0];sys.exit(0 if n[\"last_value\"]=={\"temperature\":25,\"readings\":[1,2,3],\"meta\":{\"fw\":\"2.4\"}} else 1)"'
check "navbar stats: 1 active node" 'ig GET /api/stats | python3 -c "import sys,json;sys.exit(0 if json.load(sys.stdin)[\"nodes\"][\"active\"]==1 else 1)"'
check "CSV export through ingress" 'ig GET /api/nodes/$(echo "$NODES" | python3 -c "import sys,json;print(json.load(sys.stdin)[0][\"id\"])")/export | head -1 | grep -q "Timestamp,Payload"'

echo "Restart and backup"
ha apps restart local_sensehive >/dev/null 2>&1; sleep 10
SESSION=$(python3 /root/ingress_session.py)  # created by Home Assistant Core over its WebSocket API, like the frontend
check "data persists across add-on restart" 'ig GET /api/nodes | python3 -c "import sys,json;sys.exit(0 if json.load(sys.stdin)[0][\"entry_count\"]==5 else 1)"'
BK=$(ha backups new --name sensehive-e2e --app local_sensehive --raw-json 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin)["data"]["slug"])')
check "partial backup of the add-on created" '[ -n "$BK" ]'
check "backup contains the SenseHive add-on" 'ha backups info "$BK" --raw-json | python3 -c "import sys,json;d=json.load(sys.stdin)[\"data\"];sys.exit(0 if any(a[\"slug\"]==\"local_sensehive\" for a in d[\"apps\" if \"apps\" in d else \"addons\"]) else 1)"'

echo "Supervisor view"
INFO=$(ha apps info local_sensehive --raw-json)
check "state started" 'echo "$INFO" | grep -q "\"state\":\"started\""'
check "security rating 8/8" 'echo "$INFO" | python3 -c "import sys,json;sys.exit(0 if json.load(sys.stdin)[\"data\"][\"rating\"]==8 else 1)"'
check "AppArmor profile in use" 'echo "$INFO" | grep -q "\"apparmor\":\"profile\""'
check "no Home Assistant / Supervisor API access" 'echo "$INFO" | python3 -c "import sys,json;d=json.load(sys.stdin)[\"data\"];sys.exit(0 if not d[\"homeassistant_api\"] and not d[\"hassio_api\"] and not d[\"auth_api\"] else 1)"'
check "no resolution-center issues for the add-on" '! ha resolution info --raw-json | grep -q "local_sensehive"'

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
