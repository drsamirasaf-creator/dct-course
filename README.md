# dct-course

Course website for **Dynamic Corporate Transformation** (Samir Asaf, two volumes) —
a one-semester graduate course: 32 chapters across 14 weeks, with per-chapter lecture
decks, seeded Python notebooks, seeded Excel workbooks, and the AXIOM computational
laboratory.

Built with [Quarto](https://quarto.org). Chapter pages are generated from
`data/chapters.json` by `tools/generate_site.py` — edit the generator, not the
`chapters/*.qmd` files, then rerun `python3 tools/generate_site.py`.

Deployment: see `DEPLOY.md`.
