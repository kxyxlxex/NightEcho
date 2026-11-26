import argparse
import json
import re
from math import isfinite
from urllib.request import Request, urlopen

from .cap import edf_header, local_path
from .prep import channel_map

BASE_URL = "https://physionet.org/files/capslpdb/1.0.0"
MAX_HEADER_BYTES = 16384
REQUIRED_CHANNELS = ("thorax", "abdomen", "tib_left", "tib_right")


def fetch_range(url, start, stop, *, total=None):
    request = Request(url, headers={"Range": f"bytes={start}-{stop}"})
    with urlopen(request, timeout=20) as response:
        length = stop - start + 1
        content_range = re.fullmatch(rf"bytes {start}-{stop}/([0-9]+)",
                                     response.headers.get("Content-Range", ""))
        if (response.status != 206 or not content_range or
                response.headers.get("Content-Length") != str(length)):
            raise ValueError("server did not return the requested bounded EDF range")
        source_bytes = int(content_range[1])
        if source_bytes <= stop or (total is not None and source_bytes != total):
            raise ValueError("unexpected EDF source size in range response")
        data = response.read(length)
        if len(data) != length:
            raise ValueError("incomplete EDF range")
        return data, source_bytes


def candidate_header(record):
    if not record.isalnum():
        raise ValueError("record must contain only letters and numbers")
    raw = local_path("data/raw/cap")
    for path in (raw / f"{record}.edf", raw / "headers" / f"{record}.header"):
        path = local_path(path)
        if path.is_file():
            return path

    url = f"{BASE_URL}/{record}.edf"
    fixed, total = fetch_range(url, 0, 255)
    header_bytes = int(fixed[184:192])
    channel_count = int(fixed[252:256])
    if (fixed[:8].strip() != b"0" or fixed[192:197] == b"EDF+D" or
            not 256 < header_bytes <= MAX_HEADER_BYTES or
            header_bytes != 256 * (1 + channel_count)):
        raise ValueError("unexpected continuous EDF header layout")
    metadata, _ = fetch_range(url, 256, header_bytes - 1, total=total)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(fixed + metadata)
    return path


def review(record):
    path = candidate_header(record)
    channels = edf_header(path)["channels"]
    mapped = channel_map(channels)
    by_label = {channel["label"]: channel for channel in channels}
    result = {}
    for name in REQUIRED_CHANNELS:
        if name not in mapped:
            result[name] = {"status": "missing"}
            continue
        channel = by_label[mapped[name]]
        low, high = float(channel["physical_min"]), float(channel["physical_max"])
        dmin, dmax = int(channel["digital_min"]), int(channel["digital_max"])
        rate = channel["sample_rate_hz"]
        issues = []
        if not channel["unit"]:
            issues.append("missing physical unit")
        if not (isfinite(low) and isfinite(high) and low < high):
            issues.append("invalid physical range")
        if not -32768 <= dmin < dmax <= 32767:
            issues.append("invalid signed 16-bit digital range")
        if not isfinite(rate) or rate <= (4 if name in ("thorax", "abdomen") else 20):
            issues.append("sample rate too low for planned filter")
        result[name] = {
            "label": channel["label"], "unit": channel["unit"], "sample_rate_hz": rate,
            "physical_range": [low, high], "digital_range": [dmin, dmax],
            "prefilter": channel["prefilter"],
            "status": "flagged" if issues else "pass", "issues": issues,
        }
    return {"record": record, "header_source": str(path.relative_to(local_path("."))),
            "passes_header_check": all(c["status"] == "pass" for c in result.values()),
            "channels": result}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("records", nargs="+")
    args = parser.parse_args()
    print(json.dumps([review(record) for record in args.records], indent=2))


if __name__ == "__main__":
    main()
