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
