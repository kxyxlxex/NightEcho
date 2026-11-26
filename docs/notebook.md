# Lab notebook

## 2026-10-31

- Set up project folders and a dependency-free CAP prep tool.
- Checked CAP's published record groups and one real n1 annotation report.
- Generated the 108-record inventory with 103 planned candidates.
- Parsed n1 into 1,140 stage intervals while keeping annotation timing.
- Added header inspection and tests for stage mapping, midnight timing, inventory,
  per-channel sampling rates, and project-local paths.
- No EDF recordings downloaded. Signal loading and preprocessing are next.

### First EDF check

- Downloaded the approved n16 recording and annotations inside data/raw/cap.
- Found five EEG channels only; flagged missing breathing and leg EMG channels.
- Added clock alignment and a complete 30-second epoch grid.
- n16 has 1,026 complete epochs, including seven unknown labels.
- Seven tests pass. No signal preprocessing or model training yet.
- Checked only 16 KiB of the n6 header; its labels do not confirm usable channels.
- Total project storage is about 34 MiB.

## 2026-11-01

- Surveyed five EDF headers using 80 KiB total, without downloading signal data.
- Saved channel names and recording durations to the metadata inventory.
- Added observed breathing and explicit tibial channel aliases.
- Found missing respiratory channels in rbd2 and duplicate flow labels in plm1.
- Kept ambiguous DX/SX channel pairs unmapped pending sensor verification.

## 2026-11-23

- Set up the repository-local Poetry environment with CPython 3.14.2 and
  Poetry 2.5.2. All eight existing tests passed.
- Ranked the audited candidates by EDF size and selected `n8` for the first
  preprocessing trial. Verified the channel rates and spot-checked three
  waveform windows. See the [data card](data-card.md) for the results and
  remaining quality checks.

### Full n8 waveform loading

- With approval, downloaded the 92,527,040-byte EDF and 52,631-byte annotation
  report to `data/raw/cap/`. Added a one-night loader that calibrates EDF samples
  to physical units and keeps each channel at its native rate.
- The EDF and annotations both start at 22:17:41 on 2005-01-01. The existing
  label grid yields 1,001 complete epochs (126 wake, 43 N1, 402 N2, 224 N3,
  197 REM, and 9 unknown). Verified the per-epoch sample count for every
  mapped channel. The final 10 seconds stay in the waveforms outside the grid.
- Found zero digital rail hits and zero fully flat 30-second epochs in the
  thorax and both tibial channels. Their median 30-second peak-to-peak spans
  were 0.00838 mV (thorax), 0.02404 mV (left), and 0.01142 mV (right).
  All five mapped channels became constant during the final approximately
  8.7 seconds, entirely within the unlabeled tail.
- Retained `n8` as a preprocessing trial. The thorax signal has low excursion,
  and breathing morphology and movement-event fidelity still need review.
  No filters or resampling were applied in this check.
- Reproduce with `poetry run python -m nightecho.waveform --record n8`.
  All nine tests passed, including the synthetic EDF test.

### n8 respiratory waveform review

**Decision: pause preprocessing.** The chest trace shows intermittent
breathing-band activity, but agreement with the abdominal trace is too
inconsistent to establish a usable whole-night chest signal.

- Saved [six time-aligned raw waveform windows](../reports/n8_respiration_review.svg)
  to `reports/n8_respiration_review.svg` (84,263 bytes). The traces show
  calibrated mV on separate voltage scales and share an EDF-relative time axis.
- In the early window (1,500–1,560 s), both traces peaked near 0.117 Hz. In
  the middle window (15,000–15,060 s), the chest span was 0.0061 mV and
  there was weak agreement with the abdomen. In the late window
  (28,500–28,560 s), both peaked near 0.233 Hz, with modest agreement.
- Across 500 nonoverlapping 60-second windows, the strongest Fourier
  frequencies in 0.10–0.70 Hz agreed within one frequency bin (0.017 Hz) in
  205 windows. Even after maximizing absolute band-limited correlation
  over circular time shifts of up to 2 seconds, the median was 0.44.
- The 21,480–21,540 s chest segment spans only 0.0038 mV, about five EDF
  quantization steps. The longest constant chest run inside the stage grid
  lasts 3.2 s at 23,562.7 s. The 26,880–26,940 s window contains an abrupt
  2.10 mV chest step. The recording-tail plot shows both traces flattening
  after the stage grid ends at 30,030 s.
- Used the existing local EDF and annotations. No preprocessing or NPZ
  output was produced. All nine tests passed.

### sdb1 waveform review

**Decision: pause preprocessing.** Chest and abdomen agree more often than
in `n8`, but both leg channels have invalid calibration fields and frequently
hit the 16-bit storage limits. The two nights expose different failure modes
despite both passing the channel-label audit.

- Verified the PhysioNet response sizes and downloaded with approval.
  `data/raw/cap/sdb1.edf` is 145,261,008 bytes and `data/raw/cap/sdb1.txt` is
  52,102 bytes. The first stage starts 30 seconds after the EDF starts.
  The label grid covers the full 28,260 seconds in 942 epochs, including
  177 unknown labels.
- Saved [six time-aligned chest and abdomen windows](../reports/sdb1_respiration_review.svg)
  to `reports/sdb1_respiration_review.svg` (194,923 bytes). Both inputs were
  sampled at 64 Hz and are plotted in mV using the EDF calibration formula.
  The early window at 1,440 s has a shared 0.367 Hz peak but weak waveform
  agreement. The middle window at 14,100 s shows shared 0.333 Hz cycles
  (lag-adjusted absolute correlation 0.89). The late window at 26,760 s
  shows divergent peaks and large excursions.
- Used the `n8` spectral comparison on 471 nonoverlapping one-minute
  windows, averaging the 64 Hz samples into a 10 Hz series for this check.
  Dominant frequencies in 0.10–0.70 Hz agreed within one 0.017 Hz bin in
  286/471 windows (61%), versus 205/500 (41%) for `n8`. Median absolute
  band-limited correlation after allowing up to 2 s of lag was 0.72,
  versus 0.44 for `n8`.
- Neither respiratory channel had a fully flat 30-second epoch. The
  longest constant runs were 1.50 s in chest at 14,761.36 s and 1.38 s
  in abdomen at 24,537.89 s. The first minute had an abrupt 2.61 mV
  chest step, and the final minute had large excursions in both traces.
  Chest and abdomen reached or exceeded their declared digital limits
  106,009 and 153,338 times, respectively. The exact signed 16-bit
  storage limits occurred in 133 chest epochs and 111 abdomen epochs.
- Both 128 Hz tibial channels declare digital limits of −655,360 to
  655,340, beyond the signed 16-bit storage range. The strict loader
  rejects the calibration. The opt-in raw-count review found actual
  storage-limit values in 197,621 left-leg samples (5.46%, 924/942 epochs)
  and 173,845 right-leg samples (4.81%, 866/942 epochs). Neither leg had a
  fully flat epoch. The extent of saturation and the unverified voltage
  scaling make both channels unsuitable for this preprocessing trial.
- Reproduce channel checks with
  `poetry run python -m nightecho.waveform --record sdb1 --allow-uncalibrated`.
  All nine tests passed, including the synthetic calibration check.
  No NPZ was produced.

### CAP pre-download header screen

- Added `poetry run python -m nightecho.header_review nfle25 plm1 sdb1`.
  The command uses local EDFs or cached headers first. For uncached
  recordings it requests the 256-byte fixed header and then the exact
  channel-header range. It closes the response before reading the body
  if the server ignores the range or returns inconsistent bounds.
  Cached 8,960 bytes for `nfle25` and 6,400 bytes for `plm1`.
- Ranked `nfle25` first. All four channels are 64 Hz with signed
  16-bit limits of −32,768 to 32,767. Chest and abdomen declare ±5 mV
  and both legs declare ±250 mV. The leg scale is 7.63 µV per count,
  close to the proposal's 8 µV event threshold. Respiratory and leg
  waveform quality require separate checks.
- Ranked `plm1` second. Its 64 Hz chest and abdomen declare ±1.25 and
  ±5 mV, with limits of −8,192 to 8,191 and −32,768 to 32,767,
  respectively. Both 128 Hz legs declare ±5 mV and digital limits
  of −163,840 to 163,835, outside the signed 16-bit range.
- Verified directly from the local `sdb1.edf` header that both 128 Hz legs
  declare ±20 mV and digital limits of −655,360 to 655,340. The 64 Hz
  chest declares ±2.5 mV with digital limits of −16,384 to 16,383.
  The 64 Hz abdomen declares ±1.25 mV with limits of −8,192 to 8,191.
- In `sdb1`, the left leg hit either signed storage limit in
  197,621/3,617,280 samples (5.46%). Its longest continuous run at a
  limit was 16 samples (125 ms). The right leg hit a limit in
  173,845/3,617,280 samples (4.81%), with a longest run of 17 samples
  (132.8 ms). Median per-epoch occupancy was 2.98% left and 1.43% right.
  The worst individual 30-second epochs reached 26.46% left and
  25.96% right.
- Verified source sizes and downloaded only `nfle25` after approval.
  The EDF is 236,725,520 bytes and the annotation report is 81,674 bytes.
  The strict loader aligned 1,044 epochs (nine unknown) with zero
  clock offset. The four channels had no fully flat epochs. Initial rail
  counts were zero in both respiratory channels, 12 on the left leg,
  and one on the right. Breathing agreement and EMG event fidelity
  remain to be reviewed.
  All 11 tests passed, including the bounded-range checks.

### nfle25 waveform review

**Decision:** retain both leg channels as exploratory activity envelopes.
Hold respiratory preprocessing and 8 µV event labeling.

- Compared the chest and abdomen using the same 0.10–0.70 Hz Fourier
  analysis as `sdb1`, averaging the native 64 Hz samples into 10 Hz bins.
  Their dominant peaks agreed within 0.017 Hz in 455/522 one-minute
  windows (87%), versus 286/471 (61%) for `sdb1` and 205/500 (41%) for
  `n8`. Median absolute band correlation allowing a 2-second shift
  was 0.992, versus 0.72 and 0.44, respectively.
- In the [respiratory plots](../reports/nfle25_respiration_review.svg)
  (179,199 bytes), the early, middle, and late samples show closely
  matched fine fluctuations as well as slower changes. That resemblance
  persists in the largest-step minute at 5,160 s and the lowest-excursion
  minute at 28,140 s. The median correlation of the native sample-to-sample
  differences was 0.991 (minimum 0.989 across all windows), and the
  strongest frequency bin accounted for a median 13% of chest
  breathing-band power. Neither channel clipped or had a fully flat epoch.
  The shared rapid fluctuations make agreement ambiguous as evidence of
  respiration. The cause is unresolved, so hold out the entire respiratory
  recording rather than excluding only the largest-step or lowest-amplitude
  windows.
- [Leg plots](../reports/nfle25_leg_review.svg) (26,034 bytes) show stored
  counts and their calibrated µV values on the same time grid. The
  quieter two-second left segment at 13,616 s spans −29 to 16 counts
  (−217 to 126 µV), versus −1,803 to 2,489 counts in the apparent burst
  at 28,724 s. The corresponding right examples at 782 s and 6,576 s
  span 13 to 97 and −1,557 to 4,574 counts, respectively. The quieter
  examples still have median rectified high-pass amplitudes of about
  8.1 µV left and 12.3 µV right. Larger changes are clear enough for
  exploratory envelopes. At 7.63 µV per count, one count is below the
  proposed threshold and two are already about 15.26 µV. Filtering can
  smooth those steps but cannot recover sub-count voltage or establish
  reliable events above the resting baseline.
- Saved [nfle25_leg_envelopes.npz](../data/processed/nfle25_leg_envelopes.npz)
  (2,206,322 bytes). Applied a forward/backward 10 Hz second-order
  Butterworth high-pass, full-wave rectification, three centered 13-sample
  moving averages, and linear sampling on the 10 Hz grid. Marked epochs
  intersecting a storage-limit hit plus a one-second buffer as NaN in
  the affected leg (zero-based left 636, 691, 837 and right 832).
- Verified both envelope arrays are 1,044 by 300 samples and the stage
  labels and epoch onsets match the source grid exactly, including all
  nine unknown labels. The archive contains no respiratory signals or
  threshold-based event labels. Reproduce with
  `poetry run python -m nightecho.nfle25_envelopes`. All 13 tests passed.

### Breathing-only sonar simulation

- Simulated 60 seconds of sinusoidal chest displacement at 15 breaths/min
  with a 4 mm peak excursion and 0.80 m mean range. Implemented the
  proposal's complex range-bin model at 100 frames/s, with 4.29 cm bins,
  a 20 kHz carrier, and a Gaussian spread into neighboring bins.
  Started at the range map stage and subtracted each bin's full-window
  mean for static clutter removal. Selected a bin by breathing-band
  energy, unwrapped its phase, and estimated rate from the largest
  spectral bin between 0.10 and 0.70 Hz.
- **Simulation results:** the clean case and the case with seeded
  additive complex Gaussian noise both recovered 15.0 breaths/min
  with 0.0 breaths/min absolute error at the 1 breath/min spectral
  resolution. The noise standard deviation was 0.12 per real and
  imaginary component relative to unit reflector amplitude. Both
  selected the bin centered at 0.8146 m. The run did not generate
  audio or validate phone recordings.
- Separately screened local `sdb1` in 30-second stage windows.
  Rejected any window where either belt reached or crossed its
  declared calibration limits. Selected REM at EDF-relative
  15,030–15,060 s. At 64 Hz, chest ranged from −1.072 to 0.676 mV
  within ±2.5 mV, and abdomen ranged from −0.360 to 0.381 mV within
  ±1.25 mV. Native Pearson correlation was 0.949, and both traces
  peaked at 0.367 Hz (22 breaths/min on the 30-second grid).
  This short window is suitable as a waveform input for a simulator
  trial. Belt voltages would require an assumed scaling to displacement.
- Saved the [time-aligned segment plot](../reports/sdb1_clean_breathing_segment.svg)
  (46,661 bytes). Reproduce the synthetic cases with
  `poetry run python -m nightecho.sonar_sim`. All 15 tests passed.

#### 30-second simulation results

- Used the 1,920 local `sdb1` chest samples from EDF-relative
  15,030–15,060 s. Assumed that one population standard deviation of
  belt voltage corresponds to 3 mm of chest displacement. With segment
  mean −0.005746 mV and standard deviation 0.533897 mV, the mapping
  was `displacement_mm = 5.619065 × (voltage_mV + 0.005746)`.
  This scale was chosen for the simulator and was not measured on the
  subject. Linearly interpolated the belt to 100 Hz, holding the last
  value for the final fractional source interval.
- Used the same peak-bin estimator for the belt and echo phase, after
  averaging each into 300 values at 10 Hz. The 30-second window gives
  0.0333 Hz spacing, or 2 breaths/min, and the estimator uses no
  interpolation between spectral bins.
- **Belt-driven simulation:** the chest belt and clean simulated
  echoes both estimated 22 breaths/min. Echo minus belt was
  0 breaths/min on the 2 breaths/min grid.
- **Off-grid simulation:** a 21 breaths/min sinusoid falls halfway
  between the 20 and 22 breaths/min bins. Both the direct synthetic
  displacement and the clean echoes estimated 20 breaths/min, a
  signed error of −1 breath/min and an absolute error of 1 breath/min.
- Reproduce with `poetry run python -m nightecho.sonar_sim --30-second-review`.
  No waveform or echo files were written. All 16 tests passed.
