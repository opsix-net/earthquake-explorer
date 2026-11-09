# Earthquake Explorer

Search a bundled USGS earthquake snapshot by location text and minimum magnitude.
The program reports match counts, strongest magnitude, mean reported magnitude,
and the ten strongest matching records. The data stays fixed so examples and
checks remain reproducible.

[Launch the public Binder notebook](https://mybinder.org/v2/gh/opsix-net/earthquake-explorer/main?urlpath=lab/tree/earthquake_explorer.ipynb)

No account or API key is required by the reader. Binder may take several minutes
to build or start. Its temporary sessions are not permanent storage.

## Run in Binder

1. Open the launch link and wait for JupyterLab.
2. Select Run > Run All Cells for the demonstration and offline tests.
3. Change LOCATION and MINIMUM_MAGNITUDE in the Search cell and rerun it.
4. For the interactive menu, open File > New > Terminal and run
   `python earthquake_explorer.py`.

## Run locally

Requires Python 3.10 or later. The application has no external dependencies.
Run these commands from this repository's root:

```bash
python3 earthquake_explorer.py
python3 -m unittest discover -s tests -v
```

Example menu inputs: `1`, `Alaska`, `3`, then `2` to exit. Blank location searches
all places. Minimum magnitude is inclusive and must be between 2.5 and 10.
Letters, NaN, infinity, and out-of-range values are rejected and retried.

## Data and interpretation

The original CSV and its source URL, retrieval time, event range, and SHA-256
are under `data/`. Source: [USGS CSV feeds](https://earthquake.usgs.gov/earthquakes/feed/v1.0/csv.php).
This is a captured M2.5+ past-seven-days feed, not live monitoring or a complete
historical catalog. Records can later be revised by USGS. Search uses a
case-insensitive substring of the reported place, not a geographic radius.
Non-earthquake events, malformed records, non-finite numeric values, and repeated
IDs are skipped and counted. Mean reported magnitude does not mean average energy.

## Project files

- `earthquake_explorer.py`: full commented application and command-line menu.
- `earthquake_explorer.ipynb`: runnable examples, source view, and test runner.
- `tests/test_explorer.py`: offline behavior and data checks.
- `data/earthquakes.csv`: unmodified source snapshot.
- `data/provenance.json`: source and integrity metadata.
- `.binder/requirements.txt`: standard-library application; Binder supplies Jupyter.
- `specsheet.txt`: reusable publishing and replication workflow.

The submission journal is retained locally, separate from this public source
repository. Review its name, submission date, and course IDE requirements before
submission. The repository is public, but no open-source license grant is implied.
