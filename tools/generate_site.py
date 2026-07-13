#!/usr/bin/env python3
"""Generate the dct-course Quarto site from data/chapters.json."""
import json, os, textwrap

# Layout-aware paths: run from tools/ inside the repo (SITE = repo root),
# or from the authoring sandbox (SITE = ./dct-course).
_HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_HERE) == 'tools':
    SITE = os.path.dirname(_HERE)
else:
    SITE = os.path.join(_HERE, 'dct-course')
CH = json.load(open(os.path.join(SITE, 'data', 'chapters.json')))

# ---------------- 14-week allocation (locked with author) ----------------
WEEKS = [
    (1,  [(1,1),(1,2)],        "DCT vision; enterprise systems"),
    (2,  [(1,3),(1,4)],        "Mathematical foundations; modeling principles"),
    (3,  [(1,5),(1,6)],        "Enterprise state; transformation operators"),
    (4,  [(1,7),(1,8)],        "Dynamic systems; stochastic dynamics"),
    (5,  [(1,9),(1,10),(1,11)],"The architectures: state, capital, performance"),
    (6,  [(1,12),(1,13)],      "Risk, resilience, robustness; UETA"),
    (7,  [(1,14),(1,15),(1,16)],"Analysis of UETA; the GEOP; synthesis — Midterm"),
    (8,  [(2,1),(2,2)],        "Enterprise optimization; GEOP revisited"),
    (9,  [(2,3),(2,4)],        "Convex; nonlinear"),
    (10, [(2,5),(2,6)],        "Dynamic optimization; optimal control (PMP)"),
    (11, [(2,7),(2,8),(2,9)],  "The Bellman arc: DP, HJB, stochastic control"),
    (12, [(2,10),(2,11)],      "The robustness pair: NF-REO, DRO"),
    (13, [(2,12),(2,13)],      "Multi-objective; machine learning"),
    (14, [(2,14),(2,15),(2,16)],"AI; digital twins; case-study capstone — Final"),
]
WEEK_OF = {vc: w for w, chs, _ in WEEKS for vc in chs}

def chap(v, c):
    return next(x for x in CH if x['vol'] == v and x['ch'] == c)

def slug(v, c):
    return f"v{v}ch{c:02d}"


def dl(v, n, suffix):
    """Link a download if the file exists in SITE/downloads, else mark forthcoming."""
    fname = f"DCT_V{v}_Ch{n:02d}_{suffix}"
    if os.path.exists(os.path.join(SITE, 'downloads', fname)):
        return f"[`{fname}`](../downloads/{fname})"
    return f"`{fname}` *(forthcoming)*"

GROUP_NAMES = {'A': 'Part A — Concept checks', 'B': 'Part B — Mathematical exercises',
               'C': 'Part C — Computational exercises', 'D': 'Part D — Enterprise applications'}

def seed(v, c):
    return f"26{v}{c:02d}"

os.makedirs(os.path.join(SITE, 'chapters'), exist_ok=True)
os.makedirs(os.path.join(SITE, 'assets'), exist_ok=True)
os.makedirs(os.path.join(SITE, 'styles'), exist_ok=True)

# ---------------- chapter pages ----------------
for c in CH:
    v, n = c['vol'], c['ch']
    wk = WEEK_OF[(v, n)]
    axiom_links = ' · '.join(
        f"[{m} →](https://axiom-webapp.example/modules/{m.lower()})" for m in c['axiom_modules'])
    los_md = '<ol class="los-list">' + ''.join(f"<li>{l['text']}</li>" for l in c['los']) + '</ol>'
    secs_md = '\n'.join(f"{i+1}. {s}" for i, s in enumerate(c['sections']))
    ex_md = []
    cur = None
    num = 0
    for e in c['exercises']:
        num += 1
        if e['group'] != cur:
            cur = e['group']
            ex_md.append(f"\n<h4 class='ex-part'>{GROUP_NAMES.get(cur, 'Part ' + cur)}</h4>\n")
        star = ' ★' if e['starred'] else ''
        desc = e['descriptor'].lstrip('★').lstrip()
        ex_md.append(f"- **Exercise {n}.{num}{star}** — {desc}")
    ex_md = '\n'.join(ex_md)

    body = f"""---
title: "Chapter {n} · {c['title']}"
subtitle: "Volume {'I' if v==1 else 'II'} · {c['part']} · Week {wk}"
---

::: {{.chapter-meta}}
**Volume {'I' if v==1 else 'II'}, Chapter {n}** · Taught in [Week {wk}](../schedule.html#week-{wk}) · Lab seed `{seed(v,n)}`
:::

## Learning Outcome Statements

After completing this chapter, the reader should be able to:

```{{=html}}
{los_md}
```

## Reading Guide

Work through the chapter in section order; the full development, proofs, and worked
examples are in the book — this page indexes them and does not replace them.

{secs_md}

## AXIOM Laboratory

This chapter is instrumented by: {axiom_links}

Launch the module, load the chapter model, modify inputs, run the optimization,
and compare against the worked examples in the book.

## Exercises

{len(c['exercises'])} exercises, grouped **A** concept checks · **B** mathematical ·
**C** computational · **D** enterprise applications. Starred (★) exercises are on the
advanced track. **Full solutions appear in the Instructor's Manual, Chapter {n}.**
{ex_md}

## Downloads

| Resource | File | Seed |
|---|---|---|
| Lecture deck | {dl(v,n,'Slides.pptx')} | — |
| Python notebook | {dl(v,n,'Lab.ipynb')} | `{seed(v,n)}` |
| Excel workbook | {dl(v,n,'Lab.xlsx')} | `{seed(v,n)}` |

::: {{.callout-note appearance="simple"}}
All three companions consume the same seeded engine (`{seed(v,n)}`), so their numbers
agree by construction — the MFMF convention, carried forward.
:::
"""
    with open(os.path.join(SITE, 'chapters', f"{slug(v,n)}.qmd"), 'w') as f:
        f.write(body)

# ---------------- schedule ----------------

rows = []
for w, chs, theme in WEEKS:
    links = '<br>'.join(
        f'<a href="chapters/{slug(v,c)}.html">V{"I" if v==1 else "II"}.{c} — {chap(v,c)["title"]}</a>'
        for v, c in chs)
    theme_html = theme
    for tag in ('Midterm', 'Final'):
        theme_html = theme_html.replace(f'— {tag}', f'<br><span class="milestone">&#9670; {tag}</span>')
    cls = ' class="boundary"' if w == 7 else ''
    rows.append(f'<tr id="week-{w}"{cls}><td><span class="wkb">{w}</span></td>'
                f'<td>{links}</td><td class="theme">{theme_html}</td></tr>')
schedule = f"""---
title: "14-Week Schedule"
subtitle: "32 chapters · two volumes · one semester"
---

The course runs Volume I in weeks 1–7 (posing the General Enterprise Optimization
Problem) and Volume II in weeks 8–14 (solving it). The double rule marks the volume
boundary: the midterm sits exactly where the GEOP is posed. Instructors may
re-balance — every chapter page is self-contained.

```{{=html}}
<table class="sched">
<thead><tr><th>Week</th><th>Chapters</th><th>Theme</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody></table>
```
"""
open(os.path.join(SITE, 'schedule.qmd'), 'w').write(schedule)

# ---------------- index ----------------

def ch_card(c):
    v, n = c['vol'], c['ch']
    wk = WEEK_OF[(v, n)]
    ax = c['axiom_modules'][0] if c['axiom_modules'] else ''
    return (f'<a class="ch-card" href="chapters/{slug(v,n)}.html">'
            f'<span class="wk">WK {wk}</span>'
            f'<span class="num">{n}</span>'
            f'<span class="t" style="display:block">{c["title"]}</span>'
            f'<span class="meta">{c["n_los"]} LOS · {c["n_exercises"]} EX · {ax}</span>'
            f'</a>')

def part_grids(vol):
    parts, order = {}, []
    for c in CH:
        if c['vol'] == vol:
            if c['part'] not in parts:
                parts[c['part']] = []; order.append(c['part'])
            parts[c['part']].append(c)
    out = []
    roman = 'I' if vol == 1 else 'II'
    for i, p in enumerate(order, 1):
        cards = '\n'.join(ch_card(c) for c in parts[p])
        out.append(f'<div class="part-band"><span class="eyebrow">Volume {roman} · Part {i}</span>'
                   f'<h3>{p}</h3></div>\n<div class="ch-grid">\n{cards}\n</div>')
    return '\n'.join(out)

HERO_SVG = """<svg class="hero-svg" viewBox="0 0 560 420" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <g fill="none" stroke="#7FC8A9" stroke-opacity="0.22" stroke-width="1">
    <ellipse cx="400" cy="150" rx="150" ry="86" transform="rotate(-18 400 150)"/>
    <ellipse cx="400" cy="150" rx="112" ry="62" transform="rotate(-18 400 150)"/>
    <ellipse cx="400" cy="150" rx="76" ry="40" transform="rotate(-18 400 150)"/>
    <ellipse cx="400" cy="150" rx="42" ry="21" transform="rotate(-18 400 150)"/>
  </g>
  <g stroke="#7FC8A9" stroke-opacity="0.12" stroke-width="1">
    <path d="M40 360 H540"/><path d="M40 300 H540"/><path d="M40 240 H540"/>
    <path d="M100 400 V60"/><path d="M180 400 V60"/><path d="M260 400 V60"/>
  </g>
  <path class="traj-path" d="M60 385 C 150 370, 175 330, 205 285 S 280 210, 330 190 S 385 165, 400 150"
        fill="none" stroke="#C8A24B" stroke-width="3.2" stroke-linecap="round"/>
  <circle cx="60" cy="385" r="6" fill="#EDE9DC"/>
  <circle cx="400" cy="150" r="7" fill="#C8A24B"/>
  <circle cx="400" cy="150" r="12" fill="none" stroke="#C8A24B" stroke-opacity="0.5"/>
  <text x="74" y="392" fill="#EDE9DC" font-family="STIX Two Text, serif" font-size="17" font-style="italic">x&#8320;</text>
  <text x="418" y="146" fill="#D9BE7A" font-family="STIX Two Text, serif" font-size="17" font-style="italic">x*</text>
  <text x="430" y="262" fill="#7FC8A9" fill-opacity="0.7" font-family="STIX Two Text, serif" font-size="13" font-style="italic">J(x,u) level sets</text>
</svg>"""

index = f"""---
pagetitle: "Dynamic Corporate Transformation — Graduate Course"
toc: false
---

```{{=html}}
<div class="dct-hero">
{HERO_SVG}
<div class="hero-copy">
<span class="eyebrow">Graduate course · 14 weeks · Two volumes</span>
<h1>The enterprise as a <em>dynamic system</em>. Transformation as an <em>optimization problem</em>.</h1>
<p>An evolving state governed by transformation operators, resourced by a capital
architecture, measured by a performance architecture, exposed through a risk
architecture — and steered, from <strong>x&#8320;</strong> to <strong>x*</strong>, by the
General Enterprise Optimization Problem.</p>
<a class="btn-hero" href="axiom.html">Open the AXIOM Laboratory</a>
<a class="btn-hero-outline" href="schedule.html">View the 14-week schedule</a>
</div>
</div>

<div class="stat-strip">
<div class="stat"><span class="n">32</span><span class="l">Chapters</span></div>
<div class="stat"><span class="n">2</span><span class="l">Volumes</span></div>
<div class="stat"><span class="n">14</span><span class="l">Weeks</span></div>
<div class="stat"><span class="n">301</span><span class="l">Learning outcomes</span></div>
<div class="stat"><span class="n">489</span><span class="l">Exercises</span></div>
<div class="stat"><span class="n">16</span><span class="l">AXIOM modules</span></div>
</div>

<div class="vol-arc">
<div class="vol"><span class="eyebrow">Volume I · Weeks 1–7</span>
<h3>Poses the problem</h3>
<p>Foundations and mathematical framework: states, operators, dynamics, and the five
enterprise architectures — culminating in the General Enterprise Optimization Problem.</p></div>
<div class="arc-arrow">&#10230;</div>
<div class="vol solve"><span class="eyebrow">Volume II · Weeks 8–14</span>
<h3>Solves it</h3>
<p>Convex, nonlinear, dynamic, optimal-control, stochastic, robust, multi-objective,
and AI-assisted solution theory — through digital twins and integrated case studies.</p></div>
</div>
```

## The four-part teaching system

The book is the controlling document of a chapter-aligned ecosystem: the two-volume
text, the Instructor's Manuals, this course website, and the **AXIOM computational
laboratory**. Every chapter page carries its Learning Outcome Statements, a reading
guide, an exercise index, its AXIOM modules, and three downloadable companions — a
lecture deck, a seeded Python notebook, and a seeded Excel workbook that agree by
construction.

## The chapters

```{{=html}}
{part_grids(1)}
{part_grids(2)}
```
"""
open(os.path.join(SITE, 'index.qmd'), 'w').write(index)

# ---------------- syllabus ----------------
syllabus = """---
title: "Syllabus"
subtitle: "One-semester graduate course · MBA, MSc, PhD, MFE, MQF"
---

## Course description

Dynamic Corporate Transformation (DCT) develops the enterprise as a dynamic system and
enterprise transformation as a mathematical optimization problem. Weeks 1–7 build the
framework (Volume I) and culminate in the General Enterprise Optimization Problem;
weeks 8–14 solve it (Volume II) across convex, nonlinear, dynamic, stochastic, robust,
multi-objective, and AI-assisted formulations, closing with digital twins and
integrated case studies.

## Materials

- **Required:** *Dynamic Corporate Transformation*, Volumes I & II.
- **Laboratory:** the AXIOM WebApp, plus per-chapter Python notebooks and Excel
  workbooks (this site, Downloads).
- Each chapter's page on this site is the index to its materials — start there each week.

## Assessment (default template — instructors adapt)

| Component | Weight |
|---|---|
| Weekly problem sets (from the A–D exercise groups) | 30% |
| Laboratory reports (AXIOM / notebook, seeded and validated) | 20% |
| Midterm (Volume I, week 7) | 20% |
| Capstone case study (week 14) | 30% |

## Weekly rhythm

Read the chapters before class; lecture follows the chapter's section flow; the lab
session runs the chapter's AXIOM modules; the problem set draws from the exercise
groups, with starred (★) exercises for the advanced track. Full solutions are in the
Instructor's Manual — instructors, see [Instructor Resources](instructor.qmd).
"""
open(os.path.join(SITE, 'syllabus.qmd'), 'w').write(syllabus)

# ---------------- axiom portal ----------------
axiom = """---
title: "AXIOM Laboratory"
subtitle: "The computational companion to both volumes"
---

AXIOM is the enterprise-optimization laboratory of the DCT ecosystem. Every chapter is
instrumented by one or more AXIOM modules; the chapter page links its modules directly.

The canonical workflow, for every chapter:

**Launch AXIOM → Load Chapter Model → Modify Inputs → Run Optimization → Visualize
Results → Download Report**

[Open the AXIOM WebApp →](https://axiom-webapp.example){.btn-hero}

| Module | Instruments | Chapters |
|---|---|---|
| AXIOM-01–04 | Foundations: state inspectors, modeling benches | I.1–4, II.1–4 |
| AXIOM-05–08 | Dynamics: trajectories, stability, stochastic fans | I.5–8, II.5–8 |
| AXIOM-09–12 | Architectures & robust optimization | I.9–12, II.9–12 |
| AXIOM-13–16 | Integration, ML/AI, digital twins, cases | I.13–16, II.13–16 |
"""
open(os.path.join(SITE, 'axiom.qmd'), 'w').write(axiom)

# ---------------- labs / downloads ----------------
labs = """---
title: "Labs & Downloads"
subtitle: "One deck, one notebook, one workbook per chapter — 96 files, one seed scheme"
---

Every chapter ships three companions on the seed `26VCC` (V = volume, CC = chapter):
the lecture deck, the Python notebook, and the Excel workbook. Notebook and workbook
consume the same seeded engine, so their numbers agree by construction; panel-level
seeds append two digits (`26208·01`).

Files are posted here chapter-by-chapter as they are released; each chapter page's
Downloads table links its own three files.

| Volume | Chapters | Status |
|---|---|---|
| I | 1–16 | In production |
| II | 1–16 | In production |
"""
open(os.path.join(SITE, 'labs.qmd'), 'w').write(labs)

# ---------------- instructor gate ----------------
instructor = """---
title: "Instructor Resources"
subtitle: "Restricted — access code inside the Instructor's Manual"
---

::: {.callout-important}
## Access
This area is for verified instructors. The **access code is printed in the front
matter of the Instructor's Manual** (either volume). Enter it below to unlock.
:::

Behind this gate: per-chapter **Teaching Maps**, **LOS guidance and assessment notes**,
solution references keyed to the IM chapters, syllabus variants, and slide source files.
Full worked solutions remain in the Instructor's Manuals themselves.

*(The encryption gate is applied at deploy time via Staticrypt — see DEPLOY.md, step 5.)*
"""
open(os.path.join(SITE, 'instructor.qmd'), 'w').write(instructor)

# ---------------- theme ----------------
scss = """/*-- scss:defaults --*/
@import url('https://fonts.googleapis.com/css2?family=STIX+Two+Text:ital,wght@0,400;0,600;0,700;1,400&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

// DCT palette — dark green, brass, ivory
$pine-950: #041F17;
$pine-900: #05291F;
$pine-800: #0B3D2E;
$pine-700: #14523F;
$moss-600: #1B6B52;
$brass:    #C8A24B;
$brass-soft: #D9BE7A;
$paper:    #F7F4EC;
$ink:      #17231F;
$graph:    #7FC8A9;

$primary: $pine-800;
$link-color: $pine-700;
$navbar-bg: $pine-900;
$navbar-fg: #EFEAD9;
$footer-bg: $pine-950;
$footer-fg: #CFE3D8;
$body-bg: $paper;
$body-color: $ink;
$headings-color: $pine-900;
$font-family-sans-serif: "Source Sans 3", system-ui, sans-serif;
$headings-font-family: "STIX Two Text", Georgia, serif;
$font-size-root: 17px;
"""
open(os.path.join(SITE, 'styles', 'theme.scss'), 'w').write(scss)

scss_dark = """/*-- scss:defaults --*/
@import url('https://fonts.googleapis.com/css2?family=STIX+Two+Text:ital,wght@0,400;0,600;0,700&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
$pine-950:#041F17; $pine-900:#05291F; $pine-800:#0B3D2E; $brass:#C8A24B; $brass-soft:#D9BE7A; $ivory:#EDE9DC;
$body-bg:$pine-950; $body-color:$ivory; $link-color:#8FD4B4; $navbar-bg:$pine-900; $navbar-fg:$ivory;
$headings-color:$brass-soft; $primary:$pine-800;
$font-family-sans-serif:"Source Sans 3",system-ui,sans-serif; $headings-font-family:"STIX Two Text",Georgia,serif;
"""
open(os.path.join(SITE, 'styles', 'theme-dark.scss'), 'w').write(scss_dark)

DARK_OVERRIDES = '''
/* ---------- dark mode overrides (body.quarto-dark) ---------- */
body.quarto-dark { --dct-card-bg: rgba(255,255,255,.045); }
body.quarto-dark .dct-hero { background: radial-gradient(120% 140% at 85% 15%, #14523F 0%, #05291F 45%, #021410 100%); border: 1px solid rgba(200,162,75,.3); }
body.quarto-dark .stat-strip { border-color: rgba(200,162,75,.35); }
body.quarto-dark .stat-strip .stat + .stat { border-left-color: rgba(200,162,75,.2); }
body.quarto-dark .stat-strip .n { color: #D9BE7A; }
body.quarto-dark .stat-strip .l { color: rgba(237,233,220,.6); }
body.quarto-dark .vol-arc .vol { background: var(--dct-card-bg); border-color: rgba(200,162,75,.25); }
body.quarto-dark .vol-arc .vol h3, body.quarto-dark .vol-arc .vol p { color: #EDE9DC; }
body.quarto-dark .ch-card { background: var(--dct-card-bg); border-color: rgba(200,162,75,.25); color: #EDE9DC; }
body.quarto-dark .ch-card:hover { background: rgba(255,255,255,.08); border-color: #C8A24B; box-shadow: none; }
body.quarto-dark .ch-card .num { color: #D9BE7A; }
body.quarto-dark .ch-card .t { color: #EDE9DC; }
body.quarto-dark .ch-card .meta { color: rgba(237,233,220,.55); }
body.quarto-dark .sched td, body.quarto-dark .sched th { border-bottom-color: rgba(200,162,75,.25); }
body.quarto-dark .sched th, body.quarto-dark .sched .theme { color: rgba(237,233,220,.7); }
body.quarto-dark .sched .wkb { color: #D9BE7A; }
body.quarto-dark .chapter-meta { background: rgba(255,255,255,.05); border-color: rgba(200,162,75,.3); border-left-color: #C8A24B; }
body.quarto-dark ol.los-list > li { border-bottom-color: rgba(200,162,75,.3); }
body.quarto-dark h4.ex-part { color: #8FD4B4; border-bottom-color: rgba(200,162,75,.3); }
body.quarto-dark h2::after { background: #C8A24B; }
body.quarto-dark .stat-strip .stat { color: #EDE9DC; }
'''

css_custom = """/* ---------- global type ---------- */
h1, h2, h3, h4 { font-family: "STIX Two Text", Georgia, serif; letter-spacing: 0; }
h1 { font-weight: 700; }
h2 { font-weight: 600; border-bottom: none; position: relative; padding-bottom: .4rem; margin-top: 2.2rem; }
h2::after { content: ""; position: absolute; left: 0; bottom: 0; width: 3.5rem; height: 2px; background: #C8A24B; }
.mono, .eyebrow { font-family: "IBM Plex Mono", monospace; }
.eyebrow { font-size: .72rem; letter-spacing: .18em; text-transform: uppercase; color: #C8A24B; font-weight: 500; }

.navbar { border-bottom: 2px solid #C8A24B; }
.navbar-brand { font-family: "STIX Two Text", serif; font-weight: 700; font-size: 1.15rem; }
/* ---------- hero with trajectory ---------- */
.dct-hero {
  position: relative; overflow: hidden;
  background: radial-gradient(120% 140% at 85% 15%, #14523F 0%, #0B3D2E 38%, #041F17 100%);
  color: #EFEAD9; border-radius: 14px; margin: 1.1rem 0 1.6rem;
  padding: 3.2rem 2.6rem 2.8rem;
}
.dct-hero .hero-svg { position: absolute; right: -40px; top: 50%; transform: translateY(-50%);
  width: 560px; max-width: 62%; opacity: .9; pointer-events: none; }
.dct-hero .hero-copy { position: relative; max-width: 34rem; z-index: 2; }
.dct-hero h1 { font-size: clamp(1.9rem, 4vw, 2.9rem); color: #F5F0E1; line-height: 1.12; margin: .5rem 0 1rem; }
.dct-hero h1 em { color: #D9BE7A; font-style: italic; }
.dct-hero p { font-size: 1.02rem; color: #D8E4DD; }
.dct-hero strong { color: #D9BE7A; }
@media (max-width: 900px) { .dct-hero .hero-svg { position: static; transform: none; width: 100%; max-width: 100%; margin-top: 1.2rem; opacity: .85; } }
/* trajectory draw-on animation */
.traj-path { stroke-dasharray: 1400; stroke-dashoffset: 1400; animation: traj-draw 2.4s ease-out .3s forwards; }
@keyframes traj-draw { to { stroke-dashoffset: 0; } }
@media (prefers-reduced-motion: reduce) { .traj-path { animation: none; stroke-dashoffset: 0; } }

.btn-hero, .btn-hero-outline {
  display: inline-block; margin-top: 1.2rem; margin-right: .7rem; padding: .6rem 1.25rem;
  border-radius: 8px; font-weight: 600; text-decoration: none; font-size: .95rem;
  transition: transform .12s ease, box-shadow .12s ease;
}
.btn-hero { background: #C8A24B; color: #041F17 !important; }
.btn-hero:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0,0,0,.35); }
.btn-hero-outline { border: 1.5px solid rgba(239,234,217,.7); color: #EFEAD9 !important; }
.btn-hero-outline:hover { border-color: #C8A24B; color: #D9BE7A !important; }
/* ---------- stat strip ---------- */
.stat-strip { display: flex; flex-wrap: wrap; gap: 0; border-top: 1px solid rgba(11,61,46,.25);
  border-bottom: 1px solid rgba(11,61,46,.25); margin: 1.6rem 0 2rem; }
.stat-strip .stat { flex: 1 1 110px; text-align: center; padding: .9rem .4rem; }
.stat-strip .stat + .stat { border-left: 1px solid rgba(11,61,46,.15); }
.stat-strip .n { font-family: "STIX Two Text", serif; font-size: 1.7rem; font-weight: 700; color: #0B3D2E; display: block; line-height: 1; }
.stat-strip .l { font-family: "IBM Plex Mono", monospace; font-size: .66rem; letter-spacing: .14em; text-transform: uppercase; color: rgba(23,35,31,.65); }
/* ---------- the two-volume arc ---------- */
.vol-arc { display: grid; grid-template-columns: 1fr auto 1fr; align-items: stretch; gap: .9rem; margin: 1.4rem 0 2rem; }
.vol-arc .vol { background: white; border: 1px solid rgba(11,61,46,.18); border-top: 4px solid #0B3D2E;
  border-radius: 10px; padding: 1.1rem 1.2rem; }
.vol-arc .vol.solve { border-top-color: #C8A24B; }
.vol-arc .vol h3 { margin: .2rem 0 .3rem; font-size: 1.12rem; }
.vol-arc .vol p { margin: 0; font-size: .92rem; color: rgba(23,35,31,.8); }
.vol-arc .arc-arrow { align-self: center; font-family: "STIX Two Text", serif; font-size: 1.6rem; color: #C8A24B; }
@media (max-width: 700px) { .vol-arc { grid-template-columns: 1fr; } .vol-arc .arc-arrow { transform: rotate(90deg); justify-self: center; } }
/* ---------- chapter cards ---------- */
.part-band { margin: 2rem 0 .8rem; }
.part-band .eyebrow { display: block; margin-bottom: .1rem; }
.part-band h3 { margin: 0; font-size: 1.25rem; }
.ch-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: .8rem; }
.ch-card { display: block; background: white; border: 1px solid rgba(11,61,46,.16); border-radius: 10px;
  padding: .9rem 1rem .8rem; text-decoration: none; color: #17231F; position: relative;
  transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease; }
.ch-card:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(4,31,23,.12); border-color: #C8A24B; color: #17231F; }
.ch-card .num { font-family: "STIX Two Text", serif; font-weight: 700; font-size: 1.5rem; color: #0B3D2E; line-height: 1; }
.ch-card .t { font-family: "STIX Two Text", serif; font-weight: 600; font-size: .98rem; line-height: 1.25; margin: .3rem 0 .5rem; color: #05291F; }
.ch-card .meta { font-family: "IBM Plex Mono", monospace; font-size: .66rem; letter-spacing: .04em; color: rgba(23,35,31,.62); }
.ch-card .wk { position: absolute; top: .7rem; right: .8rem; font-family: "IBM Plex Mono", monospace;
  font-size: .62rem; letter-spacing: .08em; color: #C8A24B; border: 1px solid #D9BE7A; border-radius: 999px; padding: .1rem .5rem; }
/* ---------- schedule ---------- */
.sched { width: 100%; border-collapse: collapse; margin-top: 1rem; }
.sched td, .sched th { padding: .7rem .8rem; border-bottom: 1px solid rgba(11,61,46,.14); vertical-align: top; }
.sched th { font-family: "IBM Plex Mono", monospace; font-size: .68rem; letter-spacing: .14em; text-transform: uppercase; color: rgba(23,35,31,.6); text-align: left; }
.sched .wkb { display: inline-block; min-width: 2.1rem; text-align: center; font-family: "STIX Two Text", serif;
  font-weight: 700; font-size: 1.05rem; color: #05291F; border: 2px solid #C8A24B; border-radius: 999px; padding: .15rem .35rem; }
.sched .theme { color: rgba(23,35,31,.78); font-size: .93rem; }
.sched tr.boundary td { border-bottom: 3px double #C8A24B; }
.milestone { font-family: "IBM Plex Mono", monospace; font-size: .66rem; letter-spacing: .12em; text-transform: uppercase; color: #C8A24B; }
/* ---------- chapter pages ---------- */
.chapter-meta { background: white; border: 1px solid rgba(11,61,46,.16); border-left: 4px solid #C8A24B;
  padding: .7rem 1rem; border-radius: 8px; margin-bottom: 1.2rem; font-size: .92rem; }
.chapter-meta code { font-family: "IBM Plex Mono", monospace; background: rgba(200,162,75,.14); color: #0B3D2E; }
.quarto-title-block .quarto-title .subtitle { font-family: "IBM Plex Mono", monospace; font-size: .8rem; letter-spacing: .1em; text-transform: uppercase; color: #1B6B52; }

ol.los-list { counter-reset: los; list-style: none; padding-left: 0; }
ol.los-list > li { counter-increment: los; position: relative; padding: .45rem 0 .45rem 3.4rem; border-bottom: 1px dotted rgba(11,61,46,.2); }
ol.los-list > li::before { content: counter(los, decimal-leading-zero); position: absolute; left: 0; top: .45rem;
  font-family: "IBM Plex Mono", monospace; font-size: .78rem; color: #C8A24B; border: 1px solid #D9BE7A; border-radius: 6px; padding: .12rem .45rem; }

h4.ex-part { font-family: "IBM Plex Mono", monospace; font-size: .72rem; letter-spacing: .16em; text-transform: uppercase;
  color: #14523F; margin-top: 1.6rem; border-bottom: 1px solid rgba(11,61,46,.2); padding-bottom: .3rem; }

table { font-size: .93rem; }
.page-footer { font-size: .85rem; }
"""
open(os.path.join(SITE, 'styles', 'custom.css'), 'w').write(css_custom + DARK_OVERRIDES)



# ---------------- MathJax macros (the frozen DCT alphabet) ----------------
mathjax = """<script>
window.MathJax = {
  tex: {
    macros: {
      x: "\\\\mathbf{x}", uc: "\\\\mathbf{u}", Xc: "\\\\mathcal{X}", Uc: "\\\\mathcal{U}",
      AS: "\\\\mathcal{A}_{S}", AT: "\\\\mathcal{A}_{T}", AC: "\\\\mathcal{A}_{C}",
      AP: "\\\\mathcal{A}_{P}", AR: "\\\\mathcal{A}_{R}", UETA: "\\\\mathcal{U}_{E}",
      Cvec: "\\\\mathbf{C}", Pvec: "\\\\mathbf{P}", Rvec: "\\\\mathbf{R}",
      Top: "T", Iop: "I", feas: "\\\\Omega", Lag: "\\\\mathcal{L}",
      Pareto: "\\\\mathcal{P}", J: "J", E: "\\\\mathbb{E}", Prob: "\\\\mathbb{P}",
      R: "\\\\mathbb{R}", N: "\\\\mathbb{N}", F: "\\\\mathcal{F}",
      norm: ["\\\\lVert #1 \\\\rVert", 1], abs: ["\\\\lvert #1 \\\\rvert", 1],
      dd: "\\\\,\\\\mathrm{d}", Jac: "\\\\mathbf{J}_{f}", Pol: "\\\\Pi", pol: "\\\\pi"
    }
  }
};
</script>
"""
open(os.path.join(SITE, 'assets', 'mathjax-macros.html'), 'w').write(mathjax)

# ---------------- _quarto.yml ----------------
def sidebar_entries(vol):
    return '\n'.join(
        f'          - chapters/{slug(vol, c["ch"])}.qmd' for c in CH if c['vol'] == vol)

qyml = f"""project:
  type: website
  output-dir: _site
  render:
    - "*.qmd"
    - "chapters/*.qmd"
    - "!downloads/"
  resources:
    - "downloads/"

website:
  title: "Dynamic Corporate Transformation"
  description: "Graduate course companion to the two-volume DCT series"
  navbar:
    background: primary
    search: true
    left:
      - href: index.qmd
        text: Home
      - href: syllabus.qmd
        text: Syllabus
      - href: schedule.qmd
        text: Schedule
      - href: axiom.qmd
        text: AXIOM Lab
      - href: labs.qmd
        text: Labs & Downloads
      - href: instructor.qmd
        text: Instructors
  sidebar:
    - title: "Chapters"
      style: docked
      collapse-level: 1
      contents:
        - section: "Volume I — Foundations"
          contents:
{sidebar_entries(1)}
        - section: "Volume II — Enterprise Optimization"
          contents:
{sidebar_entries(2)}
  page-footer:
    center: "© 2026 Samir Asaf · *Dynamic Corporate Transformation* · All rights reserved"

format:
  html:
    theme:
      light: [flatly, styles/theme.scss]
      dark: [darkly, styles/theme-dark.scss]
    css:
      - styles/custom.css
    toc: true
    include-in-header: assets/mathjax-macros.html
    html-math-method: mathjax
"""
open(os.path.join(SITE, '_quarto.yml'), 'w').write(qyml)

print("Site generated:", SITE)
print("qmd pages:", sum(len(files) for _,_,files in os.walk(SITE) if True))
