"""Every picture the docs show is in this repository: a missing or renamed screenshot
is a broken image on GitHub and in Home Assistant's Documentation tab."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = 'https://raw.githubusercontent.com/855princekumar/sensehive-ha-addon/main/'
IMG = re.compile(r'(?:src="|\]\()([^")\s]+\.(?:png|svg|jpg|gif))')


def test_every_image_in_the_docs_exists():
    missing = []
    for doc in (ROOT / 'README.md', ROOT / 'sensehive' / 'DOCS.md', ROOT / 'sensehive' / 'README.md'):
        for ref in IMG.findall(doc.read_text(encoding='utf-8')):
            if ref.startswith(RAW):                           # the Documentation tab needs full addresses
                path = ROOT / ref[len(RAW):]
            elif ref.startswith('http'):
                continue
            else:
                path = (doc.parent / ref).resolve()
            if not path.is_file():
                missing.append(f'{doc.name}: {ref}')
    assert not missing, missing
