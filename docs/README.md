# Docs

| Path | What it is |
|---|---|
| `methodology.md` | The running model report: every assumption, source and parameter, with its TAG status. |
| `toy-model-visual-guide.pdf` | The toy model explained in figures, with no code: 12 A4 pages. Generated from the notebook by `src/make_visual_guide.py`; rerun it after changing the model. |
| `tag/` | Copies of the TAG units and data books the notebook and methodology cite. See `tag/README.md` for versions and download status. |
| `project/` | The self-study project plan (PDF). |
| `reference/` | Background reading (PDF). Not cited as a source for model values. |

The PDFs in `project/` and `reference/` are gitignored (`*.pdf`), so they stay local and are not committed. `toy-model-visual-guide.pdf` is the one exception: it is our own output, so it is tracked.
