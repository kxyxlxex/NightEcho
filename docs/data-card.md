# CAP data card: header audit

All 108 published record headers were inspected on 2026-11-01.
Header downloads used less than 1.8 MB. No new full recordings were downloaded.

31 non-narcolepsy records have clearly labeled thoracic channels.
Their complete EDF files total approximately 11.80 GB.
This is a header-based candidate count, not a quality-approved cohort.

Only four candidates also have explicit TIB Sx/TIB Dx labels. Other records use
ambiguous DX/SX labels that need sensor verification. No RBD record has the explicit
TIB pair under this label rule; this does not establish that leg signals are absent.
13 of 22 RBD headers have a clearly labeled thoracic channel.

The proposal's 103-record analysis cannot be assumed feasible with complete
breathing and leg channels. Cohort selection and diagnosis imbalance need review
before training. Phase 1 remains incomplete: waveform quality checks, preprocessing,
demographics, and pretraining data have not been completed.

The complete audit is in data/metadata/channel_audit.csv. Reproduce with
python3 scripts/audit_cap.py. Raw headers stay ignored by git.

## First waveform spot check, 2026-11-23

`n8` (control) is the smallest audited candidate with thoracic effort and
explicit bilateral tibial EMG. PhysioNet confirmed the EDF size of 92,527,040
bytes (88.24 MiB). The header identifies piezo thorax and abdomen channels at
10 Hz, nasal pressure at 20 Hz, and left and right tibial EMG at 200 Hz.

Three 30-second windows starting 1,500, 15,000, and 28,500 seconds from EDF start
used 277,200 waveform bytes. All five mapped channels varied in each window,
and none reached the EDF digital rails. Thorax peak-to-peak spans were 41, 7,
and 10 digital counts (about 0.031, 0.005, and 0.008 mV). The low excursion
warrants a closer look at breathing morphology and agreement with nasal pressure.
Use `n8` as the first preprocessing trial. The approved full-night download,
waveform quality metrics, and label alignment are recorded in the
[lab notebook](notebook.md#full-n8-waveform-loading).
