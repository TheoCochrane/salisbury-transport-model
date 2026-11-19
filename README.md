# Salisbury Transport Model

A personal learning project to build a validated AM peak four-step transport model of Salisbury, using public data and TAG guidance.

**This is a personal learning project. It is not affiliated with the Department for Transport (DfT) or Wiltshire Council.**

## Scope and ground rules

- Public data only: anything that can be found and downloaded through a normal web search, without a login tied to any job.
- Built on my own laptop, in my own time, with my own GitHub account. No unpublished models or files from work are used.
- One exception, for validation only: the Google Maps Platform Routes API, on a personal Google account. It is not open data and is never used to set model inputs, only to benchmark journey times.

## Structure

- `environment.yml`: the conda environment specification.
- `docs/methodology.md`: a running record of every assumption, source and parameter. This is the model report in progress.
- `notebooks/`: analysis notebooks, including the four-zone toy model.
- `src/`: reusable code, added as the model develops.
- `tests/`: automated checks for the environment and model components.
- `data/` and `outputs/`: local only, not committed.

## Setup

```
conda env create -f environment.yml   # or: conda env update -n salisbury -f environment.yml
conda activate salisbury
pytest -m "not network"
```

Coordinate system: all distance calculations use British National Grid (EPSG:27700).
