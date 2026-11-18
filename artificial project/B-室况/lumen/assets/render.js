(function (root) {
  const NS = "http://www.w3.org/2000/svg";
  function el(name, attrs, parent) {
    const n = document.createElementNS(NS, name);
    if (attrs) for (const k in attrs) if (attrs[k] != null) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function clear(svg) { while (svg.firstChild) svg.removeChild(svg.firstChild); }
  function fmtClock(iso, withSec) {
    if (typeof iso === "string") {
      const m = iso.match(/T(\d{2}:\d{2}:\d{2})/);
      return withSec === false ? m[1].slice(0, 5) : m[1];
    }
    return iso;
  }
  function num(v, d) {
    d = (d == null ? 1 : d);
    return (Math.round(v * 10 ** d) / 10 ** d).toFixed(d);
  }

  function inBand(kind, v, C) {
    if (kind === "t") return v >= C.t_band[0] && v <= C.t_band[1];
    if (kind === "rh") return v >= C.rh_band[0] && v <= C.rh_band[1];
    if (kind === "lux") return v >= C.lux_mark;
    return true;
  }

  function drawTape(svg, opts) {
    const w = opts.w, h = opts.h, sc = opts.scale || 1;
    const pad = { l: Math.round(56 + 10 * (sc - 1)), r: Math.round(12 * sc), t: Math.round(8 * sc), b: Math.round(20 + 6 * sc) };
    const plotW = w - pad.l - pad.r;
    const times = opts.times, n = times.length, C = opts.comfort;
    const lanes = opts.lanes;
    const laneGap = 6 * sc;
    const plotH = h - pad.t - pad.b;
    const laneH = (plotH - laneGap * (lanes.length - 1)) / lanes.length;
    const x = (i) => pad.l + (i / (n - 1)) * plotW;

    clear(svg);
    svg.setAttribute("viewBox", "0 0 " + w + " " + h);

    lanes.forEach((lane, li) => {
      const y0 = pad.t + li * (laneH + laneGap);
      el("text", {
        x: pad.l - 8, y: y0 + laneH * 0.55,
        fill: "#8a8276", "font-size": 8 * sc,
        "font-family": "IBM Plex Sans, Noto Serif SC, sans-serif",
        "text-anchor": "end", "dominant-baseline": "middle"
      }, svg).textContent = lane.label;

      // status cells as a continuous run of in/out
      const ys = lane.series;
      let i = 0;
      while (i < n) {
        const ok = inBand(lane.kind, ys[i], C);
        let j = i + 1;
        while (j < n && inBand(lane.kind, ys[j], C) === ok) j++;
        const x1 = x(i), x2 = x(Math.min(n - 1, j));
        el("rect", {
          x: x1, y: y0, width: Math.max(0.8, x2 - x1), height: laneH * 0.55,
          fill: ok ? "rgba(138,160,122,0.55)" : "rgba(208,106,50,0.55)"
        }, svg);
        i = j;
      }

      if (lane.spark) {
        const vmin = Math.min.apply(null, ys), vmax = Math.max.apply(null, ys);
        const span = (vmax - vmin) || 1;
        const mid = y0 + laneH * 0.28;
        const amp = laneH * 0.42;
        let d = "";
        ys.forEach((v, i) => {
          const yy = mid - ((v - vmin) / span - 0.5) * 2 * amp;
          d += (i ? "L" : "M") + x(i).toFixed(1) + "," + yy.toFixed(1);
        });
        el("path", { d: d, fill: "none", stroke: "#efe6d6", "stroke-width": 1.1 * sc, "stroke-linejoin": "round", "stroke-opacity": 0.85 }, svg);
      }
    });

    // time ticks every 5 min = 30 samples
    for (let i = 0; i < n; i += 30) {
      const xx = x(i);
      el("line", { x1: xx, x2: xx, y1: pad.t, y2: pad.t + plotH, stroke: "rgba(236,230,220,0.06)" }, svg);
      const anchor = i === 0 ? "start" : (i >= n - 1 ? "end" : "middle");
      el("text", {
        x: xx, y: h - 5,
        fill: "#8a8276", "font-size": 9 * sc,
        "font-family": "IBM Plex Sans, sans-serif", "text-anchor": anchor
      }, svg).textContent = fmtClock(times[i], false);
    }

    if (opts.cursor != null) {
      const i = opts.cursor;
      const xx = x(i);
      el("line", { x1: xx, x2: xx, y1: pad.t, y2: pad.t + plotH, stroke: "#d06a32", "stroke-width": Math.max(1, sc), "stroke-opacity": 0.9 }, svg);
    }

    return {
      invX(px) {
        const u = (px - pad.l) / plotW;
        const i = Math.round(u * (n - 1));
        return Math.max(0, Math.min(n - 1, i));
      }
    };
  }

  root.LumenB = { el, clear, fmtClock, num, inBand, drawTape };
})(window);
