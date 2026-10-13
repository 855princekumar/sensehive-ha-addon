# End-to-end test in a real Home Assistant

Runs the add-on under a real Supervisor and Home Assistant Core using the official
[apps devcontainer](https://github.com/home-assistant/devcontainer).

```bash
# 1. Start the devcontainer with this repository as a local app repository
docker run -d --privileged --name ha-dev \
  -v ha-dev-docker:/var/lib/docker -v ha-dev-containerd:/var/lib/containerd \
  -v ha-dev-supervisor:/mnt/supervisor --tmpfs /tmp \
  -v "$PWD:/mnt/supervisor/apps/local/sensehive-ha-addon" \
  ghcr.io/home-assistant/devcontainer:6-apps
docker exec -d ha-dev bash -c 'supervisor_run > /tmp/supervisor.log 2>&1'
# wait until `docker exec ha-dev ha core info` shows a version (Core serves on port 80)

# 2. Install Mosquitto and SenseHive
docker exec ha-dev bash -lc 'ha store reload && ha apps install core_mosquitto && ha apps start core_mosquitto'
docker exec ha-dev bash -lc 'ha apps install local_sensehive && ha apps start local_sensehive'

# 3. Onboard a throwaway user and save its token to /root/ha_token, install
#    python3 + python3-websocket, then copy and run the test
docker cp tests/ha-devcontainer/. ha-dev:/root/
docker exec ha-dev bash /root/e2e.sh
```

`ingress_session.py` asks Home Assistant Core for an ingress session over its
WebSocket API, the same way the frontend does. The Supervisor only accepts
ingress sessions from Core.

Result for add-on 1.4.0 (Home Assistant 2026.10.1, Supervisor 2026.10.2): **21/21 passed**.
