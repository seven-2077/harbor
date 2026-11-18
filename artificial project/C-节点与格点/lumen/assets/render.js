(function (root) {
  const NS = "http://www.w3.org/2000/svg";
  function el(name, attrs, parent) {
    const n = document.createElementNS(NS, name);
    if (attrs) for (const k in attrs) if (attrs[k] != null) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function clear(svg) { while (svg.firstChild) svg.removeChild(svg.firstChild); }

  function fmtClock(isoOrSec, withSec) {
    // iso like 2026-08-03T12:00:10+08:00
    if (typeof isoOrSec === "string") {
      const m = isoOrSec.match(/T(\d{2}:\d{2}:\d{2})/);
      return withSec === false ? m[1].slice(0, 5) : m[1];
    }
    return isoOrSec;
  }
  function num(v, d) { d = (d == null ? 1 : d); return (Math.round(v * 10 ** d) / 10 ** d).toFixed(d); }

  function drawChannel(svg, opts) {
    const w = opts.w, h = opts.h;
    const sc = opts.scale || 1;
    const pad = { l: Math.round(60 + 8 * (sc - 1)), r: Math.round(14 * sc), t: Math.round(18 + 8 * sc), b: Math.round(18 + 8 * sc) };
    const plotW = w - pad.l - pad.r, plotH = h - pad.t - pad.b;
    const ys = opts.series;
    let yMin = opts.yMin, yMax = opts.yMax;
    if (yMin == null || yMax == null) {
      yMin = Math.min.apply(null, ys);
      yMax = Math.max.apply(null, ys);
    }
    if (opts.ref != null) { yMin = Math.min(yMin, opts.ref); yMax = Math.max(yMax, opts.ref); }
    // Comfort bands are design marks. Do not expand the axis to the full band
    // (e.g. 20–26 °C would flatten a 0.8 °C indoor span). Draw only the intersection.
    const padY = (yMax - yMin) * 0.18 || 1;
    yMin -= padY; yMax += padY;
    const x = (i) => pad.l + (i / (ys.length - 1)) * plotW;
    const y = (v) => pad.t + (1 - (v - yMin) / (yMax - yMin)) * plotH;

    clear(svg);
    svg.setAttribute("viewBox", "0 0 " + w + " " + h);
    // band (clip to plot; axis is not expanded to the full band)
    if (opts.band) {
      const top = pad.t, bot = pad.t + plotH;
      const y0 = Math.min(Math.max(y(opts.band[1]), top), bot);
      const y1 = Math.min(Math.max(y(opts.band[0]), top), bot);
      if (Math.abs(y1 - y0) > 0.5) {
        el("rect", { x: pad.l, y: Math.min(y0, y1), width: plotW, height: Math.abs(y1 - y0), fill: "rgba(142,174,138,0.10)" }, svg);
      }
    }
    // grid
    const ticks = 4;
    for (let i = 0; i <= ticks; i++) {
      const v = yMin + (i / ticks) * (yMax - yMin);
      const yy = y(v);
      el("line", { x1: pad.l, x2: pad.l + plotW, y1: yy, y2: yy, stroke: "rgba(215,220,225,0.06)" }, svg);
      el("text", { x: pad.l - 6, y: yy, fill: "#7a848c", "font-size": 9 * sc, "font-family": "IBM Plex Sans, sans-serif", "text-anchor": "end", "dominant-baseline": "middle" }, svg).textContent = num(v, opts.digits == null ? 1 : opts.digits);
    }
    // x ticks every 5 min = 30 samples
    for (let i = 0; i < ys.length; i += 30) {
      const xx = x(i);
      el("line", { x1: xx, x2: xx, y1: pad.t, y2: pad.t + plotH, stroke: "rgba(215,220,225,0.05)" }, svg);
      const anchor = i === 0 ? "start" : (i >= ys.length - 1 ? "end" : "middle");
      el("text", { x: xx, y: h - 6 * sc, fill: "#7a848c", "font-size": 9 * sc, "font-family": "IBM Plex Sans, sans-serif", "text-anchor": anchor }, svg).textContent = fmtClock(opts.times[i], false);
    }

    // title
    el("text", { x: pad.l, y: 8 + 8 * sc, fill: opts.color, "font-size": 10 * sc, "font-family": "IBM Plex Sans, sans-serif", "letter-spacing": "0.12em" }, svg).textContent = opts.title;

    // band label
    if (opts.band && opts.bandLabel) {
      el("text", { x: pad.l + 4, y: y(opts.band[1]) - 3 * sc, fill: "#8eae8a", "font-size": 8 * sc, "font-family": "IBM Plex Sans, Noto Serif SC, sans-serif", "text-anchor": "start" }, svg).textContent = opts.bandLabel;
    }

    // outdoor ref line (hour value, not a series)
    if (opts.ref != null) {
      const yy = y(opts.ref);
      el("line", { x1: pad.l, x2: pad.l + plotW, y1: yy, y2: yy, stroke: "#6a8aa8", "stroke-width": Math.max(1, sc), "stroke-dasharray": (3 * sc) + " " + (3 * sc) }, svg);
      el("text", { x: pad.l + plotW - 2, y: yy + 10 * sc, fill: "#6a8aa8", "font-size": 8 * sc, "font-family": "IBM Plex Sans, Noto Serif SC, sans-serif", "text-anchor": "end" }, svg).textContent = opts.refLabel || ("室外整点  " + num(opts.ref, opts.digits == null ? 1 : opts.digits));
    }

    // series
    let d = "";
    ys.forEach((v, i) => { d += (i ? "L" : "M") + x(i).toFixed(2) + "," + y(v).toFixed(2); });
    el("path", { d: d, fill: "none", stroke: opts.color, "stroke-width": 1.35 * sc, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);

    // cursor
    if (opts.cursor != null) {
      const i = opts.cursor;
      const xx = x(i), yy = y(ys[i]);
      el("line", { x1: xx, x2: xx, y1: pad.t, y2: pad.t + plotH, stroke: "#c45a3a", "stroke-width": Math.max(1, sc), "stroke-opacity": 0.85 }, svg);
      el("circle", { cx: xx, cy: yy, r: 2.6 * sc, fill: opts.color, stroke: "#0b0d0f", "stroke-width": 0.8 * sc }, svg);
    }

    return { x, y, pad, invX(px) {
      const u = (px - pad.l) / plotW;
      const i = Math.round(u * (ys.length - 1));
      return Math.max(0, Math.min(ys.length - 1, i));
    } };
  }

  function drawWeek(svg, hours, key, opts) {
    opts = opts || {};
    const w = opts.w, h = opts.h;
    const pad = { l: 36, r: 8, t: 14, b: 16 };
    const plotW = w - pad.l - pad.r, plotH = h - pad.t - pad.b;
    const ys = hours.map((d) => d[key]);
    let yMin = Math.min.apply(null, ys), yMax = Math.max.apply(null, ys);
    const mid = (yMax - yMin) * 0.12 || 1;
    yMin -= mid; yMax += mid;
    const x = (i) => pad.l + (i / (ys.length - 1)) * plotW;
    const y = (v) => pad.t + (1 - (v - yMin) / (yMax - yMin)) * plotH;
    clear(svg);
    svg.setAttribute("viewBox", "0 0 " + w + " " + h);
    let d = "";
    ys.forEach((v, i) => { d += (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1); });
    el("path", { d: d, fill: "none", stroke: opts.color || "#6a8aa8", "stroke-width": 1.1, "stroke-linejoin": "round" }, svg);
    // overlap marker 2026-08-03T12:00 is index 12
    const idx = hours.findIndex((d) => d.time === "2026-08-03T12:00");
    if (idx >= 0) {
      el("line", { x1: x(idx), x2: x(idx), y1: pad.t, y2: pad.t + plotH, stroke: "#c45a3a", "stroke-width": 1 }, svg);
      el("circle", { cx: x(idx), cy: y(ys[idx]), r: 2.2, fill: "#c45a3a" }, svg);
    }
    el("text", { x: pad.l, y: 10, fill: "#7a848c", "font-size": 8, "font-family": "IBM Plex Sans, Noto Serif SC, sans-serif" }, svg).textContent = opts.title || "";
    el("text", { x: pad.l - 4, y: pad.t + 4, fill: "#4e575e", "font-size": 8, "font-family": "IBM Plex Sans, sans-serif", "text-anchor": "end" }, svg).textContent = num(yMax, opts.digits || 0);
    el("text", { x: pad.l - 4, y: pad.t + plotH, fill: "#4e575e", "font-size": 8, "font-family": "IBM Plex Sans, sans-serif", "text-anchor": "end" }, svg).textContent = num(yMin, opts.digits || 0);
    // day ticks
    for (let i = 0; i < hours.length; i += 24) {
      const lab = "08-" + String(3 + Math.round(i / 24)).padStart(2, "0");
      const anc = i === 0 ? "start" : (i >= hours.length - 24 ? "end" : "middle");
      el("text", { x: x(i), y: h - 3, fill: "#4e575e", "font-size": 8, "font-family": "IBM Plex Sans, sans-serif", "text-anchor": anc }, svg).textContent = lab;
    }
  }

  function drawSpark(svg, ys, opts) {
    const w = opts.w, h = opts.h;
    const pad = { l: 6, r: 6, t: 8, b: 8 };
    const plotW = w - pad.l - pad.r, plotH = h - pad.t - pad.b;
    const yMin = Math.min.apply(null, ys), yMax = Math.max.apply(null, ys);
    const span = (yMax - yMin) || 1;
    const x = (i) => pad.l + (i / (ys.length - 1)) * plotW;
    const y = (v) => pad.t + (1 - (v - yMin) / span) * plotH;
    clear(svg);
    svg.setAttribute("viewBox", "0 0 " + w + " " + h);
    let d = "";
    ys.forEach((v, i) => { d += (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1); });
    el("path", { d: d, fill: "none", stroke: opts.color || "#8b9398", "stroke-width": 1.1, "stroke-linejoin": "round" }, svg);
    if (opts.cursor != null) {
      el("circle", { cx: x(opts.cursor), cy: y(ys[opts.cursor]), r: 2.2, fill: opts.color || "#8b9398" }, svg);
    }
  }

  root.LumenC = { el, clear, fmtClock, num, drawChannel, drawWeek, drawSpark };
})(window);
