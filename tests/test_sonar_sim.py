import unittest

from nightecho.sonar_sim import BIN_WIDTH_M, run_case


class SonarSimulationTests(unittest.TestCase):
    def test_recovers_clean_and_noisy_breathing(self):
        for noise_std in (0.0, 0.12):
            with self.subTest(noise_std=noise_std):
                result = run_case(noise_std=noise_std)
                self.assertLessEqual(result["absolute_error_bpm"], 0.5)
                self.assertLess(abs(result["selected_bin_center_m"] - 0.8), BIN_WIDTH_M)

    def test_recovers_a_different_input_rate(self):
        self.assertAlmostEqual(run_case(input_bpm=18)["recovered_bpm"], 18)

    def test_30_second_estimator_quantizes_off_grid_rate(self):
        result = run_case(input_bpm=21, duration_seconds=30)
        self.assertEqual(result["resolution_bpm"], 2)
        self.assertEqual(result["direct_estimate_bpm"], 20)
        self.assertEqual(result["recovered_bpm"], 20)
        self.assertEqual(result["absolute_error_bpm"], 1)
