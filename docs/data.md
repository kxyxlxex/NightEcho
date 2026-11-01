# CAP data prep

Source: https://physionet.org/content/capslpdb/1.0.0/
License: Open Data Commons Attribution 1.0.
Cite Terzano et al., Sleep Medicine 2001, 2(6):537–553, and PhysioNet as requested
on the source page when publishing results.

## Current scope

The inventory lists the documented 108 records. The planned cohort excludes five
narcolepsy records, leaving 103 candidates including the two bruxism records.
These are planned counts, not quality-approved or downloaded subjects. Age and sex
are not filled in yet. File presence is refreshed by rerunning the inventory command.

The parser reads sleep-stage events from CAP text reports and skips CAP arousals.
S3 and S4 merge into n3. Movement time and unscored intervals stay unknown.
Intervals retain their durations and gaps; unknown time is not silently deleted.
Onsets are seconds from the first annotation event, with midnight rollover handled.
They are not yet aligned to the EDF recording start. CSV rows are stage intervals,
not a guaranteed complete grid of 30-second epochs.

The EDF inspector reports channel names, physical units, and individual sampling
rates. It does not assume every record has the same channels or sampling rate.
No raw signal preprocessing, clinical prediction, or model training is implemented.

## Storage

Only the small n1 annotation sample has been downloaded. Raw and generated data
are ignored by git. The complete CAP release is about 40.1 GB; individual EDF files
can be hundreds of MB. Discuss the exact download size before fetching any EDF.
Keep any approved downloads and Python environment inside this project folder.

## Next steps

1. Approve one small EDF download and inspect its channels and units.
2. Align annotations to the recording start and make a 30-second label grid.
3. Add explicit channel aliases after checking actual headers.
4. Load selected signals, filter, and resample with per-channel sample rates.
5. Record missing channels and quality exclusions before fixing the final cohort.

Keep all versions of one subject together when train/test splits are introduced.
The simulator will need separate validation against real sonar before any clinical
performance claim.

## First recording check

Downloaded n16 after approval: 30,801,536 bytes (29.4 MiB), plus its annotation file.
Its actual EDF header has only five EEG channels at 100 Hz. It has no breathing
or tibial EMG channels, so it cannot support the planned sonar simulation inputs.
Do not count it as a usable subject for that pipeline.

The new prep command aligns stage clocks to EDF start and writes complete
30-second epochs. For n16 the annotation offset is 30 seconds. There are 1,026
complete epochs, seven unknown, and a final 20-second fragment omitted.
Epochs with gaps, mixed stages, or overlapping annotations remain unknown.
Clock alignment assumes the annotation date matches the EDF recording date.
Channel aliases are provisional; unmatched labels require manual review.

A 16 KiB range request for n6's header showed no clearly named breathing or leg
channels either. The ambiguous THE label is not mapped without verification.
No n6 signal data was downloaded. Signal loading and filtering remain pending a
recording with confirmed suitable channels. Inspect headers before choosing the
next full download.

## Header survey, 2026-11-01

Inspected five additional 16 KiB header slices; the inventory is in
`data/metadata/channel_inventory.csv`. No full recordings were downloaded.

- n1 has TORACE, ADDOME, TERMISTORE, and paired DX/SX channels.
- rbd1 has TORACE and ADDOME, but no clearly named airflow channel.
- rbd2 has no clearly labeled breathing channels.
- plm1 and sdb1 have TORACE, ADDDOME, and explicit TIB Sx/TIB Dx channels.
- plm1 has two Flusso channels. Their roles need review before mapping airflow.

Added breathing aliases for TORACE, ADDOME/ADDDOME, and TERMISTORE, and leg
aliases for explicit TIB Sx/TIB Dx. Generic DX/SX pairs remain unmapped until their
sensor identity is verified. These findings mean the planned 103-subject cohort
cannot be assumed usable without a channel audit. Missing airflow alone need not
exclude a record if the analysis uses only respiratory effort and leg EMG.
