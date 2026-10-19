"""Move the add-on to the latest SenseHive release if a newer one (with a Docker image) exists.

Writes `updated`, `upstream` and `addon` to $GITHUB_OUTPUT.
"""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / 'sensehive'
IMAGE = 'devprincekumar/sense-hive'
RELEASES = 'https://api.github.com/repos/855princekumar/sense-hive/releases/latest'


def get_json(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'sensehive-addon-sync'})
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.load(res)


def as_tuple(version):
    return tuple(int(p) for p in re.findall(r'\d+', version)[:3])


def image_exists(tag):
    try:
        get_json(f'https://hub.docker.com/v2/repositories/{IMAGE}/tags/{tag}')
        return True
    except urllib.error.HTTPError:
        return False


def output(**values):
    path = os.getenv('GITHUB_OUTPUT')
    lines = [f'{k}={v}' for k, v in values.items()]
    print('\n'.join(lines))
    if path:
        with open(path, 'a') as f:
            f.write('\n'.join(lines) + '\n')


def main():
    build = (ADDON / 'build.yaml').read_text()
    config = (ADDON / 'config.yaml').read_text()
    current = re.search(rf'{re.escape(IMAGE)}:(\S+)', build).group(1)
    try:
        upstream = get_json(RELEASES)['tag_name'].lstrip('v')
    except urllib.error.HTTPError as e:
        print(f'No SenseHive release found ({e.code})')
        output(updated='false', upstream='', addon='')
        return

    if as_tuple(upstream) <= as_tuple(current) or not image_exists(upstream):
        output(updated='false', upstream=upstream, addon='')
        return

    addon_version = re.search(r'^version:\s*"([^"]+)"', config, re.M).group(1)
    # The add-on follows SenseHive's version (1.8.1 runs SenseHive 1.8.1); an add-on-only
    # change between releases takes the next patch
    major, minor, patch = as_tuple(addon_version)
    new_addon = upstream if as_tuple(upstream) > as_tuple(addon_version) else f'{major}.{minor}.{patch + 1}'

    (ADDON / 'build.yaml').write_text(build.replace(f'{IMAGE}:{current}', f'{IMAGE}:{upstream}'))
    (ADDON / 'config.yaml').write_text(config.replace(f'version: "{addon_version}"', f'version: "{new_addon}"', 1))
    dockerfile = (ADDON / 'Dockerfile').read_text()
    (ADDON / 'Dockerfile').write_text(dockerfile.replace(f'{IMAGE}:{current}', f'{IMAGE}:{upstream}'))

    changelog = ADDON / 'CHANGELOG.md'
    text = changelog.read_text()
    entry = (f'## {new_addon} (SenseHive {upstream})\n\n'
             f'- Update SenseHive to {upstream}: '
             f'https://github.com/855princekumar/sense-hive/releases/tag/v{upstream}\n\n')
    changelog.write_text(text.replace('# Changelog\n\n', '# Changelog\n\n' + entry, 1))

    output(updated='true', upstream=upstream, addon=new_addon)


if __name__ == '__main__':
    main()
