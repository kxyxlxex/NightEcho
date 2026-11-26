# NightEcho

A research prototype for contactless sleep monitoring with phone sonar.

## Folders

- `src/nightecho/`: shared Python tools, starting with CAP data prep
- `data/raw/`: local source files, ignored by git
- `data/metadata/`: record inventory and inclusion decisions
- `data/interim/`: parsed annotations and header reports, ignored by git
- `data/processed/`: cleaned signals for later experiments, ignored by git
- `sim/`, `features/`, `models/`: upcoming simulation and modeling work
- `app/`: upcoming phone prototype
- `docs/`: data notes and lab notebook
- `reports/`: generated figures and results, ignored by git
- `tests/`: data prep checks

## Codespaces development

From the repository root, use CPython 3.14.2 and Poetry 2.5.2 to reproduce the
tested setup. In the current Codespace, `python3` resolves to that interpreter.
Poetry installs the project in the repository's `.venv` using `poetry.lock`.
The current tools have no third-party runtime dependencies.

```sh
poetry env use python3
poetry check --lock
poetry sync
poetry run python -m unittest discover -s tests -v
```

The source tools also run directly with Python 3.11 or newer:

```sh
PYTHONPATH=src python3 -m nightecho.cap inventory
PYTHONPATH=src python3 -m nightecho.cap stages --record n1
PYTHONPATH=src python3 -m nightecho.cap inspect --record n1
```

The stage command needs `data/raw/cap/n1.txt`. The inspect command needs
`data/raw/cap/n1.edf` and reads only its header, without loading signal samples.
There is no automatic downloader. Large files require a size check and user approval.
All tool outputs stay inside this project.

See [data notes](docs/data.md) for the source, scope, and next steps.

To align annotations and check channel availability for a local recording:

```sh
PYTHONPATH=src python3 -m nightecho.prep --record n16
```

This writes a small epoch CSV and a prep report under `data/interim/cap/`.

To load a local CAP recording and print waveform quality and label counts:

```sh
poetry run python -m nightecho.waveform --record n8
```

In Python, `nightecho.waveform.load_night("n8")` returns calibrated waveforms
at their native rates, channel metadata, missing channel names, and the
30-second label grid. Call `waveform.epoch_samples(epoch)` for the samples
in that epoch. Keep the paired EDF and annotation files in `data/raw/cap/`.
