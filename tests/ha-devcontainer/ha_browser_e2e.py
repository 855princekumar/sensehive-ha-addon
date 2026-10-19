"""The add-on in a real Home Assistant, seen through a browser like a person sees it.

Runs on the machine that hosts the official apps devcontainer (Supervisor and
Home Assistant Core, Core published on --ha). Needs a SenseHive checkout
(--sensehive) for its live browser checks (tools/live_e2e.py) and its emulated
fleet (version-1.0/demo_fleet.py), which runs inside the add-on's container and
publishes to Home Assistant's Mosquitto add-on with the login the Supervisor gave
SenseHive.

  python tests/ha-devcontainer/ha_browser_e2e.py --ha http://127.0.0.1:7080 \
      --user e2e --password ... --sensehive ../sense-hive --out ha-report

Checks: Home Assistant's own sign-in; SenseHive in the sidebar opens the panel
(ingress, no SenseHive sign-in); a node added with Add Node in the panel; then
SenseHive's live checks inside the panel on phone, tablet, laptop and desktop
(every emulated device Active from its last will, live readings, details, dark
mode, no sideways scroll, nothing sticking out, no errors), and every device
Inactive after the fleet stops.
"""
import argparse
import shlex
import os
import subprocess
import sys
import time


def sh(cmd):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)


def panel_frame(page, seconds=90):
    """The panel's iframe (Playwright's CSS reaches into Home Assistant's shadow DOM), once SenseHive is in it."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        el = page.locator('iframe').first
        if el.count():
            f = el.element_handle().content_frame()
            if f and '/api/hassio_ingress/' in (f.url or ''):
                try:
                    f.wait_for_selector('#root > div', timeout=15000)
                    return f
                except Exception:
                    pass
        time.sleep(1)
    raise RuntimeError('the SenseHive panel did not open: %s' % page.url)


def ha_login(page, a):
    page.goto(a.ha + '/')
    page.wait_for_selector('input[name="username"]', timeout=60000)
    page.fill('input[name="username"]', a.user)
    page.fill('input[name="password"]', a.password)
    page.keyboard.press('Enter')
    page.wait_for_url(lambda u: '/auth/' not in u, timeout=60000)
    time.sleep(3)


def addon_pages(a):
    """The add-on as Home Assistant shows it: its Info page (Start, Open Web UI, the sidebar switch)
    and its Configuration page, for the docs."""
    from playwright.sync_api import sync_playwright
    os.makedirs(a.shots, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        ha_login(page, a)
        import re

        def save(name):
            time.sleep(4)
            page.screenshot(path=os.path.join(a.shots, name + '.png'))
            print('screenshot', name, page.url, flush=True)

        def click_first(*names):
            for n in names:                              # Home Assistant 2026 calls add-ons Apps
                for loc in (page.get_by_role('link', name=re.compile(n, re.I)),
                            page.get_by_role('menuitem', name=re.compile(n, re.I)),
                            page.get_by_text(re.compile('^' + n + '$', re.I))):
                    try:
                        if loc.count():
                            loc.first.click(timeout=5000)
                            return n
                    except Exception:
                        pass
            return None

        page.goto(a.ha + '/config/dashboard')
        save('ha-settings')
        print('opened', click_first('Apps', 'Add-ons'), flush=True)
        save('ha-apps')
        page.get_by_text('Lightweight MQTT topic logger').first.click(timeout=15000)   # the card, not the sidebar
        save('ha-addon-info')
        for loc in (page.get_by_role('tab', name=re.compile('^Configuration$', re.I)),
                    page.get_by_text(re.compile('^Configuration$', re.I))):
            if loc.count():
                loc.first.click(timeout=10000)
                break
        save('ha-addon-config')
        page.get_by_text(re.compile('^Documentation$', re.I)).first.click(timeout=10000)
        save('ha-addon-docs')
        b.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ha', required=True, help='Home Assistant Core, e.g. http://127.0.0.1:7080')
    ap.add_argument('--user', required=True)
    ap.add_argument('--password', required=True)
    ap.add_argument('--sensehive', required=True, help='a SenseHive checkout (tools/live_e2e.py)')
    ap.add_argument('--container', default='ha-dev', help='the devcontainer')
    ap.add_argument('--devices', type=int, default=6)
    ap.add_argument('--out', default='ha-report')
    ap.add_argument('--min-checks', type=int, default=0)
    ap.add_argument('--shots', help='also save screenshots for the docs here (the panel, the add-on pages)')
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.sensehive, 'tools'))
    sys.path.insert(0, os.path.join(a.sensehive, 'version-1.0'))
    import live_e2e as live
    from demo_fleet import devices

    # The emulated fleet: devices on the network, on Home Assistant's Mosquitto (port 1883 of the
    # Home Assistant host), signed in as a Home Assistant user. The add-on's own broker login stays
    # private (its AppArmor profile keeps other processes out of it).
    demo_src = os.path.join(a.sensehive, 'version-1.0', 'demo_fleet.py')
    r = sh(f'docker cp "{demo_src}" {a.container}:/root/demo_fleet.py')
    if r.returncode:
        print('FAIL could not put the emulated fleet on the Home Assistant host', r.stdout)
        return 1
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fleet_in_addon.sh'), 'w', newline='\n') as fh:
        fh.write('#!/bin/sh\n'
                 '# sensehive-demo on the Home Assistant host, on its Mosquitto, as a Home Assistant user\n'
                 '# (the password comes from the environment, never written to this file)\n'
                 f'exec docker exec -e E2E_MQTT_PASSWORD {a.container} sh -c '
                 f'\'exec python3 /root/demo_fleet.py --port 1883 --username {shlex.quote(a.user)} '
                 '--password-mqtt "$E2E_MQTT_PASSWORD" "$@" --broker localhost\' sh "$@"\n')
    os.environ['E2E_MQTT_PASSWORD'] = a.password
    fleet_cmd = 'sh ' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fleet_in_addon.sh').replace(os.sep, '/')
    fleet = devices(a.devices, 'sensehive-demo')
    rep = live.Report(a.out)
    state = {'first': True}

    def open_dashboard(page):
        """Home Assistant's sign-in, then SenseHive from the sidebar: the panel's frame."""
        page.goto(a.ha + '/')
        page.wait_for_selector('input[name="username"]', timeout=60000)
        page.fill('input[name="username"]', a.user)
        page.fill('input[name="password"]', a.password)
        page.keyboard.press('Enter')
        page.wait_for_url(lambda u: '/auth/' not in u, timeout=60000)
        panels = None
        deadline = time.time() + 60
        while time.time() < deadline and not panels:
            panels = page.evaluate("() => { const h = document.querySelector('home-assistant');"
                                   " return h && h.hass && h.hass.panels ? Object.values(h.hass.panels)"
                                   ".map(p => ({title: p.title, url: p.url_path})) : null; }")
            time.sleep(0.5)
        panel = next((p for p in panels or [] if p['title'] == 'SenseHive'), None)
        if state['first']:
            rep.check('Home Assistant lists SenseHive as a sidebar panel (Show in sidebar)', panel is not None, panels, page)
            rep.check('the sidebar shows SenseHive', page.locator('ha-sidebar').get_by_text('SenseHive').count() > 0, '', page)
        if panel is None:
            raise RuntimeError('SenseHive is not a Home Assistant panel: %s' % panels)
        page.goto(a.ha + '/' + panel['url'])
        frame = panel_frame(page)
        if state['first']:
            state['first'] = False
            rep.check('the panel opens the dashboard straight away (Home Assistant signs in, no SenseHive sign-in)',
                      frame.locator('#username').count() == 0, frame.url, page)
            time.sleep(2)
            rep.check('inside Home Assistant the page has no Sign out (Home Assistant handles sign-in)',
                      frame.locator('#logoutBtn').count() == 0, '', page)
            # A clean dashboard first (earlier runs), then a person adds the first device with Add Node
            # and the rest go through the same API the dialog uses
            frame.evaluate("""async () => {
                for (const n of await (await fetch('api/nodes')).json())
                    await fetch('api/nodes/' + n.id, {method: 'DELETE'});
            }""")
            page.reload()
            frame = panel_frame(page)
            d = fleet[0]
            frame.click('#addNodeBtn')
            frame.fill('input[placeholder="e.g., sensors/temperature"]', d['topic'])
            frame.fill('input[placeholder="e.g., greenhouse-esp32"]', d['name'])
            frame.fill('input[placeholder="e.g., environment"]', d['tag'])
            frame.fill('input[placeholder="e.g., greenhouse-esp32/status"]', d['lwt'])
            frame.locator('button', has_text='Add Node').last.click()
            frame.locator('.sh-card').filter(has_text='node: ' + d['name']).first.wait_for(timeout=15000)
            time.sleep(2)
            added = frame.evaluate("""async (fleet) => {
                let ok = 0;
                for (const d of fleet) {
                    const r = await fetch('api/nodes', {method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({topic: d.topic, tag: d.tag, node_name: d.name, lwt_topic: d.lwt})});
                    ok += r.ok ? 1 : 0;
                }
                const nodes = await (await fetch('api/nodes')).json();
                return nodes.length;
            }""", fleet[1:])
            rep.check('Add Node in the panel works, and the fleet is added through ingress', added >= len(fleet), added, page)
            page.reload()
            return open_dashboard_after_reload(page)
        return frame

    def open_dashboard_after_reload(page):
        return panel_frame(page)

    rep2 = live.run(None, None, fleet, fleet_cmd, 'unused', a.out, login=False, open_dashboard=open_dashboard,
                    shots=a.shots, shot_prefix='ha-panel')
    if a.shots:
        addon_pages(a)
    passes, fails = rep.passes + rep2.passes, rep.fails + rep2.fails
    print(f'Home Assistant: {passes} checks passed, {len(fails)} failed')
    if a.min_checks and passes + len(fails) < a.min_checks:
        print(f'Only {passes + len(fails)} checks ran, fewer than {a.min_checks}')
        return 1
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
