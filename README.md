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

## Run data prep

Python 3.11 or newer is enough for the current tools. No packages need installing.
Run from this folder:

```sh
PYTHONPATH=src python3 -m nightecho.cap inventory
PYTHONPATH=src python3 -m nightecho.cap stages --record n1
PYTHONPATH=src python3 -m nightecho.cap inspect --record n1
PYTHONPATH=src python3 -m unittest discover -s tests -v
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
