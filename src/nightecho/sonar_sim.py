import argparse
import json
from cmath import exp as complex_exp, phase
from math import ceil, exp, floor, pi, sin, tau
from random import Random
from statistics import mean, pstdev

FRAME_RATE = 100
ANALYSIS_RATE = 10
BIN_WIDTH_M = 343 / (2 * 4000)
WAVELENGTH_M = 343 / 20000
PHASE_PER_METER = 4 * pi / WAVELENGTH_M
RANGE_BINS = range(ceil(0.2 / BIN_WIDTH_M), floor(1.5 / BIN_WIDTH_M) + 1)


def simulate_echoes(displacement_m, noise_std=0.0, seed=42):
    """Generate complex echoes by range bin at 100 frames per second."""
    random = Random(seed)
    returns = [[] for _ in RANGE_BINS]
    clutter = 0.25 + 0.15j
    for displacement in displacement_m:
        distance = 0.8 + displacement
        reflection = complex_exp(1j * PHASE_PER_METER * distance)
        for index, trace in zip(RANGE_BINS, returns):
            offset_bins = index - distance / BIN_WIDTH_M
            echo = reflection * exp(-0.5 * (offset_bins / 0.65) ** 2) + clutter
            if noise_std:
                echo += complex(random.gauss(0, noise_std), random.gauss(0, noise_std))
            trace.append(echo)
    return returns


def block_average(values):
    width = FRAME_RATE // ANALYSIS_RATE
    return [sum(values[i:i + width]) / width
            for i in range(0, len(values) - width + 1, width)]


def breathing_spectrum(values):
    length = len(values)
    if length < 30 * ANALYSIS_RATE:
        raise ValueError("breathing analysis requires at least 30 seconds")
    duration = length / ANALYSIS_RATE
    first, last = ceil(0.1 * duration), floor(0.7 * duration)
    return [(k / duration, abs(sum(value * complex_exp(-1j * tau * k * i / length)
                                   for i, value in enumerate(values))) ** 2)
            for k in range(first, last + 1)]


def breathing_rate(values):
    frequency, _ = max(breathing_spectrum(values), key=lambda point: point[1])
    return 60 * frequency


def recover_breathing(echoes):
    """Lock a range bin and estimate breaths per minute from its unwrapped phase."""
    centered = []
    for trace in echoes:
        mean = sum(trace) / len(trace)
        centered.append([value - mean for value in trace])
    scores = [sum(power for _, power in breathing_spectrum(block_average(trace)))
              for trace in centered]
    best = max(range(len(scores)), key=scores.__getitem__)
    if scores[best] == 0:
        raise ValueError("no breathing-band echo energy")
    trace = centered[best]
    angles = [0.0]
    for previous, current in zip(trace, trace[1:]):
        angles.append(angles[-1] + phase(current * previous.conjugate()))
    displacement_m = [value / PHASE_PER_METER for value in block_average(angles)]
    return breathing_rate(displacement_m), RANGE_BINS[best] * BIN_WIDTH_M


def run_case(input_bpm=15.0, noise_std=0.0, *, duration_seconds=60):
    displacement = [0.004 * sin(tau * input_bpm / 60 * i / FRAME_RATE)
                    for i in range(duration_seconds * FRAME_RATE)]
    rate, range_m = recover_breathing(simulate_echoes(displacement, noise_std))
    return {
        "input_bpm": input_bpm,
        "direct_estimate_bpm": breathing_rate(block_average(displacement)),
        "recovered_bpm": rate,
        "absolute_error_bpm": abs(input_bpm - rate),
        "resolution_bpm": 60 / duration_seconds,
        "selected_bin_center_m": range_m,
        "noise_std_per_component": noise_std,
    }


def run_sdb1_segment():
    from .waveform import load_night

    start, duration = 15030, 30
    night = load_night("sdb1", allow_uncalibrated=True)
    epoch = next(e for e in night.epochs if e["onset_seconds"] == start)
    belt = night.waveforms["thorax"]
    voltage = belt.epoch_samples(epoch)
    source_rate = int(belt.sample_rate_hz)
    if (belt.sample_rate_hz != source_rate or
            len(voltage) != duration * source_rate or
            not belt.physical_min < min(voltage) < max(voltage) < belt.physical_max):
        raise ValueError("expected a complete unclipped sdb1 chest window")

    center, spread = mean(voltage), pstdev(voltage)
    scale = 0.003 / spread
    interpolated = []
    for index in range(duration * FRAME_RATE):
        left, remainder = divmod(index * source_rate, FRAME_RATE)
        fraction = remainder / FRAME_RATE
        right = min(left + 1, len(voltage) - 1)
        interpolated.append(voltage[left] + fraction * (voltage[right] - voltage[left]))
    displacement = [(value - center) * scale for value in interpolated]
    belt_rate = breathing_rate(block_average(interpolated))
    echo_rate, _ = recover_breathing(simulate_echoes(displacement))
    return {
        "start_seconds": start,
        "duration_seconds": duration,
        "belt_mean_mv": center,
        "belt_std_mv": spread,
        "assumed_mm_per_mv": scale * 1000,
        "belt_rate_bpm": belt_rate,
        "echo_rate_bpm": echo_rate,
        "echo_minus_belt_bpm": echo_rate - belt_rate,
        "resolution_bpm": 60 / duration,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--30-second-review", dest="review", action="store_true")
    args = parser.parse_args()
    if args.review:
        results = {"sdb1": run_sdb1_segment(),
                   "synthetic_off_grid": run_case(21, duration_seconds=30)}
    else:
        results = {"clean": run_case(), "noisy": run_case(noise_std=0.12)}
    print(json.dumps({"kind": "simulation", **results}, indent=2))


if __name__ == "__main__":
    main()
