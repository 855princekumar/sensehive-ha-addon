"""Home Assistant add-on entry point: map add-on options to SenseHive environment variables."""
import json
import os
import re
import sys
import urllib.request

OPTIONS_FILE = '/data/options.json'
APP_DIR = '/app'
# The Supervisor's ingress proxy; Home Assistant has already authenticated these requests
INGRESS_PROXY = '172.30.32.2'
MASTER_KEY = re.compile(r'^[0-9a-fA-F]{64}$')
MIN_TOKEN = 32


def load_options(path=OPTIONS_FILE):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def discover_mqtt(token=None):
    """Ask the Supervisor for the Mosquitto add-on credentials (needs `services: mqtt:want`)."""
    token = token or os.getenv('SUPERVISOR_TOKEN')
    if not token:
        return None
    request = urllib.request.Request('http://supervisor/services/mqtt',
                                     headers={'Authorization': f'Bearer {token}'})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.load(response).get('data') or {}
    except Exception as e:
        print(f"MQTT service discovery unavailable: {e}")
        return None
    return data if data.get('host') else None


def build_env(options, discovered, environ):
    """Returns the broker dict that was applied, or None if Settings in the UI stay in charge."""
    environ['DB_PATH'] = '/data/iot_dashboard.db'
    environ['SENSEHIVE_INGRESS_PROXY'] = INGRESS_PROXY

    host = (options.get('mqtt_host') or '').strip()
    if host:
        broker = {
            'host': host,
            'port': options.get('mqtt_port') or 1883,
            'username': options.get('mqtt_username') or '',
            'password': options.get('mqtt_password') or '',
        }
    elif discovered:
        broker = {
            'host': discovered['host'],
            'port': discovered.get('port') or 1883,
            'username': discovered.get('username') or '',
            'password': discovered.get('password') or '',
        }
    else:
        broker = None

    if broker:
        environ['DEFAULT_BROKER_HOST'] = str(broker['host'])
        environ['DEFAULT_BROKER_PORT'] = str(broker['port'])
        environ['DEFAULT_BROKER_USERNAME'] = str(broker['username'])
        environ['DEFAULT_BROKER_PASSWORD'] = str(broker['password'])
        environ['SENSEHIVE_FORCE_BROKER'] = 'true'

    timezone = (options.get('timezone') or '').strip()
    if timezone:
        environ['DEFAULT_TIMEZONE'] = timezone
        environ['SENSEHIVE_TIMEZONE'] = timezone

    # First password of `admin` in a new database (direct access only; ingress needs none)
    admin = options.get('admin_password') or ''
    if admin:
        environ['SENSEHIVE_ADMIN_PASSWORD'] = admin

    build_heartbeat_env(options, environ)
    return broker


def build_heartbeat_env(options, environ):
    """Heartbeat receiver for the MQTT heartbeat agent; off unless a valid master key is set.

    Secrets are validated here and never printed. Returns 'on', 'off' or the reason it stays off.
    """
    key = (options.get('heartbeat_master_key') or '').strip()
    if not key:
        return 'off'
    if not MASTER_KEY.match(key):
        print("SenseHive: heartbeat receiver stays off: heartbeat_master_key must be 64 hex characters")
        return 'invalid key'
    environ['HEARTBEAT_MASTER_KEY'] = key
    token = (options.get('heartbeat_api_token') or '').strip()
    if token and len(token) >= MIN_TOKEN:
        environ['HEARTBEAT_API_TOKEN'] = token
    elif token:
        print(f"SenseHive: heartbeat API stays closed: heartbeat_api_token needs {MIN_TOKEN}+ characters")
    broker = (options.get('heartbeat_broker') or '').strip()
    if broker:
        environ['HEARTBEAT_BROKER'] = broker
    if options.get('heartbeat_port'):
        environ['HEARTBEAT_PORT'] = str(options['heartbeat_port'])
    return 'on'


def main():
    options = load_options()
    discovered = None if (options.get('mqtt_host') or '').strip() else discover_mqtt()
    broker = build_env(options, discovered, os.environ)

    if broker:
        source = 'add-on options' if (options.get('mqtt_host') or '').strip() else 'Mosquitto add-on'
        print(f"SenseHive: using MQTT broker {broker['host']}:{broker['port']} from {source}")
    else:
        print("SenseHive: no broker configured or discovered; using the broker saved in Settings")
    if 'HEARTBEAT_MASTER_KEY' in os.environ:
        print(f"SenseHive: heartbeat receiver on, broker {os.environ.get('HEARTBEAT_BROKER', 'broker.hivemq.com')}"
              f":{os.environ.get('HEARTBEAT_PORT', '8883')} (TLS)")

    os.chdir(APP_DIR)
    os.execvp(sys.executable, [sys.executable, os.path.join(APP_DIR, 'app.py')])


if __name__ == '__main__':
    main()
