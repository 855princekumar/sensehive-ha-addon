# Changelog

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
