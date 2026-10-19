# SenseHive Home Assistant Add-on

[![CI](https://github.com/855princekumar/sensehive-ha-addon/actions/workflows/ci.yml/badge.svg)](https://github.com/855princekumar/sensehive-ha-addon/actions/workflows/ci.yml)
![Supports amd64](https://img.shields.io/badge/amd64-yes-green.svg)
![Supports aarch64](https://img.shields.io/badge/aarch64-yes-green.svg)

Run [SenseHive](https://github.com/855princekumar/sense-hive), a lightweight MQTT topic
logger and dashboard, directly inside Home Assistant OS / Supervised.

[![Add repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2F855princekumar%2Fsensehive-ha-addon)

<p align="center">
  <img src="docs/screenshots/ha-panel-laptop.png" width="72%" alt="SenseHive in the Home Assistant sidebar, connected to the Mosquitto add-on" />
  <img src="docs/screenshots/ha-panel-phone.png" width="20%" alt="SenseHive in the Home Assistant app on a phone" />
</p>

Real screenshots from a real Home Assistant (Supervisor and Core, the Mosquitto add-on, an
emulated fleet of devices), taken by CI on every change.

---

## Features

- **One-click install** for HAOS users, single add-on for amd64 and aarch64 (Raspberry Pi 4/5)
- **Opens in the sidebar** (Ingress); Home Assistant handles authentication
- **Zero MQTT setup**: connects to the Mosquitto broker add-on automatically
- Logs every message on the topics you add, 24/7, with history and CSV export
- Topic stats, tags, node grouping and **LWT-based device online/offline status**
- Data retention, SQLite WAL mode, wildcard topics (`sensors/#`)
- **Heartbeats for edge nodes** (optional): nodes running the
  [MQTT heartbeat agent](https://github.com/855princekumar/mqtt-heartbeat-service) appear by
  themselves as online, offline or silent; history charts from 1 minute to 30 days, CSV export.
  Turn it on with a fleet master key in the Configuration tab
- In-app guides, status filters, dialogs that fit any screen and zoom
- Data stored in `/data`: survives updates and is part of Home Assistant backups
- AppArmor profile, no privileges, direct port access off by default

## Installation

1. Click the button above, or go to **Settings → Apps → Install app → ⋮ → Repositories**
   and add `https://github.com/855princekumar/sensehive-ha-addon`
   (before Home Assistant 2026: **Settings → Add-ons → Add-on Store → ⋮ → Repositories**).
2. Install **SenseHive** and press **Start**.
3. Enable **Show in sidebar** and open **SenseHive**.

If the Mosquitto broker add-on is installed, SenseHive is already connected. Add a topic
and publish to see data. See the add-on **Documentation** tab for all options.

<p align="center">
  <img src="docs/screenshots/ha-apps.png" width="45%" alt="SenseHive running next to the Mosquitto broker in Settings, Apps" />
  <img src="docs/screenshots/ha-addon-info.png" width="45%" alt="The add-on's page: Start, Show in sidebar, Open Web UI" />
</p>
<p align="center">
  <img src="docs/screenshots/ha-addon-config.png" width="45%" alt="Configuration: broker, password, heartbeats, all optional" />
  <img src="docs/screenshots/ha-addon-docs.png" width="45%" alt="The Documentation tab" />
</p>

## Upgrading from 1.3.x

1.4.0 replaces the old prebuilt-image add-on. The image is now built from the official
multi-arch `devprincekumar/sense-hive` image, and data moves to `/data`. Topics from 1.3.x
were stored inside the container and are not carried over. Export CSVs first if you
need them.

## Quality checks

Every change runs through [CI](.github/workflows/ci.yml), the real Home Assistant included:

| Check | What it covers |
| ----- | -------------- |
| Home Assistant app linter | `config.yaml` / `build.yaml` against the official schema |
| AppArmor | Profile parses and is named after the add-on slug |
| Unit tests | Option handling, broker discovery, ingress settings |
| Multi-arch build | amd64 and aarch64 images build from `build.yaml` |
| Sandbox test | Real add-on container with a mock Supervisor (172.30.32.2), Mosquitto with credentials and an ingress proxy: discovery, ingress without login, direct access requiring login, data flow, LWT, CSV export, persistence across restarts, option overrides, bad credentials |
| Real Home Assistant | Official apps devcontainer (Supervisor and Core), onboarding, the Mosquitto add-on, this add-on from the repository: store install, local build, Mosquitto discovery, ingress via Core, data flow, LWT, restart, backup, security rating 8/8, AppArmor (**21 checks**) |
| Real Home Assistant with a browser | Home Assistant's sign-in, SenseHive in the sidebar, the panel without a second sign-in and without Sign out, Add Node, an emulated fleet of 6 devices on Home Assistant's Mosquitto, live readings and last-will status, details, dark mode, phone to desktop with no layout or console errors (**30 checks**), and the screenshots above ([how to run](tests/ha-devcontainer/README.md)) |

Run the sandbox locally with Docker: `python tests/sandbox_test.py`

## Staying in sync with SenseHive

The add-on wraps the published `devprincekumar/sense-hive` image. The
[sync workflow](.github/workflows/sync-upstream.yml) checks for new SenseHive releases
daily. When one is out, it opens a PR that moves the add-on to the new image, bumps the
add-on version, adds a changelog entry and runs the sandbox test.

## Support

- Add-on issues: https://github.com/855princekumar/sensehive-ha-addon/issues
- SenseHive: https://github.com/855princekumar/sense-hive
