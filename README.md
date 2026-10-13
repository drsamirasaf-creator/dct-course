# dct-course

Course website for **Dynamic Corporate Transformation** (Samir Asaf, two volumes) —
a one-semester graduate course: 32 chapters across 14 weeks, with per-chapter lecture
decks, seeded Python notebooks, seeded Excel workbooks, and the AXIOM computational
laboratory.

Built with [Quarto](https://quarto.org). Chapter pages are generated from
`data/chapters.json` by `tools/generate_site.py` — edit the generator, not the
`chapters/*.qmd` files, then rerun `python3 tools/generate_site.py`.

Deployment: see `DEPLOY.md`.

Notebooks: `downloads/` holds the notebooks and workbooks the site's "Open in Colab" links open. They are copies of
the site repository's `public/downloads` with a Colab note and a run-order guard added; refresh them with
`python3 tools/colab_notebooks.py` (it also prepares `labs/`).
