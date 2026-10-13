"""Unit tests for the add-on entry point (sensehive/run.py)."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('addon_run', ROOT / 'sensehive' / 'run.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)

DEFAULTS = {'mqtt_host': '', 'mqtt_port': 1883, 'mqtt_username': '', 'mqtt_password': '', 'timezone': ''}
DISCOVERED = {'host': 'core-mosquitto', 'port': 1883, 'username': 'addons', 'password': 'secret', 'ssl': False}


def test_always_sets_data_path_and_ingress_proxy():
    env = {}
    run.build_env(DEFAULTS, None, env)
    assert env['DB_PATH'] == '/data/iot_dashboard.db'
    assert env['SENSEHIVE_INGRESS_PROXY'] == '172.30.32.2'


def test_uses_discovered_mosquitto_when_no_host_set():
    env = {}
    broker = run.build_env(DEFAULTS, DISCOVERED, env)
    assert broker['host'] == 'core-mosquitto'
    assert env['DEFAULT_BROKER_HOST'] == 'core-mosquitto'
    assert env['DEFAULT_BROKER_USERNAME'] == 'addons' and env['DEFAULT_BROKER_PASSWORD'] == 'secret'
    assert env['SENSEHIVE_FORCE_BROKER'] == 'true'


def test_explicit_host_wins_over_discovery():
    env = {}
    options = dict(DEFAULTS, mqtt_host='192.168.1.10', mqtt_port=1884, mqtt_username='u', mqtt_password='p')
    run.build_env(options, DISCOVERED, env)
    assert (env['DEFAULT_BROKER_HOST'], env['DEFAULT_BROKER_PORT']) == ('192.168.1.10', '1884')
    assert (env['DEFAULT_BROKER_USERNAME'], env['DEFAULT_BROKER_PASSWORD']) == ('u', 'p')


def test_no_broker_leaves_ui_settings_in_charge():
    env = {}
    assert run.build_env(DEFAULTS, None, env) is None
    assert 'SENSEHIVE_FORCE_BROKER' not in env and 'DEFAULT_BROKER_HOST' not in env


def test_timezone_only_applied_when_set():
    env = {}
    run.build_env(DEFAULTS, None, env)
    assert 'SENSEHIVE_TIMEZONE' not in env
    run.build_env(dict(DEFAULTS, timezone='Europe/Berlin'), None, env)
    assert env['SENSEHIVE_TIMEZONE'] == 'Europe/Berlin'


def test_load_options_missing_or_invalid(tmp_path):
    assert run.load_options(str(tmp_path / 'missing.json')) == {}
    bad = tmp_path / 'bad.json'
    bad.write_text('{not json')
    assert run.load_options(str(bad)) == {}
    good = tmp_path / 'options.json'
    good.write_text(json.dumps(DEFAULTS))
    assert run.load_options(str(good)) == DEFAULTS


def test_discovery_without_token_is_skipped(monkeypatch):
    monkeypatch.delenv('SUPERVISOR_TOKEN', raising=False)
    assert run.discover_mqtt() is None
