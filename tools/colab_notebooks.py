"""Keep the course's notebooks ready for Google Colab.

The site repository's public/downloads holds the reference notebooks and workbooks (the DCT Simulator pins their
bytes, so they are never edited there). This tool copies them into downloads/, which the "Open in Colab" links
open, and adds two things for Colab readers, in downloads/ and in labs/:

* a note in the first cell: run the notebook from the top with Runtime > Run all;
* one guard line at the top of every code cell after the first, so that a cell run before the setup cell (after
  opening the notebook, or after Colab restarts its runtime) says what to do instead of raising NameError.

Nothing else changes: the code, the wording and the checks are the reference notebook's. The tool is idempotent.

    python3 tools/colab_notebooks.py [--site ../pixel-perfect-show-8533]   # sync from the site, then add the guards
    python3 tools/colab_notebooks.py --no-sync                              # add the guards only
"""
import argparse, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTE = ("\n\n> **Running in Google Colab:** choose **Runtime ▸ Run all** (Ctrl+F9). Each cell uses names that the "
        "cells above it define, so after opening the notebook, or after the runtime restarts, run it from the top.")
GUARD = ('if "SEED" not in globals(): raise RuntimeError("Run the notebook from the top first: '
         'Runtime > Run all (Ctrl+F9).")  # Colab guard\n')


def lines(text: str) -> list[str]:
    out = text.splitlines(keepends=True)
    return out


def prepare(path: Path) -> bool:
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb["cells"]
    changed = False
    first_md = next(c for c in cells if c["cell_type"] == "markdown")
    src = "".join(first_md["source"])
    if "Running in Google Colab" not in src:
        first_md["source"] = lines(src.rstrip("\n") + NOTE)
        changed = True
    code = [c for c in cells if c["cell_type"] == "code"]
    if "SEED" not in "".join(code[0]["source"]):
        raise SystemExit(f"{path.name}: the first code cell does not define SEED")
    for c in code[1:]:
        src = "".join(c["source"])
        if not src.startswith(GUARD):
            c["source"] = lines(GUARD + src)
            changed = True
    if changed:
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=str(ROOT.parent / "pixel-perfect-show-8533"))
    ap.add_argument("--no-sync", action="store_true")
    a = ap.parse_args()
    if not a.no_sync:
        src = Path(a.site) / "public" / "downloads"
        for f in sorted(src.glob("DCT_V*_Ch*_Lab.*")):
            if f.suffix in (".ipynb", ".xlsx"):
                shutil.copyfile(f, ROOT / "downloads" / f.name)
    n = sum(prepare(p) for p in sorted((ROOT / "downloads").glob("*.ipynb")) + sorted((ROOT / "labs").glob("*.ipynb")))
    print(f"{n} notebooks prepared for Colab")


if __name__ == "__main__":
    main()
