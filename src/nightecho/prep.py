import argparse
import json
from collections import Counter
from datetime import datetime

from .cap import ROOT, edf_header, local_path, read_stages, write_csv

ALIASES = {
    "thorax": {"thorax", "thoracic", "chest", "torace"},
    "abdomen": {"abdomen", "abdominal", "abdo", "addome", "adddome"},
    "airflow": {"airflow", "flow", "nasal", "termistore"},
    "tib_left": {"tibialisl", "tibl", "ltib", "tibsx"},
    "tib_right": {"tibialisr", "tibr", "rtib", "tibdx"},
}


def channel_map(channels):
    mapped = {}
    for channel in channels:
        label = "".join(c for c in channel["label"].lower() if c.isalnum())
        for name, aliases in ALIASES.items():
            if label in aliases:
                if name in mapped:
                    raise ValueError(f"multiple channels match {name}")
                mapped[name] = channel["label"]
    return mapped


def aligned_epochs(stages, header):
    start = datetime.strptime(header["recording_time"], "%H.%M.%S")
    first = datetime.strptime(stages[0]["clock_time"], "%H:%M:%S")
    offset = (first - start).total_seconds() % 86400
    origin = stages[0]["onset_seconds"]
    intervals = [(row["onset_seconds"] - origin + offset,
                  row["onset_seconds"] - origin + offset + row["duration_seconds"],
                  row["stage"]) for row in stages]
    duration = header["data_records"] * header["record_duration_seconds"]
    epochs = []
    for onset in range(0, int(duration) - 29, 30):
        # only label epochs covered by one stage for all thirty seconds
        matches = [(a, b, stage) for a, b, stage in intervals if a < onset + 30 and b > onset]
        stage = "unknown"
        if len(matches) == 1:
            a, b, value = matches[0]
            if a <= onset and b >= onset + 30:
                stage = value
        epochs.append({"onset_seconds": onset, "duration_seconds": 30, "stage": stage})
    return epochs, offset


def prepare(raw, record):
    header = edf_header(raw / f"{record}.edf")
    stages = read_stages(raw / f"{record}.txt")
    epochs, offset = aligned_epochs(stages, header)
    mapped = channel_map(header["channels"])
    missing = sorted(set(ALIASES) - set(mapped))
    report = {
        "record_id": record,
        "source_bytes": (raw / f"{record}.edf").stat().st_size,
        "duration_seconds": header["data_records"] * header["record_duration_seconds"],
        "annotation_start_offset_seconds": offset,
        "epoch_count": len(epochs),
        "epoch_counts_by_stage": dict(Counter(row["stage"] for row in epochs)),
        "channels": header["channels"],
        "channel_mapping": mapped,
        "missing_channels": missing,
        "channel_review_required": bool(missing),
        "signal_preprocessing_status": "not implemented",
        "alignment_basis": "annotation clock time relative to edf start; same recording date assumed",
    }
    output = ROOT / "data/interim/cap"
    write_csv(output / f"{record}_epochs.csv", epochs, list(epochs[0]))
    (output / f"{record}_prep.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", required=True)
    parser.add_argument("--raw-dir", default="data/raw/cap")
    args = parser.parse_args()
    if not args.record.isalnum():
        parser.error("record must contain only letters and numbers")
    print(json.dumps(prepare(local_path(args.raw_dir), args.record), indent=2))


if __name__ == "__main__":
    main()
