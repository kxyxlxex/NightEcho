import argparse
import json
from array import array
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from itertools import groupby
from math import ceil, isclose, isfinite
from statistics import median
from sys import byteorder

from .cap import edf_header, local_path, read_stages
from .prep import ALIASES, aligned_epochs, channel_map


@dataclass
class Waveform:
    label: str
    unit: str
    sample_rate_hz: Fraction
    physical_min: float
    physical_max: float
    samples: array
    calibrated: bool = True

    def epoch_samples(self, epoch):
        """Return the native samples in the epoch's half-open time interval."""
        onset = epoch["onset_seconds"]
        stop = onset + epoch["duration_seconds"]
        return self.samples[ceil(onset * self.sample_rate_hz):
                            ceil(stop * self.sample_rate_hz)]


@dataclass
class Night:
    record_id: str
    channels: list[dict]
    waveforms: dict[str, Waveform]
    missing_channels: tuple[str, ...]
    epochs: list[dict]
    annotation_start_offset_seconds: float


def load_night(record, raw_dir="data/raw/cap", *, allow_uncalibrated=False):
    """Load one continuous CAP EDF and its aligned sleep-stage annotations."""
    if not record.isalnum():
        raise ValueError("record must contain only letters and numbers")
    raw = local_path(raw_dir)
    path = local_path(raw / f"{record}.edf")
    stages_path = local_path(raw / f"{record}.txt")
    with path.open("rb") as stream:
        fixed = stream.read(256)
        if fixed[:8].strip() != b"0" or fixed[192:197] == b"EDF+D":
            raise ValueError("expected a continuous 16-bit EDF")
        header = edf_header(path)
        channels = header["channels"]
        header_bytes = int(fixed[184:192])
        if header_bytes != (1 + len(channels)) * 256:
            raise ValueError("unexpected EDF header size")
        record_duration = Fraction(fixed[244:252].decode("ascii").strip())
        counts = [round(channel["sample_rate_hz"] * record_duration)
                  for channel in channels]
        record_count = header["data_records"]
        if record_count <= 0 or not counts or any(count <= 0 for count in counts):
            raise ValueError("invalid EDF data record count or sample count")
        stride = 2 * sum(counts)
        if stream.seek(0, 2) != header_bytes + stride * record_count:
            raise ValueError("EDF file size does not match its header")
        mapped = channel_map(channels)
        by_label = {label: name for name, label in mapped.items()}
        waveforms = {}
        blocks = []
        start = 0
        for channel, count in zip(channels, counts):
            stop = start + 2 * count
            label = channel["label"]
            if label in by_label:
                low, high = float(channel["physical_min"]), float(channel["physical_max"])
                dmin, dmax = int(channel["digital_min"]), int(channel["digital_max"])
                calibrated = (isfinite(low) and isfinite(high) and low < high and
                              -32768 <= dmin < dmax <= 32767)
                if not calibrated and not allow_uncalibrated:
                    raise ValueError(f"invalid EDF calibration for {label}")
                unit = channel["unit"]
                if not calibrated:
                    low, high = -32768, 32767
                    dmin, dmax = -32768, 32767
                    unit = "digital counts"
                waveform = Waveform(label, unit, count / record_duration,
                                    low, high, array("d"), calibrated)
                waveforms[by_label[label]] = waveform
                blocks.append((start, stop, waveform, dmin, (high - low) / (dmax - dmin)))
            start = stop

        stream.seek(header_bytes)
        for _ in range(record_count):
            data = stream.read(stride)
            if len(data) != stride:
                raise ValueError("incomplete EDF data record")
            for start, stop, waveform, dmin, scale in blocks:
                digital = array("h")
                digital.frombytes(data[start:stop])
                if byteorder == "big":
                    digital.byteswap()
                low = waveform.physical_min
                waveform.samples.extend(low + (value - dmin) * scale for value in digital)

    epochs, offset = aligned_epochs(read_stages(stages_path), header)
    return Night(record, channels, waveforms, tuple(sorted(ALIASES.keys() - mapped.keys())),
                 epochs, offset)


def waveform_quality(waveform, epochs):
    """Summarize digital rail hits, constant runs, and epoch amplitude."""
    samples = waveform.samples
    low, high = waveform.physical_min, waveform.physical_max
    rail_samples = 0
    longest_run = 0
    for value, run in groupby(samples):
        count = sum(1 for _ in run)
        longest_run = max(longest_run, count)
        if value <= low or value >= high or isclose(value, high, rel_tol=1e-12):
            rail_samples += count
    spans = []
    for epoch in epochs:
        segment = waveform.epoch_samples(epoch)
        if segment:
            spans.append(max(segment) - min(segment))
    return {
        "unit": waveform.unit,
        "calibrated": waveform.calibrated,
        "sample_rate_hz": float(waveform.sample_rate_hz),
        "samples": len(samples),
        "rail_samples": rail_samples,
        "longest_constant_seconds": longest_run / float(waveform.sample_rate_hz),
        "flat_epochs": spans.count(0),
        "median_epoch_peak_to_peak": median(spans) if spans else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", required=True)
    parser.add_argument("--raw-dir", default="data/raw/cap")
    parser.add_argument("--allow-uncalibrated", action="store_true",
                        help="review invalidly calibrated channels in raw digital counts")
    args = parser.parse_args()
    night = load_night(args.record, args.raw_dir,
                       allow_uncalibrated=args.allow_uncalibrated)
    print(json.dumps({
        "record_id": night.record_id,
        "annotation_start_offset_seconds": night.annotation_start_offset_seconds,
        "epoch_count": len(night.epochs),
        "epoch_counts_by_stage": dict(Counter(epoch["stage"] for epoch in night.epochs)),
        "missing_channels": night.missing_channels,
        "waveforms": {name: waveform_quality(waveform, night.epochs)
                      for name, waveform in night.waveforms.items()},
    }, indent=2))


if __name__ == "__main__":
    main()
