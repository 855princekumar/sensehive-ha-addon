"""Functional sandbox test for the SenseHive add-on (needs Docker).

Recreates the parts of a Home Assistant system the add-on talks to:
  - 'hassio' network 172.30.32.0/23 like HAOS
  - Mosquitto broker with credentials, reachable as core-mosquitto
  - mock Supervisor at 172.30.32.2: MQTT service discovery + ingress proxy
and then installs the add-on image with /data, options.json and SUPERVISOR_TOKEN.

Usage: python tests/sandbox_test.py [--base-image devprincekumar/sense-hive:1.1.0] [--keep]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDON_DIR = ROOT / 'sensehive'
PREFIX = 'shsbx'
NETWORK = f'{PREFIX}-hassio'
TOKEN = 'sandbox-supervisor-token'
MQTT_USER, MQTT_PASS = 'addons', 'Sandbox-Pass-123'
PROXY_PORT = 18123
INGRESS = f'http://127.0.0.1:{PROXY_PORT}/api/hassio_ingress/sandboxtoken'

results = []


def docker(*args, check=True, capture=True):
    env = dict(os.environ, MSYS_NO_PATHCONV='1')
    proc = subprocess.run(['docker', *args], capture_output=capture, text=True, encoding='utf-8', errors='replace', env=env)
    if check and proc.returncode != 0:
        raise RuntimeError(f"docker {' '.join(args)} failed:\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout.strip() if capture else ''


def logs():
    proc = subprocess.run(['docker', 'logs', f'{PREFIX}-addon'], capture_output=True, text=True,
                          encoding='utf-8', errors='replace')
    return proc.stdout + proc.stderr


def check(name, condition, detail=''):
    results.append((name, bool(condition)))
    print(f"  [{'PASS' if condition else 'FAIL'}] {name}" + (f' - {detail}' if detail and not condition else ''), flush=True)


def http(method, path, body=None, base=INGRESS):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.status, res.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except OSError as e:
        return 0, str(e)


def wait_until(fn, timeout=60, interval=1.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        value = fn()
        if value:
            return value
        time.sleep(interval)
    return fn()


def cleanup():
    for name in ('addon', 'supervisor', 'mosquitto'):
        docker('rm', '-f', f'{PREFIX}-{name}', check=False)
    docker('volume', 'rm', '-f', f'{PREFIX}-data', check=False)
    docker('network', 'rm', NETWORK, check=False)


def mosquitto_pub(topic, message, retain=False):
    args = ['exec', f'{PREFIX}-mosquitto', 'mosquitto_pub', '-h', 'localhost', '-u', MQTT_USER, '-P', MQTT_PASS,
            '-t', topic, '-m', message, '-q', '1']
    if retain:
        args.append('-r')
    docker(*args)


def start_addon(image, options):
    docker('rm', '-f', f'{PREFIX}-addon', check=False)
    docker('create', '--name', f'{PREFIX}-addon', '--network', NETWORK, '--ip', '172.30.33.5',
           '--network-alias', 'sensehive', '-e', f'SUPERVISOR_TOKEN={TOKEN}',
           '-v', f'{PREFIX}-data:/data', image)
    with tempfile.TemporaryDirectory() as tmp:
        opts = Path(tmp) / 'options.json'
        opts.write_text(json.dumps(options))
        docker('cp', str(opts), f'{PREFIX}-addon:/data/options.json')
    docker('start', f'{PREFIX}-addon')
    ok = wait_until(lambda: http('GET', '/api/health')[0] == 200, timeout=60)
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-image', help='BUILD_FROM override (default: amd64 entry of build.yaml)')
    parser.add_argument('--keep', action='store_true', help='leave the sandbox running')
    args = parser.parse_args()

    build_yaml = (ADDON_DIR / 'build.yaml').read_text()
    base_image = args.base_image or re.search(r'amd64:\s*(\S+)', build_yaml).group(1)
    version = re.search(r'^version:\s*"([^"]+)"', (ADDON_DIR / 'config.yaml').read_text(), re.M).group(1)
    image = f'{PREFIX}/sensehive-addon:{version}'

    cleanup()
    try:
        print(f'Building add-on {version} from {base_image}', flush=True)
        docker('build', '-q', '--build-arg', f'BUILD_FROM={base_image}', '--build-arg', 'BUILD_ARCH=amd64',
               '--build-arg', f'BUILD_VERSION={version}', '-t', image, str(ADDON_DIR))
        labels = json.loads(docker('inspect', '-f', '{{json .Config.Labels}}', image))
        check('image carries io.hass labels', labels.get('io.hass.type') == 'addon' and labels.get('io.hass.version') == version)

        docker('network', 'create', '--subnet', '172.30.32.0/23', '--gateway', '172.30.32.1', NETWORK)
        docker('volume', 'create', f'{PREFIX}-data')

        conf = ('listener 1883\\nallow_anonymous false\\npassword_file /mosquitto/config/passwd\\n')
        docker('run', '-d', '--name', f'{PREFIX}-mosquitto', '--network', NETWORK, '--ip', '172.30.33.10',
               '--network-alias', 'core-mosquitto', 'eclipse-mosquitto:2', 'sh', '-c',
               f'mosquitto_passwd -c -b /mosquitto/config/passwd {MQTT_USER} {MQTT_PASS} && '
               f'printf "{conf}" > /mosquitto/config/mosquitto.conf && '
               'chown mosquitto /mosquitto/config/passwd 2>/dev/null; chmod 0700 /mosquitto/config/passwd; '
               'exec mosquitto -c /mosquitto/config/mosquitto.conf')

        docker('run', '-d', '--name', f'{PREFIX}-supervisor', '--network', NETWORK, '--ip', '172.30.32.2',
               '--network-alias', 'supervisor', '-p', f'{PROXY_PORT}:80',
               '-e', f'SUPERVISOR_TOKEN={TOKEN}', '-e', f'MQTT_PASSWORD={MQTT_PASS}',
               '-v', f'{ROOT / "tests"}:/sv:ro', 'python:3.12-alpine', 'python', '-u', '/sv/mock_supervisor.py')
        time.sleep(2)

        print('Scenario 1: default options -> Mosquitto discovered through the Supervisor', flush=True)
        check('add-on starts and answers health checks through ingress',
              start_addon(image, {'mqtt_host': '', 'mqtt_port': 1883, 'mqtt_username': '', 'mqtt_password': '', 'timezone': ''}))
        out = wait_until(lambda: (l := logs()) and 'Connected to MQTT broker' in l and l, timeout=30) \
            or logs()
        check('broker discovered from Mosquitto add-on', 'core-mosquitto:1883 from Mosquitto add-on' in out, out[-600:])
        check('authenticated to broker with discovered credentials', 'Connected to MQTT broker' in out, out[-600:])
        check('database stored in /data', '/data/iot_dashboard.db' in out)
        health = json.loads(http('GET', '/api/health')[1])
        check('health reports MQTT connected', health.get('mqtt_connected') is True, str(health))

        status, page = http('GET', '/')
        # The name is "SenseHive" since 1.4 ("Sense-Hive" before)
        check('dashboard opens through ingress without a login',
              status == 200 and ('SenseHive' in page or 'Sense-Hive' in page), f'{status}')
        # Since 1.4 the browser code is served from static/ (no CDN, no inline script); older
        # versions had it inline. Either way every URL must be relative to work behind ingress.
        scripts = re.findall(r'<script[^>]*src="([^"]+)"', page)
        code = page
        for src in scripts:
            s_status, s_body = http('GET', '/' + src)
            check(f'script {src} loads through ingress', s_status == 200 and not src.startswith(('/', 'http')),
                  f'{s_status}')
            code += s_body
        check('dashboard uses relative URLs (ingress safe)', "api/" in code and "fetch('/api" not in code
              and 'fetch("/api' not in code)
        status, _ = http('GET', '/api/nodes')
        check('API usable through ingress (HA-authenticated)', status == 200, f'{status}')

        direct = docker('run', '--rm', '--network', NETWORK, 'curlimages/curl:8.10.1', '-s', '-o', '/dev/null',
                        '-w', '%{http_code}', 'http://sensehive:5000/api/nodes', check=False)
        check('direct access from another container still requires login', direct == '401', direct)
        direct_login = docker('run', '--rm', '--network', NETWORK, 'curlimages/curl:8.10.1', '-s', '-o', '/dev/null',
                              '-w', '%{http_code}', 'http://sensehive:5000/', check=False)
        check('direct access redirects to the login page', direct_login == '302', direct_login)

        print('Scenario 2: full data flow', flush=True)
        status, body = http('POST', '/api/nodes', {'topic': 'greenhouse/esp32/telemetry', 'tag': 'environment',
                                                   'node_name': 'greenhouse-esp32', 'lwt_topic': 'greenhouse/esp32/status'})
        check('add topic with tag, node and LWT', status == 200, body)
        http('POST', '/api/nodes', {'topic': 'home/#', 'tag': 'misc', 'node_name': 'house'})
        time.sleep(1.5)
        for i in range(5):
            mosquitto_pub('greenhouse/esp32/telemetry', json.dumps({'temperature': 20 + i, 'readings': [1, 2, 3],
                                                                    'meta': {'fw': '1.0.%d' % i}}))
        mosquitto_pub('home/kitchen/light', 'on')
        mosquitto_pub('greenhouse/esp32/status', 'online', retain=True)

        def topic(name):
            nodes = json.loads(http('GET', '/api/nodes')[1])
            return next((n for n in nodes if n['topic'] == name), None)

        tele = wait_until(lambda: (t := topic('greenhouse/esp32/telemetry')) and t['entry_count'] == 5 and t['status'] == 'active' and t, 20)
        check('messages logged and LWT status active', bool(tele), str(topic('greenhouse/esp32/telemetry')))
        if tele:
            check('nested JSON payload stored intact', tele['last_value'] == {'temperature': 24, 'readings': [1, 2, 3], 'meta': {'fw': '1.0.4'}})
            check('entry count and size reported', tele['approx_size_bytes'] > 0)
        check('wildcard subscription logs messages', wait_until(lambda: (t := topic('home/#')) and t['entry_count'] == 1, 10))
        stats = json.loads(http('GET', '/api/stats')[1])
        check('navbar stats: 1 active node', stats['nodes']['active'] == 1, str(stats))

        mosquitto_pub('greenhouse/esp32/status', 'offline', retain=True)
        check('LWT offline marks the node inactive',
              wait_until(lambda: json.loads(http('GET', '/api/stats')[1])['nodes']['inactive'] == 1, 10))

        status, csv_body = http('GET', f"/api/nodes/{tele['id'] if tele else 0}/export")
        check('CSV export through ingress', status == 200 and csv_body.startswith('Timestamp,Payload'), f'{status}')

        print('Scenario 3: restart keeps data (add-on update / host reboot)', flush=True)
        docker('restart', f'{PREFIX}-addon')
        wait_until(lambda: http('GET', '/api/health')[0] == 200, 60)
        after = topic('greenhouse/esp32/telemetry')
        check('data persists across restarts', after and after['entry_count'] == 5, str(after))
        check('LWT status persists across restarts', after and after['status'] == 'inactive', str(after))

        print('Scenario 4: broker set in the add-on Configuration tab', flush=True)
        check('add-on restarts with explicit broker options',
              start_addon(image, {'mqtt_host': 'core-mosquitto', 'mqtt_port': 1883, 'mqtt_username': MQTT_USER,
                                  'mqtt_password': MQTT_PASS, 'timezone': 'Europe/Berlin'}))
        out = wait_until(lambda: (l := logs()) and 'Connected to MQTT broker' in l and l, 30) \
            or logs()
        check('explicit options take priority over discovery', 'from add-on options' in out, out[-600:])
        check('connected with explicit credentials', 'Connected to MQTT broker' in out, out[-600:])
        broker = json.loads(http('GET', '/api/broker')[1])
        check('timezone option applied', broker.get('timezone') == 'Europe/Berlin', str(broker))

        print('Scenario 5: wrong broker password is reported, add-on keeps running', flush=True)
        start_addon(image, {'mqtt_host': 'core-mosquitto', 'mqtt_port': 1883, 'mqtt_username': MQTT_USER,
                            'mqtt_password': 'wrong', 'timezone': ''})
        time.sleep(4)
        health = json.loads(http('GET', '/api/health')[1])
        check('UI stays up with bad credentials, MQTT reported disconnected', health.get('mqtt_connected') is False, str(health))

        print('Scenario 6: heartbeat receiver from the Configuration tab', flush=True)
        key, api_token = 'c3' * 32, 'sandbox-heartbeat-token-' + 'x' * 16
        hb = {'mqtt_host': '', 'mqtt_port': 1883, 'mqtt_username': '', 'mqtt_password': '', 'timezone': '',
              'admin_password': '', 'heartbeat_master_key': key, 'heartbeat_api_token': api_token,
              'heartbeat_broker': '', 'heartbeat_port': 8883}
        check('add-on restarts with heartbeat options', start_addon(image, hb))
        out = wait_until(lambda: (l := logs()) and 'heartbeat receiver on' in l and l, 30) or logs()
        check('heartbeat receiver reported on', 'heartbeat receiver on' in out, out[-600:])
        check('master key and API token never logged', key not in out and api_token not in out)
        status = json.loads(http('GET', '/api/heartbeat/status')[1] or '{}')
        check('heartbeat receiver enabled', status.get('enabled') is True, str(status))
        code, _ = http('GET', '/heartbeats')
        check('Heartbeats page through ingress', code == 200, str(code))
        code, js = http('GET', '/static/dashboard.js')
        check('dashboard has the guides and status filter',
              code == 200 and 'infoHeartbeats' in js and 'statusFilter' in js, str(code))

        bad = dict(hb, heartbeat_master_key='not-a-valid-key-' + 'q' * 48)
        start_addon(image, bad)
        out = wait_until(lambda: (l := logs()) and 'must be 64 hex' in l and l, 30) or logs()
        check('invalid master key keeps the receiver off',
              'must be 64 hex' in out and bad['heartbeat_master_key'] not in out, out[-600:])
        status = json.loads(http('GET', '/api/heartbeat/status')[1] or '{}')
        check('receiver reported disabled', status.get('enabled') is False, str(status))
    finally:
        if args.keep:
            print(f'Sandbox kept running. Ingress URL: {INGRESS}/')
        else:
            cleanup()

    failed = [name for name, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
