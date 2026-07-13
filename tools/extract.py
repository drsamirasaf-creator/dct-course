#!/usr/bin/env python3
"""DCT course website extraction pipeline.
Parses manuscript LaTeX (Vol 1 & 2) -> data/chapters.json
Extracts: title, part, sections, LOS, exercises (A-D groups), AXIOM modules.
"""
import re, json, glob, os

SRC = os.path.join(os.path.dirname(__file__), 'sources')

# ---------- LaTeX -> plain/markdown-ish text cleanup ----------
MACROS_INLINE = {
    r'\\textbf\{([^{}]*)\}': r'**\1**',
    r'\\emph\{([^{}]*)\}': r'*\1*',
    r'\\textit\{([^{}]*)\}': r'*\1*',
    r'\\textsf\{([^{}]*)\}': r'\1',
    r'\\texttt\{([^{}]*)\}': r'`\1`',
    r'~': ' ',
    r'\\&': '&',
    r'\\%': '%',
    r'\\#': '#',
    r'\\_': '_',
    r'\\ldots': '…',
    r"``": '"', r"''": '"',
    r'\\adv': '★',
}

def clean(text):
    t = text
    # resolve \ref/\eqref/\Cref to readable placeholders
    t = re.sub(r'(Theorem|Proposition|Lemma|Corollary|Definition|Example|Exercise|Figure|Table|Section|Chapter|Equation|Remark|Algorithm)~?\\ref\{[^}]*\}', r'\1 (see book)', t)
    t = re.sub(r'\\eqref\{[^}]*\}', '(see book)', t)
    t = re.sub(r'\\ref\{[^}]*\}', '(see book)', t)
    t = re.sub(r'\\label\{[^}]*\}', '', t)
    t = re.sub(r'\\cite[tp]?\{[^}]*\}', '', t)
    t = re.sub(r'\\footnote\{[^{}]*\}', '', t)
    t = re.sub(r'\\website\{(\d+)\}', r'Course Website, Chapter \1', t)
    t = re.sub(r'\\axmodule\{([^}]*)\}', r'\1', t)
    for pat, rep in MACROS_INLINE.items():
        t = re.sub(pat, rep, t)
    t = re.sub(r'%.*', '', t)          # comments
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def first_sentence(text, maxlen=160):
    t = clean(text)
    # cut at first sentence end outside math
    depth = 0
    for i, c in enumerate(t):
        if c == '$':
            depth ^= 1
        elif c in '.?!' and depth == 0 and i > 20:
            return t[:i+1]
    return (t[:maxlen] + '…') if len(t) > maxlen else t

# ---------- parsers ----------
def parse_chapter(path, vol):
    t = open(path).read()
    ch = int(re.search(r'chapter_(\d+)', path).group(1))
    # title (may span lines)
    m = re.search(r'\\chapter\{(.+?)\}\s*\n', t, re.S)
    title = re.sub(r'\s+', ' ', m.group(1)).strip() if m else f'Chapter {ch}'

    # sections (numbered only)
    sections = [re.sub(r'\s+', ' ', s).strip()
                for s in re.findall(r'\\section\{([^}]+)\}', t)]

    # LOS block
    los = []
    mb = re.search(r'section\*\{Learning Outcome Statements\}(.*?)\\end\{enumerate\}', t, re.S)
    if mb:
        block = mb.group(1)
        items = re.split(r'\\item\s', block)[1:]
        for it in items:
            lab = re.search(r'\\label\{(los:[^}]+)\}', it)
            los.append({'id': lab.group(1) if lab else '',
                        'text': clean(re.sub(r'\\label\{[^}]*\}', '', it))})

    # Exercises: split section, find Part A-D subsections
    exercises = []
    mex = re.search(r'\\section\{Exercises\}(.*?)(\\section\{Notes|\\section\{References|\\begin\{thebibliography)', t, re.S)
    if mex:
        exblock = mex.group(1)
        parts = re.split(r'\\subsection\*\{Part ([A-D])[^}]*\}', exblock)
        # parts = [pre, 'A', blockA, 'B', blockB, ...]
        for i in range(1, len(parts), 2):
            grp, blk = parts[i], parts[i+1]
            for it in re.split(r'\\item\s', blk)[1:]:
                lab = re.search(r'\\label\{(exc:[^}]+)\}', it)
                starred = '\\adv' in it[:80] or '★' in it[:80]
                exercises.append({
                    'group': grp,
                    'id': lab.group(1) if lab else '',
                    'starred': starred,
                    'descriptor': first_sentence(re.sub(r'\\label\{[^}]*\}', '', it))
                })

    axiom = sorted(set(re.findall(r'AXIOM-(\d+)', t)), key=int)
    return {
        'vol': vol, 'ch': ch, 'title': title,
        'sections': sections, 'los': los,
        'exercises': exercises,
        'axiom_modules': [f'AXIOM-{a}' for a in axiom],
        'n_los': len(los), 'n_exercises': len(exercises),
    }

def parse_parts(main_path):
    """Map chapter number -> part title from main.tex \\part + \\include order."""
    t = open(main_path).read()
    order, current = {}, None
    for m in re.finditer(r'\\part\{([^}]+)\}|\\include\{chapter_(\d+)\}', t):
        if m.group(1):
            current = re.sub(r'\s+', ' ', m.group(1)).strip()
        elif m.group(2):
            order[int(m.group(2))] = current
    return order

def main():
    out = []
    for vol, d in [(1, 'vol1_manuscript'), (2, 'vol2_manuscript')]:
        parts = parse_parts(os.path.join(SRC, d, 'main.tex'))
        for f in sorted(glob.glob(os.path.join(SRC, d, 'chapter_*.tex'))):
            c = parse_chapter(f, vol)
            c['part'] = parts.get(c['ch'], '')
            out.append(c)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)
    with open(os.path.join(os.path.dirname(__file__), 'data', 'chapters.json'), 'w') as fh:
        json.dump(out, fh, indent=1)
    # sanity report
    print(f"chapters: {len(out)}")
    print(f"LOS total: {sum(c['n_los'] for c in out)}")
    print(f"exercises total: {sum(c['n_exercises'] for c in out)}")
    for c in out:
        flag = '' if (c['n_los'] and c['n_exercises'] and c['axiom_modules']) else '  <-- CHECK'
        print(f"V{c['vol']}.{c['ch']:02d} [{(c['part'] or '')[:28]:28s}] LOS={c['n_los']:2d} ex={c['n_exercises']:2d} axiom={','.join(c['axiom_modules'])}{flag}")

if __name__ == '__main__':
    main()
