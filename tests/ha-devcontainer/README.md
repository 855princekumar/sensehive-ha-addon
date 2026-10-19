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

# 3. The same as CI: onboarding, Mosquitto, SenseHive in the sidebar, the 21 checks
docker cp tests/ha-devcontainer/. ha-dev:/root/
docker exec -e E2E_USER=e2e -e E2E_PASSWORD=choose-one ha-dev bash /root/setup_ha.sh
docker exec ha-dev bash /root/e2e.sh

# 4. A browser in Home Assistant (needs a SenseHive checkout and Playwright on this machine;
#    publish port 80 of the devcontainer, e.g. -p 7080:80 in step 1)
python tests/ha-devcontainer/ha_browser_e2e.py --ha http://127.0.0.1:7080 --user e2e     --password choose-one --sensehive ../sense-hive
```

`ingress_session.py` asks Home Assistant Core for an ingress session over its
WebSocket API, the same way the frontend does. The Supervisor only accepts
ingress sessions from Core.

`ha_browser_e2e.py` signs in to Home Assistant's own page, opens SenseHive from
the sidebar panel, adds a node with Add Node, runs SenseHive's emulated fleet
(`sensehive-demo`) inside the add-on on Home Assistant's Mosquitto, and runs
SenseHive's live browser checks (`tools/live_e2e.py`) inside the panel on
phone, tablet, laptop and desktop.

CI runs all of it on every change (job **Real Home Assistant (Supervisor and
Core), with a browser**). Result for add-on 1.8.1 on Home Assistant 2026.10.2 /
Supervisor 2026.10.3: **21/21** ingress, data, restart, backup and security
checks, **30/30** browser checks.
