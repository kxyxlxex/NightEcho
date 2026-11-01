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
