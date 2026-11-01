import unittest

from nightecho.prep import aligned_epochs, channel_map


class PrepTests(unittest.TestCase):
    def test_alignment_keeps_unscored_start(self):
        stages = [{"onset_seconds": 0, "duration_seconds": 30,
                   "stage": "wake", "clock_time": "22:35:17"}]
        header = {"recording_time": "22.34.47", "data_records": 9,
                  "record_duration_seconds": 10}
        rows, offset = aligned_epochs(stages, header)
        self.assertEqual(offset, 30)
        self.assertEqual([r["stage"] for r in rows], ["unknown", "wake", "unknown"])

    def test_midnight_alignment(self):
        stages = [{"onset_seconds": 0, "duration_seconds": 30,
                   "stage": "rem", "clock_time": "00:00:00"}]
        header = {"recording_time": "23.59.30", "data_records": 6,
                  "record_duration_seconds": 10}
        rows, offset = aligned_epochs(stages, header)
        self.assertEqual(offset, 30)
        self.assertEqual(rows[1]["stage"], "rem")

    def test_observed_channel_labels(self):
        channels = [{"label": name} for name in ["TORACE", "ADDDOME", "TIB Sx", "TIB Dx"]]
        self.assertEqual(channel_map(channels), {"thorax": "TORACE", "abdomen": "ADDDOME", "tib_left": "TIB Sx", "tib_right": "TIB Dx"})

    def test_eeg_is_not_a_breathing_channel(self):
        self.assertEqual(channel_map([{"label": "C4-A1"}]), {})
        self.assertEqual(channel_map([{"label": "THORAX"}]), {"thorax": "THORAX"})


if __name__ == "__main__":
    unittest.main()
