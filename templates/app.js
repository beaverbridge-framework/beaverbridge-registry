/* Facet search over the embedded registry index. No network, no framework. */
(function () {
  "use strict";
  var DATA = JSON.parse(document.getElementById("data").textContent);
  var ENTRIES = DATA.entries, CL = DATA.class_labels;
  var INST = {};
  DATA.instances.forEach(function (i) { INST[i.id] = i; });
  var PAGE = 60, COLLAPSED = 10;
  var NONE = "(no class)", NOANCHOR = "(no anchor)";

  var NOCOORD = "(no coordinates)";
  var FACETS = [
    { key: "instance", label: "Instance", get: function (e) { return [e.instance]; },
      text: function (v) { return INST[v] ? INST[v].title : v; },
      sub: function (v) { return INST[v] ? INST[v].licence : ""; } },
    { key: "region", label: "Region", get: function (e) { return e.regions; }, text: function (v) { return v; } },
    { key: "class", label: "Class", get: function (e) { return e.classes.length ? e.classes : [NONE]; },
      text: function (v) { return v === NONE ? NONE : CL[v] || v; },
      sub: function (v) { return v === NONE ? "" : v.split(":")[0]; } },
    { key: "crm", label: "CIDOC CRM", get: function (e) { return e.crm.length ? e.crm : [NOANCHOR]; },
      text: function (v) { return v; } }
  ];

  ENTRIES.forEach(function (e) {
    e._model = e.kinds.length > 0 && e.kinds.indexOf("domain") < 0;  // classes of the data model only
    e._v = {};
    FACETS.forEach(function (f) { e._v[f.key] = f.get(e); });
    e._h = [e.label, e.description, e.id, e.classes.map(function (c) { return CL[c]; }).join(" "),
            e.part_of.map(function (p) { return p.label; }).join(" "), e.crm.join(" ")].join(" ").toLowerCase();
  });

  var state = { q: "", sel: {}, sort: "label", shown: PAGE, expanded: {}, model: false, view: "list" };
  FACETS.forEach(function (f) { state.sel[f.key] = []; });

  /* ---- URL hash <-> state ---- */
  function readHash() {
    try {
      var p = new URLSearchParams(location.hash.replace(/^#/, ""));
      state.q = p.get("q") || "";
      if (p.get("sort") === "id") state.sort = "id";
      state.model = p.get("model") === "1";
      state.view = p.get("view") === "map" ? "map" : "list";
      FACETS.forEach(function (f) { state.sel[f.key] = p.getAll(f.key); });
    } catch (err) { /* old browser: start empty */ }
  }
  function writeHash() {
    try {
      var p = new URLSearchParams();
      if (state.q) p.set("q", state.q);
      if (state.sort !== "label") p.set("sort", state.sort);
      if (state.model) p.set("model", "1");
      if (state.view === "map") p.set("view", "map");
      FACETS.forEach(function (f) { state.sel[f.key].forEach(function (v) { p.append(f.key, v); }); });
      var s = p.toString();
      history.replaceState(null, "", s ? "#" + s : location.pathname + location.search);
    } catch (err) { /* file:// in some browsers */ }
  }

  /* ---- matching ---- */
  function tokens() { return state.q.toLowerCase().split(/\s+/).filter(Boolean); }
  function matches(e, toks, skip) {
    if (!state.model && e._model) return false;
    for (var i = 0; i < toks.length; i++) if (e._h.indexOf(toks[i]) < 0) return false;
    for (var k = 0; k < FACETS.length; k++) {
      var key = FACETS[k].key, sel = state.sel[key];
      if (key === skip || !sel.length) continue;
      if (!e._v[key].some(function (v) { return sel.indexOf(v) >= 0; })) return false;
    }
    return true;
  }

  /* ---- DOM helpers (text only, never innerHTML) ---- */
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (a) {
      if (a === "text") n.textContent = attrs[a]; else n.setAttribute(a, attrs[a]);
    });
    (kids || []).forEach(function (k) { n.appendChild(typeof k === "string" ? document.createTextNode(k) : k); });
    return n;
  }
  function safeUrl(u) { return /^https?:\/\//i.test(u); }
  function link(href, text) {
    return safeUrl(href) ? el("a", { href: href, rel: "noopener", text: text }) : document.createTextNode(text);
  }
  function highlight(parent, text, toks) {
    if (!toks.length) { parent.appendChild(document.createTextNode(text)); return; }
    var low = text.toLowerCase(), mask = new Array(text.length + 1).join("0").split("");
    toks.forEach(function (t) {
      var at = low.indexOf(t);
      while (at >= 0) { for (var j = at; j < at + t.length; j++) mask[j] = "1"; at = low.indexOf(t, at + t.length); }
    });
    var i = 0;
    while (i < text.length) {
      var j = i; while (j < text.length && mask[j] === mask[i]) j++;
      var part = text.slice(i, j);
      parent.appendChild(mask[i] === "1" ? el("mark", { text: part }) : document.createTextNode(part));
      i = j;
    }
  }

  /* ---- facets ---- */
  function renderFacets() {
    var toks = tokens(), host = document.getElementById("facets");
    host.textContent = "";
    FACETS.forEach(function (f) {
      var counts = {}, all = {};
      ENTRIES.forEach(function (e) {
        var ok = matches(e, toks, f.key);
        e._v[f.key].forEach(function (v) { all[v] = true; if (ok) counts[v] = (counts[v] || 0) + 1; });
      });
      state.sel[f.key].forEach(function (v) { all[v] = true; });
      var vals = Object.keys(all).sort(function (a, b) {
        return (counts[b] || 0) - (counts[a] || 0) || f.text(a).localeCompare(f.text(b));
      });
      if (!vals.length) return;
      var open = state.expanded[f.key], shown = open ? vals : vals.slice(0, COLLAPSED);
      state.sel[f.key].forEach(function (v) { if (shown.indexOf(v) < 0) shown.push(v); });
      var ul = el("ul");
      shown.forEach(function (v) {
        var id = "f-" + f.key + "-" + v.replace(/[^A-Za-z0-9]/g, "_");
        var cb = el("input", { type: "checkbox", id: id });
        cb.checked = state.sel[f.key].indexOf(v) >= 0;
        cb.addEventListener("change", function () { toggle(f.key, v); });
        var lab = el("label", { "for": id }, [cb, el("span", { text: f.text(v) })]);
        if (f.sub && f.sub(v)) lab.appendChild(el("span", { "class": "sub", text: f.sub(v) }));
        lab.appendChild(el("span", { "class": "n", text: String(counts[v] || 0) }));
        ul.appendChild(el("li", counts[v] ? {} : { "class": "zero" }, [lab]));
      });
      var set = el("fieldset", { "class": "facet" }, [el("legend", { text: f.label }), ul]);
      if (vals.length > COLLAPSED) {
        var b = el("button", { type: "button", "class": "more", text: open ? "Show fewer" : "Show all " + vals.length });
        b.addEventListener("click", function () { state.expanded[f.key] = !open; renderFacets(); });
        set.appendChild(b);
      }
      host.appendChild(set);
    });
  }
  function toggle(key, v) {
    var s = state.sel[key], i = s.indexOf(v);
    if (i >= 0) s.splice(i, 1); else s.push(v);
    state.shown = PAGE; update();
  }

  /* ---- results ---- */
  function card(e, toks) {
    var h = el("h3"), a = el("a", { href: e.url, rel: "noopener" });
    highlight(a, e.label, toks);
    h.appendChild(a); h.appendChild(el("span", { "class": "badge", text: e.id }));
    var c = el("article", { "class": "card" }, [h]);
    if (e.description) { var p = el("p"); highlight(p, e.description, toks); c.appendChild(p); }
    var dl = el("dl");
    function row(name, node) { dl.appendChild(el("dt", { text: name })); dl.appendChild(el("dd", {}, [node])); }
    if (e.classes.length) {
      var box = el("span");
      e.classes.forEach(function (k) {
        var t = el("button", { type: "button", "class": "tag", "aria-pressed": state.sel["class"].indexOf(k) >= 0 ? "true" : "false", text: CL[k] || k });
        t.addEventListener("click", function () { toggle("class", k); });
        box.appendChild(t);
      });
      row("Class", box);
    }
    if (e.part_of.length) row("Part of", document.createTextNode(e.part_of.map(function (p) { return p.label; }).join(", ")));
    if (e.coordinates.length) row("Coordinates", document.createTextNode(e.coordinates.slice(0, 2).map(function (x) { return x[0] + ", " + x[1]; }).join(" | ")));
    if (e.wikidata.length) {
      var w = el("span");
      e.wikidata.forEach(function (q, i) { if (i) w.appendChild(document.createTextNode(", ")); w.appendChild(link("https://www.wikidata.org/entity/" + q, q)); });
      row("Wikidata", w);
    }
    if (e.matches.length) {
      var m = el("span");
      e.matches.slice(0, 3).forEach(function (u, i) { if (i) m.appendChild(document.createTextNode(" ")); m.appendChild(link(u, u.replace(/^https?:\/\//, "").slice(0, 60))); });
      if (e.matches.length > 3) m.appendChild(document.createTextNode(" +" + (e.matches.length - 3)));
      row("Match", m);
    }
    if (dl.childNodes.length) c.appendChild(dl);
    return c;
  }
  function renderResults(list) {
    var toks = tokens(), host = document.getElementById("results");
    host.textContent = "";
    if (!list.length) { host.appendChild(el("div", { "class": "empty", text: "No entry matches. Remove a filter or a search word." })); return; }
    list.slice(0, state.shown).forEach(function (e) { host.appendChild(card(e, toks)); });
    if (list.length > state.shown) {
      var b = el("button", { type: "button", "class": "primary", text: "Show " + Math.min(PAGE, list.length - state.shown) + " more" });
      b.addEventListener("click", function () { state.shown += PAGE; renderResults(list); });
      host.appendChild(b);
    }
  }

  /* ---- map: an SVG of the hits that have coordinates; no tiles, no server ---- */
  var SVGNS = "http://www.w3.org/2000/svg";
  function svg(tag, attrs) {
    var n = document.createElementNS(SVGNS, tag);
    Object.keys(attrs || {}).forEach(function (a) { n.setAttribute(a, attrs[a]); });
    return n;
  }
  function renderMap(list) {
    var host = document.getElementById("map");
    host.textContent = "";
    var pts = [];
    list.forEach(function (e) { e.coordinates.forEach(function (c) { pts.push({ e: e, lat: c[0], lon: c[1] }); }); });
    if (!pts.length) { host.appendChild(el("div", { "class": "empty", text: "None of the current hits has coordinates." })); return; }
    var minLat = 90, maxLat = -90, minLon = 180, maxLon = -180;
    pts.forEach(function (p) {
      minLat = Math.min(minLat, p.lat); maxLat = Math.max(maxLat, p.lat);
      minLon = Math.min(minLon, p.lon); maxLon = Math.max(maxLon, p.lon);
    });
    var padLat = Math.max((maxLat - minLat) * 0.1, 0.5), padLon = Math.max((maxLon - minLon) * 0.1, 0.5);
    minLat -= padLat; maxLat += padLat; minLon -= padLon; maxLon += padLon;
    var k = Math.cos(((minLat + maxLat) / 2) * Math.PI / 180);   // east-west squeeze at this latitude
    var W = 800, spanX = (maxLon - minLon) * k, spanY = maxLat - minLat;
    var H = Math.max(240, Math.min(560, Math.round(W * spanY / spanX)));
    function X(lon) { return ((lon - minLon) / (maxLon - minLon)) * W; }
    function Y(lat) { return H - ((lat - minLat) / (maxLat - minLat)) * H; }
    var root = svg("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "class": "mapsvg",
                            "aria-label": "Map of " + pts.length + " positions" });
    var step = [0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30].filter(function (s) { return (maxLon - minLon) / s <= 8; })[0] || 30;
    for (var lo = Math.ceil(minLon / step) * step; lo <= maxLon; lo += step) {
      root.appendChild(svg("line", { x1: X(lo), y1: 0, x2: X(lo), y2: H, "class": "grid" }));
      var t = svg("text", { x: X(lo) + 3, y: H - 4, "class": "gridlabel" }); t.textContent = (Math.round(lo * 100) / 100) + "°"; root.appendChild(t);
    }
    for (var la = Math.ceil(minLat / step) * step; la <= maxLat; la += step) {
      root.appendChild(svg("line", { x1: 0, y1: Y(la), x2: W, y2: Y(la), "class": "grid" }));
      var u = svg("text", { x: 3, y: Y(la) - 3, "class": "gridlabel" }); u.textContent = (Math.round(la * 100) / 100) + "°"; root.appendChild(u);
    }
    var order = DATA.instances.map(function (i) { return i.id; });
    pts.forEach(function (p) {
      var a = svg("a", { href: p.e.url, target: "_blank", rel: "noopener" });
      var c = svg("circle", { cx: X(p.lon).toFixed(1), cy: Y(p.lat).toFixed(1), r: 5, "class": "pt i" + (order.indexOf(p.e.instance) % 4) });
      var tt = svg("title"); tt.textContent = p.e.label + " (" + p.e.id + ")";
      c.appendChild(tt); a.appendChild(c); root.appendChild(a);
    });
    host.appendChild(root);
    var leg = el("p", { "class": "legend" });
    var seen = {};
    pts.forEach(function (p) { seen[p.e.instance] = true; });
    order.filter(function (i) { return seen[i]; }).forEach(function (i) {
      leg.appendChild(el("span", { "class": "key i" + (order.indexOf(i) % 4), text: "● " + (INST[i] ? INST[i].title : i) }));
    });
    leg.appendChild(el("span", { "class": "muted", text: pts.length + " positions from " + list.filter(function (e) { return e.coordinates.length; }).length + " hits; graticule only, no base map" }));
    host.appendChild(leg);
  }

  function update() {
    var toks = tokens();
    var list = ENTRIES.filter(function (e) { return matches(e, toks, null); });
    if (state.sort === "label") list.sort(function (a, b) { return a.label.localeCompare(b.label) || (a.id < b.id ? -1 : 1); });
    document.getElementById("count").textContent = "";
    var cnt = document.getElementById("count");
    cnt.appendChild(el("strong", { text: String(list.length) }));
    cnt.appendChild(document.createTextNode(" of " + ENTRIES.length + " entries"));
    var showMap = state.view === "map";
    document.getElementById("map").hidden = !showMap;
    document.getElementById("results").hidden = showMap;
    document.getElementById("view-list").setAttribute("aria-pressed", showMap ? "false" : "true");
    document.getElementById("view-map").setAttribute("aria-pressed", showMap ? "true" : "false");
    renderFacets();
    if (showMap) renderMap(list); else renderResults(list);
    writeHash();
  }

  /* ---- controls ---- */
  var q = document.getElementById("q"), sort = document.getElementById("sort");
  readHash(); q.value = state.q; sort.value = state.sort;
  var timer = null;
  q.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(function () { state.q = q.value.trim(); state.shown = PAGE; update(); }, 120);
  });
  var mdl = document.getElementById("model");
  mdl.checked = state.model;
  mdl.addEventListener("change", function () { state.model = mdl.checked; state.shown = PAGE; update(); });
  ["list", "map"].forEach(function (v) {
    document.getElementById("view-" + v).addEventListener("click", function () { state.view = v; update(); });
  });
  sort.addEventListener("change", function () { state.sort = sort.value; update(); });
  document.getElementById("clear").addEventListener("click", function () {
    state.q = ""; q.value = ""; state.model = false; mdl.checked = false; FACETS.forEach(function (f) { state.sel[f.key] = []; }); state.shown = PAGE; update();
  });
  window.addEventListener("hashchange", function () { readHash(); q.value = state.q; sort.value = state.sort; mdl.checked = state.model; update(); });

  update();
})();
