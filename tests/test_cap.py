import tempfile
import unittest
from pathlib import Path

from nightecho.cap import ROOT, inventory, local_path, read_stages, edf_header


class CapTests(unittest.TestCase):
    def test_inventory(self):
        rows = inventory(ROOT / "data/raw/cap")
        self.assertEqual(len(rows), 108)
        self.assertEqual(sum(row["planned_include"] for row in rows), 103)
        self.assertEqual(sum(row["diagnosis"] == "rbd" for row in rows), 22)
        self.assertEqual(len({row["subject_id"] for row in rows}), 108)

    def test_midnight_and_unknown_stages(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as folder:
            path = Path(folder) / "sample.txt"
            path.write_text(
                "Sleep Stage\tPosition\tTime [hh:mm:ss]\tEvent\tDuration[s]\tLocation\n"
                "S4\tSupine\t23:59:30\tSLEEP-S4\t30\tx\n"
                "S4\tSupine\t23:59:40\tMCAP-A1\t5\tx\n"
                "MT\tSupine\t00:00:00\tSLEEP-MT\t30\tx\n"
                "W\t00:01:00\tSLEEP-S0\t30\tx\n"
            )
            rows = read_stages(path)
        self.assertEqual([row["stage"] for row in rows], ["n3", "unknown", "wake"])
        self.assertEqual([row["onset_seconds"] for row in rows], [0, 30, 90])

    def test_edf_channel_rates(self):
        fixed = bytearray(b" " * 256)
        fixed[252:256] = b"2   "
        fixed[244:252] = b"1       "
        fixed[236:244] = b"60      "
        values = [(["THORAX", "EMG1"], 16), (["", ""], 80),
                  (["mV", "uV"], 8), (["-1", "-1"], 8), (["1", "1"], 8),
                  (["-32768", "-32768"], 8), (["32767", "32767"], 8),
                  (["", ""], 80), (["100", "512"], 8), (["", ""], 32)]
        header = b"".join(value.encode().ljust(width) for entries, width in values for value in entries)
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as folder:
            path = Path(folder) / "sample.edf"
            path.write_bytes(fixed + header)
            result = edf_header(path)
        self.assertEqual([c["sample_rate_hz"] for c in result["channels"]], [100, 512])
        self.assertEqual(result["channels"][1]["unit"], "uV")

    def test_paths_stay_in_project(self):
        with self.assertRaises(ValueError):
            local_path("../outside")


if __name__ == "__main__":
    unittest.main()
