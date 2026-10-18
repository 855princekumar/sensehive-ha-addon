# Changelog

## 1.8.0 (SenseHive 1.8.0)

- Update SenseHive to 1.8.0: https://github.com/855princekumar/sense-hive/releases/tag/v1.8.0
- **Add heartbeat nodes from Home Assistant:** set **Heartbeat master key** to `auto`
  (a private fleet key, kept in the add-on's data and in backups), then
  **Heartbeats, Add node**: a join token per node, or many as a CSV. On each node:
  `git clone` the heartbeat agent and `sudo python3 setup.py`. Nodes of other
  SenseHives on the same broker never appear.
- New options **Heartbeat broker username / password** for a broker that needs a login.

## 1.7.0 (SenseHive 1.7.0)

- Update SenseHive to 1.7.0: https://github.com/855princekumar/sense-hive/releases/tag/v1.7.0
- **Secure topics**: devices publish encrypted and signed messages under
  `sensehive/secure/...` with a key SenseHive issues, and their topics appear
  by themselves. Generate keys in bulk with CSV download, revoke, show again
  with your password. Code for ESP32, MicroPython, Node-RED and Python:
  https://github.com/855princekumar/sense-hive/blob/main/docs/SECURE-TOPICS.md
- Topic logs has two cards: **Open topics** (added by hand) and **Secure topics**
- Heartbeat recycle bin: hide retired nodes, restore them, see when one comes back
- The keys are encrypted with SenseHive's secret key in `/data`, which is in Home
  Assistant backups

## 1.6.1 (SenseHive 1.6.1)

- Update SenseHive to 1.6.1: https://github.com/855princekumar/sense-hive/releases/tag/v1.6.1
- Heartbeat history always shows an outage that is still going on: how long an
  offline or silent node has been down since its last heartbeat, also when that
  was before the chosen range

## 1.6.0 (SenseHive 1.6.0)

- Update SenseHive to 1.6.0: https://github.com/855princekumar/sense-hive/releases/tag/v1.6.0
- **Heartbeats for edge nodes** from the add-on Configuration tab: heartbeat master
  key, API token and broker. Nodes running the
  [MQTT heartbeat agent](https://github.com/855princekumar/mqtt-heartbeat-service)
  appear by themselves as online, offline or silent; invalid keys keep it off
  and are never printed
- Heartbeat history: charts from 1 minute to 30 days with breaks, uptime and
  delivery delay; CSV export for one, selected or all nodes (SenseHive 1.5)
- Two cards on the dashboard switch between Topic logs and Heartbeats with a
  smooth fade; an (i) guide on each; filter by online, offline or silent
- Every dialog fits the screen at any size and zoom
- Hardened against hostile input: payload size cap, per-node flood limit, API
  token lockout, CSV formula escaping, request size limit, more security headers
- Optional **admin password** for direct port access (first password of a new
  database)

## 1.5.0 (SenseHive 1.4.2)

- Update SenseHive to 1.4.2: https://github.com/855princekumar/sense-hive/releases/tag/v1.4.2
- New look (light by default, dark remembered), a layout that fits phones to desktops, and a Heartbeats link
- Browser code now ships inside the image (no CDN) under a strict Content Security Policy; works the same through ingress
- Salted password hashes and sign-in lockout (SenseHive 1.3), safe topic names and no error details shown to the browser
- Optional heartbeat receiver for edge nodes (off unless configured)

## 1.4.0 (SenseHive 1.1.0)

> **Before updating from 1.3.x:** export the CSV of any topic you want to keep.
> Earlier versions stored data inside the container, so it does not survive the update.
> From 1.4.0 on, data is kept in `/data` and included in backups.

- Opens inside Home Assistant via Ingress (sidebar panel); no second login needed
- Connects to the Mosquitto broker add-on automatically (no manual broker setup)
- Broker, credentials and timezone configurable from the add-on Configuration tab
- Database stored in `/data`: survives updates and is included in Home Assistant backups
- AppArmor profile; direct port access disabled by default
- Single add-on for amd64 and aarch64 (multi-arch image)
- SenseHive 1.1.0: topic stats, tags, node grouping, LWT device status,
  data retention, SQLite WAL mode, wildcard topic logging and fixed JSON
  payload wrapping
