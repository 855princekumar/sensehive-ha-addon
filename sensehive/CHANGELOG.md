# Changelog

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
