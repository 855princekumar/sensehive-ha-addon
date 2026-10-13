# SenseHive Add-on

SenseHive logs every message on the MQTT topics you add, keeps the history in
SQLite, and gives you a dashboard with live values, history, CSV export,
tags, node grouping and LWT-based device status.

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

## Direct access (optional)

Direct access on a port is **disabled by default**. To reach SenseHive
without Home Assistant (for example from another machine), set a port under
**Configuration → Network**. Direct access uses the SenseHive login
(`admin` / `admin123` by default). Change the password under
**Settings → Account** before enabling it.

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

## Security

- Runs with an AppArmor profile and no extra privileges
- No host network, no device access, no Home Assistant API access
- Ingress requests are authenticated by Home Assistant

## Support

Issues: https://github.com/855princekumar/sensehive-ha-addon/issues
SenseHive project: https://github.com/855princekumar/sense-hive
