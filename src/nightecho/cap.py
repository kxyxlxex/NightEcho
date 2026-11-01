import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GROUPS = {
    "n": (16, "control"),
    "brux": (2, "bruxism"),
    "ins": (9, "insomnia"),
    "narco": (5, "narcolepsy"),
    "nfle": (40, "nfle"),
    "plm": (10, "plm"),
    "rbd": (22, "rbd"),
    "sdb": (4, "sdb"),
}
STAGES = {
    "SLEEP-S0": "wake", "SLEEP-S1": "n1", "SLEEP-S2": "n2",
    "SLEEP-S3": "n3", "SLEEP-S4": "n3", "SLEEP-REM": "rem",
    "SLEEP-MT": "unknown", "SLEEP-UNSCORED": "unknown", "MT": "unknown",
}


def local_path(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("path must stay inside the project folder")
    return path


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def inventory(raw):
    rows = []
    for prefix, (count, diagnosis) in GROUPS.items():
        for number in range(1, count + 1):
            record = f"{prefix}{number}"
            rows.append({
                "subject_id": record,
                "record_id": record,
                "diagnosis": diagnosis,
                "planned_include": prefix != "narco",
                "exclusion_reason": "narcolepsy protocol exclusion" if prefix == "narco" else "",
                "edf_present": (raw / f"{record}.edf").is_file(),
                "annotations_present": (raw / f"{record}.txt").is_file(),
            })
    return rows


def read_stages(path):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header = next(i for i, line in enumerate(lines) if line.startswith("Sleep Stage\t"))
    rows = []
    previous_clock = None
    day = 0
    origin = None
    for line in lines[header + 1:]:
        cells = line.split("\t")
        if len(cells) < 4:
            continue
        # some reports omit the position column
        clock_index = next((i for i, cell in enumerate(cells[:3]) if ":" in cell), None)
        if clock_index is None:
            continue
        event = cells[clock_index + 1].strip()
        clock = datetime.strptime(cells[clock_index].strip(), "%H:%M:%S")
        seconds = clock.hour * 3600 + clock.minute * 60 + clock.second
        if previous_clock is not None and seconds < previous_clock - 43200:
            day += 86400
        previous_clock = seconds
        absolute = day + seconds
        if origin is None:
            origin = absolute
        if event not in STAGES:
            continue
        duration = float(cells[clock_index + 2].strip().replace(",", "."))
        if duration <= 0:
            raise ValueError(f"invalid stage duration in {path.name}")
        rows.append({
            "onset_seconds": absolute - origin,
            "duration_seconds": duration,
            "stage": STAGES[event],
            "source_event": event,
            "clock_time": cells[clock_index].strip(),
        })
    if not rows:
        raise ValueError(f"no sleep stages found in {path.name}")
    return rows


def edf_header(path):
    with path.open("rb") as stream:
        fixed = stream.read(256)
        count = int(fixed[252:256])
        header = stream.read(count * 256)
    if len(header) != count * 256:
        raise ValueError("incomplete edf header")
    widths = [("label", 16), ("transducer", 80), ("unit", 8),
              ("physical_min", 8), ("physical_max", 8), ("digital_min", 8),
              ("digital_max", 8), ("prefilter", 80), ("samples", 8), ("reserved", 32)]
    channels = [{} for _ in range(count)]
    offset = 0
    for name, width in widths:
        for index, channel in enumerate(channels):
            channel[name] = header[offset + index * width:offset + (index + 1) * width].decode("ascii").strip()
        offset += count * width
    duration = float(fixed[244:252])
    for channel in channels:
        channel["sample_rate_hz"] = int(channel.pop("samples")) / duration
    return {
        "recording_date": fixed[168:176].decode("ascii").strip(),
        "recording_time": fixed[176:184].decode("ascii").strip(),
        "data_records": int(fixed[236:244]),
        "record_duration_seconds": duration,
        "channels": channels,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["inventory", "stages", "inspect"])
    parser.add_argument("--raw-dir", default="data/raw/cap")
    parser.add_argument("--record", default="n1")
    args = parser.parse_args()
    raw = local_path(args.raw_dir)
    if not args.record.isalnum():
        parser.error("record must contain only letters and numbers")
    if args.command == "inventory":
        rows = inventory(raw)
        target = ROOT / "data/metadata/subjects.csv"
        write_csv(target, rows, list(rows[0]))
        print(f"saved {len(rows)} records to {target.relative_to(ROOT)}")
    elif args.command == "stages":
        rows = read_stages(raw / f"{args.record}.txt")
        target = ROOT / f"data/interim/cap/{args.record}_stages.csv"
        write_csv(target, rows, list(rows[0]))
        print(f"saved {len(rows)} stage intervals to {target.relative_to(ROOT)}")
        print(json.dumps(dict(Counter(row['stage'] for row in rows)), indent=2))
    else:
        result = edf_header(raw / f"{args.record}.edf")
        target = ROOT / f"data/interim/cap/{args.record}_header.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
