/* ---------------------------------------------------------------
   The DCT Map — renderer and interaction layer
   Dependency-free. Reads assets/dct-map/map.json, draws an SVG
   scene, and wires camera, tracing, guided tour and drawer.
   --------------------------------------------------------------- */

(function () {
  "use strict";

  var SVGNS = "http://www.w3.org/2000/svg";
  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function el(tag, attrs, text) {
    var n = document.createElementNS(SVGNS, tag);
    if (attrs) for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    return n;
  }
  function h(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }
  function stripTags(s) {
    return String(s || "").replace(/<br\s*\/?>/gi, "  ·  ").replace(/<[^>]+>/g, "")
      .replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">").replace(/\s+/g, " ").trim();
  }
  function plain(s) {
    return String(s || "")
      .replace(/[_^]\{([^}]*)\}/g, "$1")
      .replace(/([_^])(\S)/g, "$2");
  }
  function wrap(text, maxChars) {
    var words = String(text).split(/\s+/), lines = [], cur = "";
    for (var i = 0; i < words.length; i++) {
      var probe = cur ? cur + " " + words[i] : words[i];
      if (plain(probe).length > maxChars && cur) { lines.push(cur); cur = words[i]; }
      else { cur = probe; }
    }
    if (cur) lines.push(cur);
    return lines;
  }
  /* Renders _x, _{xyz}, ^x, ^{xyz} as real SVG sub/superscripts. */
  function notate(target, str, size) {
    var s = String(str), re = /([_^])(?:\{([^}]*)\}|(\S))/g, last = 0, m;
    while ((m = re.exec(s)) !== null) {
      if (m.index > last) target.appendChild(document.createTextNode(s.slice(last, m.index)));
      var shift = (m[1] === "_" ? 0.26 : -0.38) * size;
      var t = el("tspan", { "font-size": Math.round(size * 0.68) + "px", dy: shift });
      t.textContent = m[2] != null ? m[2] : m[3];
      target.appendChild(t);
      var back = el("tspan", { dy: -shift });
      back.textContent = "\u200b";
      target.appendChild(back);
      last = re.lastIndex;
    }
    if (last < s.length) target.appendChild(document.createTextNode(s.slice(last)));
    return target;
  }
  function notateHTML(str) {
    function tag(k, v) { return k === "_" ? "<sub>" + v + "</sub>" : "<sup>" + v + "</sup>"; }
    return String(str || "")
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/([_^])\{([^}]*)\}/g, function (_, k, v) { return tag(k, v); })
      .replace(/([_^])(\S)/g, function (_, k, v) { return tag(k, v); });
  }

  function boot(root) {
    var src = root.getAttribute("data-src") || "assets/dct-map/map.json";
    fetch(src, { cache: "no-cache" })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (data) { build(root, data); })
      .catch(function (err) {
        root.appendChild(h("p", "dctmap__error",
          "The map data could not be loaded (" + err.message +
          "). Serve the site over HTTP — quarto preview, or the published GitHub Pages URL — rather than opening the file directly."));
      });
  }

  function build(root, data) {
    var L = data.layout;
    var VB = L.viewBox;
    var vbW = VB[2], vbH = VB[3];

    /* ---------- index and layout ---------- */

    var nodes = data.nodes.slice();
    var byId = {};
    nodes.forEach(function (n) {
      byId[n.id] = n;
      n.feeds = n.feeds || [];
      n.prereqs = [];
      n.vol = /Vol\. II/.test(n.chapter || "") ? 2 : 1;
    });
    nodes.forEach(function (n) {
      n.feeds.forEach(function (t) { if (byId[t]) byId[t].prereqs.push(n.id); });
    });

    var mainCols = {};
    nodes.forEach(function (n) {
      if (n.rail) return;
      (mainCols[n.col] = mainCols[n.col] || []).push(n);
    });
    Object.keys(mainCols).forEach(function (c) {
      var list = mainCols[c].sort(function (a, b) { return a.order - b.order; });
      var total = list.reduce(function (s, n) { return s + (n.h || L.nodeH); }, 0) +
                  L.nodeGap * (list.length - 1);
      var y = L.flowCenterY - total / 2;
      list.forEach(function (n) {
        n.w = n.w || L.nodeW;
        n.h = n.h || L.nodeH;
        n.cx = L.colX0 + (n.col - 1) * L.colPitch;
        n.cy = y + n.h / 2;
        y += n.h + L.nodeGap;
      });
    });

    var rail = nodes.filter(function (n) { return n.rail; })
      .sort(function (a, b) { return a.order - b.order; });
    rail.forEach(function (n, i) {
      n.w = L.rail.w;
      n.h = L.rail.h;
      n.cx = L.rail.x0 + i * L.rail.pitch + n.w / 2;
      n.cy = L.rail.y + n.h / 2;
    });

    /* ---------- shell ---------- */

    root.classList.add("dctmap");

    var bar = h("div", "dctmap__bar");
    var frame = h("div", "dctmap__frame");
    var tip = h("div", "dctmap__tip");
    var drawer = h("aside", "dctmap__drawer");
    drawer.setAttribute("aria-live", "polite");

    var svg = el("svg", {
      "class": "dctmap__stage",
      viewBox: VB.join(" "),
      preserveAspectRatio: "xMidYMid meet",
      role: "application",
      "aria-label": "Interactive map of the Dynamic Corporate Transformation framework"
    });
    var scene = el("g", { "class": "dctmap__scene" });
    svg.appendChild(scene);
    frame.appendChild(svg);
    frame.appendChild(tip);
    frame.appendChild(drawer);

    root.appendChild(bar);
    root.appendChild(frame);

    var gEdges = el("g", { "class": "dctmap__edges" });
    var gNodes = el("g", { "class": "dctmap__nodes" });
    var gChrome = el("g", { "class": "dctmap__chrome" });
    scene.appendChild(gChrome);
    scene.appendChild(gEdges);
    scene.appendChild(gNodes);

    /* ---------- chrome: spine, band headers, rail band ---------- */

    var segGap = 10;
    var segW = (L.spine.w - segGap * (data.stages.length - 1)) / data.stages.length;
    var spineSegs = {};
    data.stages.forEach(function (st, i) {
      var x = L.spine.x0 + i * (segW + segGap);
      var g = el("g", { "class": "spine-seg", tabindex: "0", role: "button",
                        "aria-label": "Stage: " + st.verb + ". " + st.gloss });
      g.appendChild(el("rect", { "class": "spine-box", x: x, y: L.spine.y, width: segW, height: L.spine.h }));
      g.appendChild(el("text", { "class": "spine-verb", x: x + segW / 2, y: L.spine.y + L.spine.h / 2 + 10,
                                 "text-anchor": "middle" }, st.verb));
      gChrome.appendChild(g);
      if (i < data.stages.length - 1) {
        var ax = x + segW + segGap / 2;
        gChrome.appendChild(el("path", { "class": "spine-arrow",
          d: "M" + (ax - 4) + " " + (L.spine.y + L.spine.h / 2 - 5) + "l7 5l-7 5z" }));
      }
      spineSegs[st.id] = g;
      g.addEventListener("click", function () { toggleStage(st.id); });
      g.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleStage(st.id); }
      });
    });
    var glossText = el("text", { "class": "spine-gloss", x: L.spine.x0, y: L.spine.y + L.spine.h + 26 },
      "Seven moves, left to right: the order in which DCT is taught and the order in which it is used.");
    gChrome.appendChild(glossText);

    data.bands.forEach(function (b) {
      var cx = L.colX0 + (b.col - 1) * L.colPitch;
      var list = (mainCols[b.col] || []);
      if (!list.length) return;
      var half = L.nodeW / 2;
      wrap(b.title, 17).forEach(function (line, i) {
        gChrome.appendChild(el("text", { "class": "band-title", x: cx - half,
          y: L.bandLabelY + i * 32 }, line));
      });
      gChrome.appendChild(el("text", { "class": "band-where", x: cx - half, y: L.bandLabelY + 62 }, b.where));
      gChrome.appendChild(el("line", { "class": "band-rule",
        x1: cx - half, y1: L.bandLabelY + 80, x2: cx + half, y2: L.bandLabelY + 80 }));
    });

    var railTop = L.rail.y - 52;
    gChrome.appendChild(el("rect", { "class": "rail-band", x: 120, y: railTop,
      width: vbW - 240, height: 200, rx: 2 }));
    gChrome.appendChild(el("text", { "class": "rail-title", x: L.rail.x0, y: railTop + 38 },
      "Mathematical stack — what each object above is built out of"));
    wrap(data.railNote, 230).forEach(function (line, i) {
      gChrome.appendChild(el("text", { "class": "rail-note", x: L.rail.x0, y: L.rail.y + L.rail.h + 36 + i * 24 }, line));
    });

    /* ---------- edges ---------- */

    var edgeEls = [];
    nodes.forEach(function (s) {
      s.feeds.forEach(function (tid) {
        var t = byId[tid];
        if (!t) return;
        var cls = "edge";
        var d;
        if (s.rail && !t.rail) {
          cls += " is-rail";
          var sy = s.cy - s.h / 2, ty = t.cy + t.h / 2;
          d = "M" + s.cx + " " + sy + " C" + s.cx + " " + (sy - 150) + " " + t.cx + " " + (ty + 190) + " " + t.cx + " " + ty;
        } else if (s.rail && t.rail) {
          d = "M" + (s.cx + s.w / 2) + " " + s.cy + " L" + (t.cx - t.w / 2) + " " + t.cy;
        } else if (s.col === t.col) {
          var bx = Math.max(s.cx + s.w / 2, t.cx + t.w / 2) + 54;
          d = "M" + (s.cx + s.w / 2) + " " + s.cy + " C" + bx + " " + s.cy + " " + bx + " " + t.cy +
              " " + (t.cx + t.w / 2) + " " + t.cy;
        } else {
          var x1 = s.cx + s.w / 2, x2 = t.cx - t.w / 2, mid = (x2 - x1) * 0.48;
          d = "M" + x1 + " " + s.cy + " C" + (x1 + mid) + " " + s.cy + " " + (x2 - mid) + " " + t.cy +
              " " + x2 + " " + t.cy;
        }
        var p = el("path", { "class": cls, d: d });
        p.__from = s.id; p.__to = t.id;
        gEdges.appendChild(p);
        edgeEls.push(p);
      });
    });

    /* ---------- nodes ---------- */

    var nodeEls = {};
    nodes.forEach(function (n) {
      var hinge = !!(n.w && n.w !== L.nodeW && !n.rail);
      var g = el("g", {
        "class": "node" + (n.rail ? " is-rail" : "") + (hinge ? " is-hinge" : ""),
        tabindex: "0", role: "button",
        "aria-label": plain(n.label) + ". " + (n.chapter ? n.chapter + ". " : "") + (n.blurb || "")
      });
      g.appendChild(el("rect", { "class": "node-box", x: n.cx - n.w / 2, y: n.cy - n.h / 2,
        width: n.w, height: n.h, rx: 2 }));

      var inner = n.w - 28;
      var labelSize = hinge ? 30 : 24;
      var labelLines = wrap(n.label, Math.floor(inner / (labelSize * 0.50)));
      if (!hinge && labelLines.length > 3) labelLines = labelLines.slice(0, 3);
      var lh = hinge ? 34 : 28;

      var mathSize = hinge ? 19 : 20;
      var mathLines;
      if (n.svgMath) {
        mathLines = [];
        [].concat(n.svgMath).forEach(function (line) {
          mathLines = mathLines.concat(wrap(line, Math.floor(inner / (mathSize * 0.60))));
        });
        if (!hinge) mathLines = mathLines.slice(0, 1);
      } else {
        var mathTxt = n.mathHtml ? stripTags(n.mathHtml) : (n.sub || "");
        mathLines = mathTxt ? wrap(mathTxt, Math.floor(inner / (mathSize * 0.60))) : [];
        mathLines = mathLines.slice(0, hinge ? 7 : 1);
      }

      var mlh = mathSize + 5;
      var mathCls = (n.mathHtml || n.svgMath) ? "node-math" : "node-sub";
      var mathNSize = mathCls === "node-math" ? mathSize : 17;
      var chapTxt = n.chapter ? (n.chapter + (n.axiom ? "  ·  " + n.axiom : "")) : "";

      /* Label, notation and the zoom-revealed chapter line all go into one
         measured stack, so no two rows can ever be placed on top of one
         another. Measure, drop from the bottom until it fits, then place. */
      var rows = [];
      labelLines.forEach(function (line) {
        rows.push({ t: line, cls: "node-label", s: labelSize, lh: lh, gap: 0 });
      });
      mathLines.forEach(function (line, i) {
        rows.push({ t: line, cls: mathCls, s: mathNSize, lh: mlh, gap: i === 0 ? 10 : 0 });
      });
      if (chapTxt) rows.push({ t: chapTxt, cls: "node-detail", s: 15, lh: 18, gap: 5 });

      function stackH() {
        return rows.reduce(function (a, r) { return a + r.lh + r.gap; }, 0);
      }
      while (stackH() > n.h - 10 && rows.length > 1) rows.pop();

      var y = hinge ? (n.cy - n.h / 2 + 44) : (n.cy - stackH() / 2 + labelSize * 0.78);
      rows.forEach(function (r) {
        y += r.gap;
        g.appendChild(notate(el("text", { "class": r.cls, x: n.cx, y: y,
          "text-anchor": "middle" }), r.t, r.s));
        y += r.lh;
      });


      gNodes.appendChild(g);
      nodeEls[n.id] = g;

      g.addEventListener("mouseenter", function (e) { showTip(n, e); });
      g.addEventListener("mousemove", function (e) { moveTip(e); });
      g.addEventListener("mouseleave", hideTip);
      g.addEventListener("click", function (e) { e.stopPropagation(); select(n.id); });
      g.addEventListener("focus", function () { select(n.id, true); });
      g.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(n.id); }
      });
    });

    /* ---------- tooltip ---------- */

    function showTip(n, e) {
      tip.innerHTML = "";
      tip.appendChild(h("strong", null, n.label));
      tip.appendChild(document.createTextNode(
        (n.blurb || "").split(". ").slice(0, 1).join(". ").slice(0, 180) + "."));
      tip.classList.add("is-on");
      moveTip(e);
    }
    function moveTip(e) {
      var r = frame.getBoundingClientRect();
      var x = clamp(e.clientX - r.left + 14, 8, r.width - 340);
      var y = clamp(e.clientY - r.top + 14, 8, r.height - 90);
      tip.style.left = x + "px";
      tip.style.top = y + "px";
    }
    function hideTip() { tip.classList.remove("is-on"); }

    /* ---------- camera ---------- */

    var cam = { k: 1, x: 0, y: 0 };
    function apply() {
      scene.setAttribute("transform", "translate(" + cam.x + "," + cam.y + ") scale(" + cam.k + ")");
      root.classList.toggle("is-zoomed", cam.k > 1.2);
    }
    function easeTo(target, ms) {
      if (REDUCED) { cam = target; apply(); return; }
      var from = { k: cam.k, x: cam.x, y: cam.y }, t0 = performance.now(), dur = ms || 520;
      function step(now) {
        var p = clamp((now - t0) / dur, 0, 1);
        var e = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
        cam.k = from.k + (target.k - from.k) * e;
        cam.x = from.x + (target.x - from.x) * e;
        cam.y = from.y + (target.y - from.y) * e;
        apply();
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }
    function fitTo(box, pad) {
      pad = pad == null ? 60 : pad;
      var k = clamp(Math.min(vbW / (box.w + pad * 2), vbH / (box.h + pad * 2)), 0.55, 2.6);
      return { k: k, x: vbW / 2 - k * (box.x + box.w / 2), y: vbH / 2 - k * (box.y + box.h / 2) };
    }
    function boxOf(list) {
      var x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
      list.forEach(function (n) {
        x1 = Math.min(x1, n.cx - n.w / 2); x2 = Math.max(x2, n.cx + n.w / 2);
        y1 = Math.min(y1, n.cy - n.h / 2); y2 = Math.max(y2, n.cy + n.h / 2);
      });
      return { x: x1, y: y1, w: x2 - x1, h: y2 - y1 };
    }
    function toScene(e) {
      var m = svg.getScreenCTM().inverse();
      var p = svg.createSVGPoint();
      p.x = e.clientX; p.y = e.clientY;
      return p.matrixTransform(m);
    }

    svg.addEventListener("wheel", function (e) {
      e.preventDefault();
      var p = toScene(e);
      var k2 = clamp(cam.k * (e.deltaY < 0 ? 1.12 : 1 / 1.12), 0.55, 3.2);
      var r = k2 / cam.k;
      cam.x = p.x - (p.x - cam.x) * r;
      cam.y = p.y - (p.y - cam.y) * r;
      cam.k = k2;
      apply();
    }, { passive: false });

    var drag = null;
    svg.addEventListener("pointerdown", function (e) {
      if (e.target.closest && e.target.closest(".node, .spine-seg")) return;
      drag = { x: e.clientX, y: e.clientY, cx: cam.x, cy: cam.y, s: svg.getScreenCTM().a };
      svg.classList.add("is-dragging");
      svg.setPointerCapture(e.pointerId);
    });
    svg.addEventListener("pointermove", function (e) {
      if (!drag) return;
      cam.x = drag.cx + (e.clientX - drag.x) / drag.s;
      cam.y = drag.cy + (e.clientY - drag.y) / drag.s;
      apply();
    });
    svg.addEventListener("pointerup", function () { drag = null; svg.classList.remove("is-dragging"); });
    svg.addEventListener("pointercancel", function () { drag = null; svg.classList.remove("is-dragging"); });
    svg.addEventListener("click", function (e) {
      if (!(e.target.closest && e.target.closest(".node"))) clearSelection();
    });

    /* ---------- selection and tracing ---------- */

    var selected = null;

    function walk(startId, key) {
      var seen = {}, stack = byId[startId][key].slice();
      while (stack.length) {
        var id = stack.pop();
        if (seen[id]) continue;
        seen[id] = true;
        (byId[id] ? byId[id][key] : []).forEach(function (n) { if (!seen[n]) stack.push(n); });
      }
      return seen;
    }

    function paint() {
      var up = selected ? walk(selected, "prereqs") : {};
      var down = selected ? walk(selected, "feeds") : {};
      nodes.forEach(function (n) {
        var g = nodeEls[n.id], c = g.classList;
        c.toggle("is-selected", n.id === selected);
        c.toggle("is-up", !!up[n.id]);
        c.toggle("is-down", !!down[n.id]);
        var inStage = !activeStage || n.stage === activeStage || (n.rail && activeStage === "represent");
        var inVol = !volFilter || n.vol === volFilter;
        var visible = inStage && inVol && (!selected || n.id === selected || up[n.id] || down[n.id]);
        c.toggle("is-mute", !visible);
      });
      edgeEls.forEach(function (p) {
        var c = p.classList;
        var isUp = selected && (up[p.__from] || p.__from === selected) && (up[p.__to] || p.__to === selected);
        var isDown = selected && (down[p.__from] || p.__from === selected) && (down[p.__to] || p.__to === selected);
        c.toggle("is-up", !!isUp);
        c.toggle("is-down", !!isDown);
        var liveA = !nodeEls[p.__from].classList.contains("is-mute");
        var liveB = !nodeEls[p.__to].classList.contains("is-mute");
        c.toggle("is-mute", !(liveA && liveB));
      });
      Object.keys(spineSegs).forEach(function (id) {
        spineSegs[id].classList.toggle("is-active", id === activeStage);
      });
    }

    function select(id, quiet) {
      selected = id;
      paint();
      openDrawer(byId[id]);
      if (!quiet) history.replaceState(null, "", "#node=" + id);
    }
    function clearSelection() {
      selected = null;
      paint();
      closeDrawer();
      history.replaceState(null, "", location.pathname + location.search);
    }

    /* ---------- drawer ---------- */

    function openDrawer(n) {
      drawer.innerHTML = "";
      var head = h("div", "dctmap__drawer-head");
      var titleWrap = h("div");
      var t = h("h2", "dctmap__drawer-title");
      t.innerHTML = notateHTML(n.label);
      titleWrap.appendChild(t);
      var stage = (data.stages.filter(function (s) { return s.id === n.stage; })[0] || {}).verb;
      var meta = [n.chapter, n.axiom, stage].filter(Boolean).join("  ·  ");
      if (meta) titleWrap.appendChild(h("div", "dctmap__meta", meta));
      head.appendChild(titleWrap);
      var close = h("button", "dctmap__drawer-close", "×");
      close.setAttribute("aria-label", "Close panel");
      close.addEventListener("click", clearSelection);
      head.appendChild(close);
      drawer.appendChild(head);

      var body = h("div", "dctmap__drawer-body");
      if (n.mathHtml) {
        var m = h("div", "dctmap__math");
        m.innerHTML = n.mathHtml;
        body.appendChild(m);
      }
      if (n.blurb) body.appendChild(h("p", null, n.blurb));
      if (n.detail && n.detail.length) {
        var ul = h("ul");
        n.detail.forEach(function (d) { ul.appendChild(h("li", null, d)); });
        body.appendChild(ul);
      }
      if (n.depth === "outline") {
        body.appendChild(h("p", "dctmap__meta", "Outline entry — full commentary still to be written."));
      }

      if (n.prereqs.length) {
        body.appendChild(h("h3", null, "Depends on"));
        body.appendChild(chips(n.prereqs, "up"));
      }
      if (n.feeds.length) {
        body.appendChild(h("h3", null, "Feeds into"));
        body.appendChild(chips(n.feeds, "down"));
      }
      if (n.href) {
        body.appendChild(h("h3", null, "Read it"));
        var links = h("div", "dctmap__links");
        var a = h("a", null, n.chapter ? "Open " + n.chapter : "Open the chapter");
        a.href = n.href;
        links.appendChild(a);
        if (n.axiom) {
          var b = h("a", null, "Open " + n.axiom + " in AXIOM");
          b.href = "axiom.html";
          links.appendChild(b);
        }
        body.appendChild(links);
      }
      drawer.appendChild(body);
      drawer.classList.add("is-open");
    }
    function chips(ids, kind) {
      var box = h("div", "dctmap__chips");
      ids.forEach(function (id) {
        var n = byId[id];
        if (!n) return;
        var b = h("button", "dctmap__chip dctmap__chip--" + kind);
        b.innerHTML = notateHTML(n.label);
        b.addEventListener("click", function () {
          select(id);
          easeTo(fitTo(boxOf([n]), 300), 420);
        });
        box.appendChild(b);
      });
      return box;
    }
    function closeDrawer() { drawer.classList.remove("is-open"); }

    /* ---------- stage and volume filters ---------- */

    var activeStage = null, volFilter = null;

    function toggleStage(id) {
      activeStage = activeStage === id ? null : id;
      selected = null;
      closeDrawer();
      paint();
      var st = data.stages.filter(function (s) { return s.id === activeStage; })[0];
      glossText.textContent = st
        ? st.verb + " — " + st.gloss
        : "Seven moves, left to right: the order in which DCT is taught and the order in which it is used.";
      if (activeStage) {
        var list = nodes.filter(function (n) { return n.stage === activeStage; });
        if (list.length) easeTo(fitTo(boxOf(list), 120));
        history.replaceState(null, "", "#stage=" + activeStage);
      } else {
        easeTo({ k: 1, x: 0, y: 0 });
        history.replaceState(null, "", location.pathname + location.search);
      }
    }

    /* ---------- guided tour ---------- */

    var tour = null;
    function startTour() {
      stopTour();
      var i = 0;
      tourBtn.textContent = "Stop tour";
      tourBtn.classList.add("is-on");
      activeStage = null;
      (function next() {
        if (i >= data.stages.length) { stopTour(); easeTo({ k: 1, x: 0, y: 0 }); return; }
        activeStage = data.stages[i].id;
        var st = data.stages[i];
        glossText.textContent = st.verb + " — " + st.gloss;
        paint();
        var list = nodes.filter(function (n) { return n.stage === st.id; });
        if (list.length) easeTo(fitTo(boxOf(list), 120));
        i++;
        tour = setTimeout(next, REDUCED ? 1400 : 3600);
      })();
    }
    function stopTour() {
      if (tour) clearTimeout(tour);
      tour = null;
      tourBtn.textContent = "Play the seven moves";
      tourBtn.classList.remove("is-on");
    }

    /* ---------- control bar ---------- */

    var g1 = h("div", "dctmap__bar-group");
    var tourBtn = h("button", "dctmap__btn dctmap__btn--play", "Play the seven moves");
    tourBtn.addEventListener("click", function () { tour ? stopTour() : startTour(); });
    g1.appendChild(tourBtn);
    bar.appendChild(g1);

    var g2 = h("div", "dctmap__bar-group");
    [["Volume I", 1], ["Volume II", 2]].forEach(function (pair) {
      var b = h("button", "dctmap__btn", pair[0]);
      b.setAttribute("aria-pressed", "false");
      b.addEventListener("click", function () {
        volFilter = volFilter === pair[1] ? null : pair[1];
        Array.prototype.forEach.call(g2.children, function (c) { c.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", volFilter ? "true" : "false");
        paint();
        var list = nodes.filter(function (n) { return !volFilter || n.vol === volFilter; });
        easeTo(volFilter ? fitTo(boxOf(list), 100) : { k: 1, x: 0, y: 0 });
      });
      g2.appendChild(b);
    });
    bar.appendChild(g2);

    var g3 = h("div", "dctmap__bar-group");
    var mathBtn = h("button", "dctmap__btn", "Jump to the mathematical stack");
    mathBtn.addEventListener("click", function () { easeTo(fitTo(boxOf(rail), 90)); });
    g3.appendChild(mathBtn);
    var geopBtn = h("button", "dctmap__btn", "Jump to GEOP");
    geopBtn.addEventListener("click", function () { select("geop"); easeTo(fitTo(boxOf([byId.geop]), 260)); });
    g3.appendChild(geopBtn);
    bar.appendChild(g3);

    var g4 = h("div", "dctmap__bar-group");
    ["−", "+"].forEach(function (sym) {
      var b = h("button", "dctmap__btn", sym);
      b.setAttribute("aria-label", sym === "+" ? "Zoom in" : "Zoom out");
      b.addEventListener("click", function () {
        var k2 = clamp(cam.k * (sym === "+" ? 1.3 : 1 / 1.3), 0.55, 3.2), r = k2 / cam.k;
        easeTo({ k: k2, x: vbW / 2 - (vbW / 2 - cam.x) * r, y: vbH / 2 - (vbH / 2 - cam.y) * r }, 260);
      });
      g4.appendChild(b);
    });
    var resetBtn = h("button", "dctmap__btn", "Reset view");
    resetBtn.addEventListener("click", function () {
      stopTour(); volFilter = null; activeStage = null;
      Array.prototype.forEach.call(g2.children, function (c) { c.setAttribute("aria-pressed", "false"); });
      clearSelection();
      glossText.textContent = "Seven moves, left to right: the order in which DCT is taught and the order in which it is used.";
      easeTo({ k: 1, x: 0, y: 0 });
    });
    g4.appendChild(resetBtn);
    bar.appendChild(g4);

    bar.appendChild(h("span", "dctmap__hint", "Click a box to trace what it needs and what it feeds. Scroll to zoom, drag to pan."));

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { clearSelection(); stopTour(); }
    });

    /* ---------- legend ---------- */

    var legend = h("div", "dctmap__legend");
    data.legend.forEach(function (item) {
      var row = h("div");
      var d = h("dfn");
      d.innerHTML = notateHTML(item.sym);
      row.appendChild(d);
      row.appendChild(document.createTextNode(item.def));
      legend.appendChild(row);
    });
    root.appendChild(legend);

    /* ---------- mobile list ---------- */

    var list = h("div", "dctmap__list");
    data.bands.forEach(function (b) {
      var group = (mainCols[b.col] || []);
      if (!group.length) return;
      list.appendChild(h("h3", "dctmap__list-band", b.title));
      list.appendChild(h("div", "dctmap__list-where", b.where));
      group.forEach(function (n) { list.appendChild(listItem(n)); });
    });
    if (rail.length) {
      list.appendChild(h("h3", "dctmap__list-band", "Mathematical stack"));
      list.appendChild(h("div", "dctmap__list-where", "Prerequisites carried by every object above"));
      rail.forEach(function (n) { list.appendChild(listItem(n)); });
    }
    root.insertBefore(list, legend);

    function listItem(n) {
      var d = document.createElement("details");
      var s = document.createElement("summary");
      s.innerHTML = notateHTML(n.label);
      d.appendChild(s);
      var body = h("div", "dctmap__list-body");
      if (n.mathHtml) {
        var m = h("div", "dctmap__math");
        m.innerHTML = n.mathHtml;
        body.appendChild(m);
      }
      if (n.blurb) body.appendChild(h("p", null, n.blurb));
      if (n.detail) {
        var ul = h("ul");
        n.detail.forEach(function (x) { ul.appendChild(h("li", null, x)); });
        body.appendChild(ul);
      }
      if (n.href) {
        var links = h("div", "dctmap__links");
        var a = h("a", null, n.chapter ? "Open " + n.chapter : "Open the chapter");
        a.href = n.href;
        links.appendChild(a);
        body.appendChild(links);
      }
      d.appendChild(body);
      return d;
    }

    /* ---------- deep links ---------- */

    function fromHash() {
      var m = /#node=([\w-]+)/.exec(location.hash);
      if (m && byId[m[1]]) {
        select(m[1], true);
        easeTo(fitTo(boxOf([byId[m[1]]]), 320), 0);
        return;
      }
      var s = /#stage=([\w-]+)/.exec(location.hash);
      if (s && spineSegs[s[1]]) toggleStage(s[1]);
    }

    apply();
    paint();
    fromHash();
    window.addEventListener("hashchange", fromHash);
  }

  document.addEventListener("DOMContentLoaded", function () {
    Array.prototype.forEach.call(document.querySelectorAll("[data-dct-map]"), boot);
  });
})();
