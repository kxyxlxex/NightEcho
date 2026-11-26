from array import array
from itertools import chain
from math import cos, isfinite, sin, sqrt, tau
from struct import pack
from sys import byteorder
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from .cap import local_path
from .waveform import load_night

SOURCE_RATE = 64
OUTPUT_RATE = 10
EPOCH_SECONDS = 30


def highpass(values):
    """Apply a 10 Hz Butterworth high-pass in both directions."""
    angle = tau * 10 / SOURCE_RATE
    c = cos(angle)
    norm = 1 + sin(angle) / sqrt(2)
    b = (1 + c) / (2 * norm)
    a1 = -2 * c / norm
    a2 = (2 - norm) / norm

    def filter_once(signal):
        output = array("d")
        x1 = x2 = signal[0]
        y1 = y2 = 0.0
        for x in signal:
            y = b * (x - 2 * x1 + x2) - a1 * y1 - a2 * y2
            output.append(y)
            x2, x1 = x1, x
            y2, y1 = y1, y
        return output

    forward = filter_once(values)
    forward.reverse()
    backward = filter_once(forward)
    backward.reverse()
    return backward


def smooth(values):
    """Apply three centered 13-sample moving averages with edge extension."""
    radius = 6
    for _ in range(3):
        padded = array("d", chain([values[0]] * radius, values, [values[-1]] * radius))
        total = sum(padded[:2 * radius + 1])
        output = array("d", [total / (2 * radius + 1)])
        for entering, leaving in zip(padded[2 * radius + 1:], padded):
            total += entering - leaving
            output.append(max(0.0, total / (2 * radius + 1)))
        values = output
    return values


def prepare_envelope(waveform, epoch_count):
    native_count = epoch_count * EPOCH_SECONDS * SOURCE_RATE
    if (not waveform.calibrated or waveform.unit != "mV" or
            waveform.sample_rate_hz != SOURCE_RATE or len(waveform.samples) != native_count):
        raise ValueError("expected a calibrated nfle25 leg channel covering the epoch grid")
    values = waveform.samples
    excluded = set()
    for index, value in enumerate(values):
        if value <= waveform.physical_min or value >= waveform.physical_max:
            first = max(0, index - SOURCE_RATE) // (EPOCH_SECONDS * SOURCE_RATE)
            last = min(native_count - 1, index + SOURCE_RATE) // (EPOCH_SECONDS * SOURCE_RATE)
            excluded.update(range(first, last + 1))

    rectified_uv = array("d", (abs(v) * 1000 for v in highpass(values)))
    filtered = smooth(rectified_uv)
    envelope = array("f")
    samples_per_epoch = EPOCH_SECONDS * OUTPUT_RATE
    for index in range(epoch_count * samples_per_epoch):
        left, remainder = divmod(index * SOURCE_RATE, OUTPUT_RATE)
        fraction = remainder / OUTPUT_RATE
        value = (1 - fraction) * filtered[left] + fraction * filtered[left + 1]
        envelope.append(float("nan") if index // samples_per_epoch in excluded else value)
    return envelope, sorted(excluded)


def write_npy(archive, name, dtype, shape, data):
    header = repr({"descr": dtype, "fortran_order": False, "shape": shape}).encode("ascii")
    header += b" " * (-(10 + len(header) + 1) % 64) + b"\n"
    archive.writestr(f"{name}.npy", b"\x93NUMPY\x01\x00" + pack("<H", len(header)) + header + data)


def main():
    night = load_night("nfle25")
    epochs = night.epochs
    if not epochs or any(e["onset_seconds"] != i * EPOCH_SECONDS or
                         e["duration_seconds"] != EPOCH_SECONDS
                         for i, e in enumerate(epochs)):
        raise ValueError("expected a complete 30-second grid starting at EDF time zero")
    count = len(epochs)
    output = local_path("data/processed/nfle25_leg_envelopes.npz")
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=output.parent, delete=False) as temp:
        temporary_path = local_path(temp.name)
    try:
        with ZipFile(temporary_path, "w", compression=ZIP_DEFLATED) as archive:
            write_npy(archive, "stage", "|S7", (count,),
                      b"".join(e["stage"].encode("ascii").ljust(7, b"\0") for e in epochs))
            write_npy(archive, "epoch_onset_seconds", "<i4", (count,),
                      pack(f"<{count}i", *(e["onset_seconds"] for e in epochs)))
            write_npy(archive, "sample_rate_hz", "<i4", (), pack("<i", OUTPUT_RATE))
            shape = (count, EPOCH_SECONDS * OUTPUT_RATE)
            for name in ("tib_left", "tib_right"):
                envelope, excluded = prepare_envelope(night.waveforms[name], count)
                if (sum(isfinite(value) for value in envelope) !=
                        (count - len(excluded)) * shape[1]):
                    raise ValueError("unexpected nonfinite envelope samples")
                if byteorder == "big":
                    envelope.byteswap()
                write_npy(archive, f"{name}_envelope_uv", "<f4", shape, envelope.tobytes())
                write_npy(archive, f"{name}_excluded_epochs", "<i4", (len(excluded),),
                          pack(f"<{len(excluded)}i", *excluded))
                print(f"{name}: excluded zero-based epoch indices {excluded}")
        temporary_path.replace(output)
    finally:
        temporary_path.unlink(missing_ok=True)
    print(f"{output} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
