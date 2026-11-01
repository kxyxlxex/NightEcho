import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nightecho.cap import inventory, edf_header, write_csv


def inspect(row):
    record = row['record_id']
    path = ROOT / f'data/raw/cap/headers/{record}.header'
    if not path.exists():
        request = Request(f'https://physionet.org/files/capslpdb/1.0.0/{record}.edf', headers={'Range': 'bytes=0-16383'})
        with urlopen(request, timeout=60) as response:
            if response.status != 206:
                raise ValueError('server did not return a partial response')
            path.write_bytes(response.read(16384))
    header = edf_header(path)
    labels = [c['label'] for c in header['channels']]
    normalized = [label.upper().strip() for label in labels]
    row['channels'] = ' | '.join(labels)
    row['thorax_present'] = any(x in normalized for x in ['TORACE', 'THORAX', 'CHEST'])
    row['explicit_leg_pair'] = 'TIB SX' in normalized and 'TIB DX' in normalized
    row['ambiguous_leg_pair'] = 'DX1-DX2' in normalized and 'SX1-SX2' in normalized
    row['duration_seconds'] = header['data_records'] * header['record_duration_seconds']
    row['estimated_edf_bytes'] = 256 * (1 + len(labels)) + int(sum(c['sample_rate_hz'] for c in header['channels']) * row['duration_seconds'] * 2)
    return row


if __name__ == '__main__':
    rows = inventory(ROOT / 'data/raw/cap')
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(inspect, rows))
    write_csv(ROOT / 'data/metadata/channel_audit.csv', rows, list(rows[0]))
    for diagnosis in sorted(set(row['diagnosis'] for row in rows)):
        group = [row for row in rows if row['diagnosis'] == diagnosis]
        print(diagnosis, len(group), 'thorax:', sum(row['thorax_present'] for row in group), 'explicit legs:', sum(row['explicit_leg_pair'] for row in group))
    usable = [row for row in rows if row['planned_include'] and row['thorax_present'] and row['explicit_leg_pair']]
    print('explicit candidates:', len(usable), 'bytes:', sum(row['estimated_edf_bytes'] for row in usable))
    print('smallest:', sorted([(row['estimated_edf_bytes'], row['record_id']) for row in usable])[:5])
