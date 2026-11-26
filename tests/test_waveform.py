import struct
import tempfile
import unittest
from pathlib import Path

from nightecho.cap import ROOT
from nightecho.waveform import load_night, waveform_quality


def synthetic_edf(left_digital_max="100"):
    labels = ["THORAX", "C4-A1", "Tib Sx", "Tib Dx"]
    fixed = ["0", "", "", "01.01.26", "23.59.30", "1280", "", "7", "10", "4"]
    widths = [8, 80, 80, 8, 8, 8, 44, 8, 8, 4]
    header = b"".join(value.encode().ljust(width) for value, width in zip(fixed, widths))
    fields = [
        (labels, 16), ([""] * 4, 80), (["mV", "uV", "uV", "uV"], 8),
        (["-2"] * 4, 8), (["2"] * 4, 8), (["-100"] * 4, 8),
        (["100", "100", left_digital_max, "100"], 8),
        ([""] * 4, 80), (["10", "10", "20", "20"], 8), ([""] * 4, 32),
    ]
    header += b"".join(value.encode().ljust(width) for values, width in fields
                       for value in values)
    records = []
    for index in range(7):
        samples = [(index - 4) * 25] * 10 + [99] * 10 + [-100, 100] * 10 + [0] * 20
        records.append(struct.pack("<60h", *samples))
    return header + b"".join(records)


class WaveformTests(unittest.TestCase):
    def test_load_calibrated_waveforms_and_align_epochs(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as folder:
            raw = Path(folder)
            (raw / "sample.edf").write_bytes(synthetic_edf())
            (raw / "sample.txt").write_text(
                "Sleep Stage\tPosition\tTime [hh:mm:ss]\tEvent\tDuration[s]\tLocation\n"
                "R\tSupine\t00:00:00\tSLEEP-REM\t30\tx\n"
            )
            night = load_night("sample", raw)
            self.assertEqual(night.missing_channels, ("abdomen", "airflow"))
            self.assertEqual(len(night.channels), 4)
            self.assertEqual(night.annotation_start_offset_seconds, 30)
            self.assertEqual([epoch["stage"] for epoch in night.epochs], ["unknown", "rem"])
            thorax = night.waveforms["thorax"]
            left = night.waveforms["tib_left"]
            right = night.waveforms["tib_right"]
            self.assertEqual((thorax.sample_rate_hz, left.sample_rate_hz), (1, 2))
            self.assertEqual((thorax.unit, left.unit), ("mV", "uV"))
            self.assertEqual(len(thorax.samples), 70)
            self.assertEqual(list(thorax.epoch_samples(night.epochs[1])),
                             [-0.5] * 10 + [0] * 10 + [0.5] * 10)
            self.assertEqual(list(left.epoch_samples(night.epochs[1])), [-2, 2] * 30)
            self.assertEqual(waveform_quality(left, night.epochs)["rail_samples"], 140)
            self.assertEqual(waveform_quality(right, night.epochs)["flat_epochs"], 2)
            self.assertEqual(waveform_quality(right, night.epochs)["longest_constant_seconds"], 70)

            (raw / "sample.edf").write_bytes(synthetic_edf()[:-1])
            with self.assertRaisesRegex(ValueError, "file size does not match"):
                load_night("sample", raw)

            (raw / "sample.edf").write_bytes(synthetic_edf("655340"))
            with self.assertRaisesRegex(ValueError, "invalid EDF calibration for Tib Sx"):
                load_night("sample", raw)
            review = load_night("sample", raw, allow_uncalibrated=True)
            left = review.waveforms["tib_left"]
            self.assertFalse(left.calibrated)
            self.assertEqual(left.unit, "digital counts")
            self.assertEqual(list(left.epoch_samples(review.epochs[1])), [-100, 100] * 30)
            self.assertTrue(review.waveforms["thorax"].calibrated)
