# SenseHive Add-on

SenseHive logs every message on the MQTT topics you add, keeps the history in
SQLite, and gives you a dashboard with live values, history, CSV export,
tags, node grouping and LWT-based device status. It can also watch your edge
nodes through encrypted heartbeats (see [Heartbeats](#heartbeats-for-edge-nodes)).

## Installation

1. In Home Assistant go to **Settings → Add-ons → Add-on Store**.
2. Open the menu (⋮) → **Repositories** and add:
   `https://github.com/855princekumar/sensehive-ha-addon`
3. Install **SenseHive** and press **Start**.
4. Enable **Show in sidebar** and open **SenseHive** from the sidebar
   (or press **Open Web UI**).

Inside Home Assistant you are already signed in, so there is no SenseHive
login screen.

## MQTT broker

If the official **Mosquitto broker** add-on is installed, SenseHive connects to
it automatically using the credentials Home Assistant provides. No host, port
or password needs to be entered.

To use a different broker, fill in **MQTT broker host** (and port/credentials)
in the **Configuration** tab. When the host is set it always takes priority
over automatic discovery.

When no broker is configured or discovered, SenseHive uses the broker saved on
its own **Settings** page.

## Using SenseHive

1. Click **Add Node** and enter the MQTT topic (wildcards such as
   `sensors/#` are supported), a **Node ID** (the device) and a **Tag**.
2. Optionally enter the device's **LWT / status topic**. SenseHive then shows
   whether the device is online, both per topic and per node.
3. Publish to the topic. Values appear live, and every message is logged.

The two cards at the top switch between **Topic logs** and **Heartbeats**. The
**(i)** button on each card opens a short guide. Both views filter by status
(online, offline, silent or no last will).

## Heartbeats for edge nodes

Edge nodes (Raspberry Pi, gateways, servers) running the
[MQTT heartbeat agent](https://github.com/855princekumar/mqtt-heartbeat-service)
send an encrypted heartbeat every 10 seconds over a public MQTT broker and
leave a last will. SenseHive finds them by itself.

1. Create a fleet master key once, on any computer:
   `python3 -c "import secrets; print(secrets.token_hex(32))"`
2. Enter it as **Heartbeat master key** in the **Configuration** tab and
   restart the add-on.
3. Install the agent on each node with the same fleet key
   ([setup guide](https://github.com/855princekumar/mqtt-heartbeat-service/blob/main/docs/SETUP.md)).
4. Open **Heartbeats**: nodes are online, offline (their last will arrived) or
   silent (nothing heard). **History** shows charts from 1 minute to 30 days;
   tick nodes to export CSV.

Messages are AES-256-GCM encrypted per node on topics that change every 10
minutes, so the public broker sees nothing useful. Keep the master key secret:
it is stored as a password option and never printed in the log.

## Direct access (optional)

Direct access on a port is **disabled by default**. To reach SenseHive
without Home Assistant (for example from another machine), set a port under
**Configuration → Network**. Direct access uses the SenseHive login: set
**Admin password** in the Configuration tab before the first start, or change
the default (`admin` / `admin123`) under **Settings → Account** before enabling
the port.

## Data and backups

The database is stored in the add-on's private `/data` folder. It survives
add-on updates and is included in Home Assistant backups. Configure automatic
cleanup under **Settings → Data Retention** in the SenseHive UI.

## Options

| Option          | Description                                                              |
| --------------- | ------------------------------------------------------------------------ |
| `mqtt_host`     | Broker host. Empty = use the Mosquitto add-on automatically              |
| `mqtt_port`     | Broker port (default `1883`)                                             |
| `mqtt_username` | Broker username                                                          |
| `mqtt_password` | Broker password                                                          |
| `timezone`      | Timezone for stored timestamps (e.g. `Europe/Berlin`). Empty = set it in the SenseHive UI |
| `admin_password` | First password of `admin` for direct access (new database only)         |
| `heartbeat_master_key` | 64 hex characters; turns on the heartbeat receiver. Empty = off   |
| `heartbeat_api_token` | Bearer token (32+ characters) for the read-only heartbeat API      |
| `heartbeat_broker` | Heartbeat broker. Empty = `broker.hivemq.com`                         |
| `heartbeat_port` | Heartbeat broker TLS port (default `8883`)                              |

## Security

- Runs with an AppArmor profile and no extra privileges
- No host network, no device access, no Home Assistant API access
- Ingress requests are authenticated by Home Assistant
- Strict Content Security Policy, no CDN; sign-in lockout and API token lockout
- Secrets (broker password, admin password, heartbeat key and token) are
  password options, passed to SenseHive as environment variables and never logged

## Support

Issues: https://github.com/855princekumar/sensehive-ha-addon/issues
SenseHive project: https://github.com/855princekumar/sense-hive
