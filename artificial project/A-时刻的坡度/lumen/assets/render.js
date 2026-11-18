/* Shared drawing helpers for the Marey specimen. No chart library. */
(function (root) {
  const NS = "http://www.w3.org/2000/svg";

  function el(name, attrs, parent) {
    const n = document.createElementNS(NS, name);
    if (attrs) {
      for (const k in attrs) {
        if (attrs[k] !== undefined && attrs[k] !== null) n.setAttribute(k, attrs[k]);
      }
    }
    if (parent) parent.appendChild(n);
    return n;
  }

  function fmtClock(sec, opt) {
    opt = opt || {};
    const sign = sec < 0 ? -1 : 1;
    sec = Math.round(Math.abs(sec));
    let h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    const pad = (n) => String(n).padStart(2, "0");
    if (opt.withSeconds) return (sign < 0 ? "-" : "") + pad(h) + ":" + pad(m) + ":" + pad(s);
    return (sign < 0 ? "-" : "") + pad(h) + ":" + pad(m);
  }

  function fmtSpan(sec) {
    const m = Math.round(sec / 60);
    if (m < 60) return m + " 分";
    const h = Math.floor(m / 60);
    return h + " 小时 " + (m % 60) + " 分";
  }

  function stationIndex(S) {
    const map = {};
    S.stations.forEach((st, i) => { map[st.id] = st; st._i = i; });
    return map;
  }

  function scales(S, box) {
    const t0 = 0;
    const t1 = 26 * 3600;
    const y0 = 0;
    const y1 = S.stations[S.stations.length - 1].chainage_m;
    return {
      t0, t1, y0, y1,
      pad: box.pad,
      w: box.w,
      h: box.h,
      plotW: box.w - box.pad.l - box.pad.r,
      plotH: box.h - box.pad.t - box.pad.b,
      x(sec) { return box.pad.l + ((sec - t0) / (t1 - t0)) * (box.w - box.pad.l - box.pad.r); },
      y(ch) { return box.pad.t + ((ch - y0) / (y1 - y0)) * (box.h - box.pad.t - box.pad.b); },
      invX(px) {
        const u = (px - box.pad.l) / (box.w - box.pad.l - box.pad.r);
        return t0 + u * (t1 - t0);
      }
    };
  }

  function tripPathD(trip, sc, byId) {
    const pts = [];
    trip.stops.forEach((st, i) => {
      const y = sc.y(byId[st.s].chainage_m);
      pts.push([sc.x(st.a), y]);
      if (st.d !== st.a) pts.push([sc.x(st.d), y]);
    });
    if (!pts.length) return "";
    let d = "M" + pts[0][0].toFixed(2) + "," + pts[0][1].toFixed(2);
    for (let i = 1; i < pts.length; i++) d += "L" + pts[i][0].toFixed(2) + "," + pts[i][1].toFixed(2);
    return d;
  }

  function positionAt(trip, t, byId) {
    const s = trip.stops;
    const tStart = Math.min(s[0].a, s[0].d);
    const tEnd = Math.max(s[s.length - 1].a, s[s.length - 1].d);
    if (t < tStart || t > tEnd) return null;
    for (let i = 0; i < s.length; i++) {
      const lo = Math.min(s[i].a, s[i].d);
      const hi = Math.max(s[i].a, s[i].d);
      if (t >= lo && t <= hi) {
        return { chainage: byId[s[i].s].chainage_m, dwelling: lo !== hi, station: s[i].s, trip };
      }
    }
    for (let i = 0; i < s.length - 1; i++) {
      const t0 = s[i].d, t1 = s[i + 1].a;
      if (t >= t0 && t <= t1) {
        const u = t1 === t0 ? 0 : (t - t0) / (t1 - t0);
        const c0 = byId[s[i].s].chainage_m, c1 = byId[s[i + 1].s].chainage_m;
        return { chainage: c0 + u * (c1 - c0), dwelling: false, from: s[i].s, to: s[i + 1].s, trip };
      }
    }
    return null;
  }

  function drawMarey(svg, S, sc, opts) {
    opts = opts || {};
    const byId = stationIndex(S);
    const river = S.meta.river_gap;
    const yE = sc.y(byId[river.east_station].chainage_m);
    const yW = sc.y(byId[river.west_station].chainage_m);
    const yTop = Math.min(yE, yW), yBot = Math.max(yE, yW);

    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", "0 0 " + sc.w + " " + sc.h);
    svg.setAttribute("preserveAspectRatio", "none");

    const gBg = el("g", { class: "bg" }, svg);

    // river band
    el("rect", {
      x: sc.pad.l, y: yTop,
      width: sc.plotW, height: yBot - yTop,
      fill: "rgba(90,110,112,0.13)"
    }, gBg);
    el("text", {
      x: sc.pad.l + 8, y: (yTop + yBot) / 2,
      fill: "#6e7878", "font-size": 9, "font-family": "IBM Plex Sans, sans-serif",
      "letter-spacing": "0.08em", "dominant-baseline": "middle"
    }, gBg).textContent = "东河区段（坐标示意）";

    // peak veils
    const peaks = [[6.5 * 3600, 9.5 * 3600], [16 * 3600, 19.5 * 3600]];
    peaks.forEach(([a, b]) => {
      el("rect", {
        x: sc.x(a), y: sc.pad.t,
        width: sc.x(b) - sc.x(a), height: sc.plotH,
        fill: "rgba(232,223,208,0.035)"
      }, gBg);
    });

    // hour grid
    const gGrid = el("g", { class: "grid" }, svg);
    const hourStep = sc.plotW < 980 ? 2 : 1;
    for (let h = 0; h <= 26; h++) {
      const x = sc.x(h * 3600);
      el("line", {
        x1: x, x2: x, y1: sc.pad.t, y2: sc.pad.t + sc.plotH,
        stroke: h % 6 === 0 ? "rgba(232,223,208,0.10)" : "rgba(232,223,208,0.045)",
        "stroke-width": 1
      }, gGrid);
      if (h % hourStep === 0) {
        el("text", {
          x: x, y: sc.pad.t + sc.plotH + 16,
          fill: "#7a7166", "font-size": 10, "font-family": "IBM Plex Sans, sans-serif",
          "text-anchor": "middle", "font-variant-numeric": "tabular-nums"
        }, gGrid).textContent = String(h).padStart(2, "0") + ":00";
      }
    }

    // station lines + labels
    const skip = S.meta.eastbound_local_skips.stations;
    S.stations.forEach((st) => {
      const y = sc.y(st.chainage_m);
      el("line", {
        x1: sc.pad.l - 4, x2: sc.pad.l + sc.plotW, y1: y, y2: y,
        stroke: "rgba(232,223,208,0.07)", "stroke-width": 1
      }, gGrid);
      const isTerm = st.id === "701" || st.id === "726";
      const label = st.name + (skip.indexOf(st.id) >= 0 ? "  †" : "");
      const txt = el("text", {
        x: sc.pad.l - 8, y: y,
        fill: isTerm ? "#e8dfd0" : (skip.indexOf(st.id) >= 0 ? "#c9a070" : "#9a9084"),
        "font-size": isTerm ? 11 : 10,
        "font-family": "IBM Plex Sans, sans-serif",
        "text-anchor": "end",
        "dominant-baseline": "middle",
        "data-station": st.id,
        cursor: "pointer"
      }, gGrid);
      txt.textContent = label;
    });

    // trips
    const gTrips = el("g", { class: "trips" }, svg);
    S.trips.forEach((trip) => {
      const west = trip.dir === 1;
      const express = trip.route === "7X";
      const d = tripPathD(trip, sc, byId);
      const col = west ? "#d19a4a" : "#a8b6b8";
      const p = el("path", {
        d: d,
        fill: "none",
        stroke: col,
        "stroke-width": express ? 1.25 : 0.7,
        "stroke-opacity": express ? 0.82 : 0.42,
        "stroke-linejoin": "round",
        "stroke-linecap": "round",
        "data-id": trip.id,
        class: "trip" + (express ? " express" : "") + (west ? " west" : " east")
      }, gTrips);
      // invisible hit area
      el("path", {
        d: d,
        fill: "none",
        stroke: "transparent",
        "stroke-width": 6,
        "data-id": trip.id,
        class: "hit",
        cursor: "pointer"
      }, gTrips);
    });

    // scrubber group (empty, filled by app)
    el("g", { class: "scrub" }, svg);
    el("g", { class: "hi" }, svg);

    return { byId };
  }

  function highlightTrip(svg, trip, sc, byId, S) {
    const g = svg.querySelector("g.hi");
    while (g.firstChild) g.removeChild(g.firstChild);
    if (!trip) return;
    const d = tripPathD(trip, sc, byId);
    const west = trip.dir === 1;
    el("path", {
      d: d, fill: "none",
      stroke: west ? "#f0c075" : "#d7e4e6",
      "stroke-width": 2,
      "stroke-linejoin": "round",
      "stroke-linecap": "round"
    }, g);
    trip.stops.forEach((st) => {
      const y = sc.y(byId[st.s].chainage_m);
      el("circle", {
        cx: sc.x(st.a), cy: y, r: 1.6,
        fill: west ? "#f0c075" : "#d7e4e6"
      }, g);
    });
  }

  function drawScrub(svg, t, sc, S, byId) {
    const g = svg.querySelector("g.scrub");
    while (g.firstChild) g.removeChild(g.firstChild);
    if (t == null) return;
    const x = sc.x(t);
    el("line", {
      x1: x, x2: x, y1: sc.pad.t, y2: sc.pad.t + sc.plotH,
      stroke: "#c45a3a", "stroke-width": 1, "stroke-opacity": 0.9
    }, g);
    const on = [];
    S.trips.forEach((trip) => {
      const p = positionAt(trip, t, byId);
      if (!p) return;
      on.push(p);
      const west = trip.dir === 1;
      el("circle", {
        cx: x, cy: sc.y(p.chainage),
        r: trip.route === "7X" ? 2.6 : 2.1,
        fill: west ? "#d19a4a" : "#a8b6b8",
        stroke: "#0c0b09", "stroke-width": 0.6
      }, g);
    });
    return on;
  }

  function drawRibbon(svg, S, w, h) {
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", "0 0 " + w + " " + h);
    const lons = S.stations.map((s) => s.lon);
    const lats = S.stations.map((s) => s.lat);
    const minLon = Math.min.apply(null, lons), maxLon = Math.max.apply(null, lons);
    const minLat = Math.min.apply(null, lats), maxLat = Math.max.apply(null, lats);
    const pad = { l: 10, r: 10, t: 14, b: 14 };
    const x = (lon) => pad.l + ((lon - minLon) / (maxLon - minLon)) * (w - pad.l - pad.r);
    const y = (lat) => pad.t + ((maxLat - lat) / (maxLat - minLat)) * (h - pad.t - pad.b);
    // river band between vernon and grand central longitudes
    const v = S.stations.find((s) => s.id === "721");
    const g = S.stations.find((s) => s.id === "723");
    el("rect", {
      x: Math.min(x(v.lon), x(g.lon)),
      y: pad.t,
      width: Math.abs(x(g.lon) - x(v.lon)),
      height: h - pad.t - pad.b,
      fill: "rgba(90,110,112,0.16)"
    }, svg);
    let d = "";
    (S.ribbon || []).forEach((p, i) => {
      const cmd = (i === 0 ? "M" : "L") + x(p.lon).toFixed(1) + "," + y(p.lat).toFixed(1);
      d += cmd;
    });
    if (d) el("path", { d: d, fill: "none", stroke: "#8a8073", "stroke-width": 1.2 }, svg);
    S.stations.forEach((st) => {
      const term = st.id === "701" || st.id === "726";
      el("circle", {
        cx: x(st.lon), cy: y(st.lat), r: term ? 2.4 : 1.5,
        fill: term ? "#e8dfd0" : "#8a8073"
      }, svg);
    });
    el("text", { x: x(S.stations[S.stations.length - 1].lon), y: h - 3, fill: "#7a7166", "font-size": 8, "font-family": "IBM Plex Sans, sans-serif", "text-anchor": "start" }, svg).textContent = "West · Hudson Yards";
    el("text", { x: x(S.stations[0].lon), y: h - 3, fill: "#7a7166", "font-size": 8, "font-family": "IBM Plex Sans, sans-serif", "text-anchor": "end" }, svg).textContent = "East · Flushing";
  }

  function drawDensity(svg, S, w, h) {
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", "0 0 " + w + " " + h);
    const o = S.computed.trips_by_hour_origin;
    const hours = [];
    let max = 1;
    for (let i = 0; i < 25; i++) {
      const west = o.west_local[i] + o.west_express[i];
      const east = o.east_local[i] + o.east_express[i];
      hours.push({ i, west, east, wx: o.west_express[i], ex: o.east_express[i] });
      max = Math.max(max, west, east);
    }
    const pad = { l: 18, r: 4, t: 6, b: 16 };
    const slot = (w - pad.l - pad.r) / 25;
    const mid = pad.t + (h - pad.t - pad.b) / 2;
    const half = (h - pad.t - pad.b) / 2 - 2;
    el("line", { x1: pad.l, x2: w - pad.r, y1: mid, y2: mid, stroke: "#2c2822" }, svg);
    hours.forEach((hr) => {
      const x = pad.l + hr.i * slot;
      const hw = (hr.west / max) * half;
      const he = (hr.east / max) * half;
      const hwx = (hr.wx / max) * half;
      const hex = (hr.ex / max) * half;
      el("rect", { x: x + 1, y: mid - hw, width: slot - 2, height: Math.max(0, hw), fill: "rgba(209,154,74,0.70)" }, svg);
      if (hwx > 0) el("rect", { x: x + 1, y: mid - hwx, width: slot - 2, height: hwx, fill: "#d19a4a" }, svg);
      el("rect", { x: x + 1, y: mid, width: slot - 2, height: Math.max(0, he), fill: "rgba(168,182,184,0.70)" }, svg);
      if (hex > 0) el("rect", { x: x + 1, y: mid, width: slot - 2, height: hex, fill: "#a8b6b8" }, svg);
      if (hr.i % 3 === 0) {
        el("text", {
          x: x + slot / 2, y: h - 3,
          fill: "#534c44", "font-size": 8, "font-family": "IBM Plex Sans, sans-serif", "text-anchor": "middle"
        }, svg).textContent = String(hr.i).padStart(2, "0");
      }
    });
    el("text", { x: 2, y: pad.t + 6, fill: "#7a7166", "font-size": 8, "font-family": "IBM Plex Sans, sans-serif" }, svg).textContent = "西";
    el("text", { x: 2, y: h - pad.b - 2, fill: "#7a7166", "font-size": 8, "font-family": "IBM Plex Sans, sans-serif" }, svg).textContent = "东";
  }

  function drawRideBars(svg, S, w, h, opts) {
    opts = opts || {};
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", "0 0 " + w + " " + h);
    const date = (S.ridership && S.ridership.default_date) || "2026-08-03";
    const pad = { l: 18, r: 6, t: 4, b: 14 };

    if (opts.hourly && opts.complex) {
      const series = opts.complex.hourly[date] || [];
      const max = Math.max(1, Math.max.apply(null, series));
      const slot = (w - pad.l - pad.r) / 24;
      series.forEach((v, i) => {
        const bh = (v / max) * (h - pad.t - pad.b);
        const x = pad.l + i * slot;
        const attr = {
          x: x + 1, y: h - pad.b - bh, width: slot - 2, height: Math.max(0, bh)
        };
        if (opts.complex.multi_line) {
          el("rect", Object.assign(attr, { fill: "none", stroke: "#8a8073", "stroke-width": 1 }), svg);
        } else {
          el("rect", Object.assign(attr, { fill: "rgba(232,223,208,0.45)" }), svg);
        }
        if (i % 3 === 0) {
          el("text", { x: x + slot / 2, y: h - 3, fill: "#534c44", "font-size": 8, "font-family": "IBM Plex Sans, sans-serif", "text-anchor": "middle" }, svg).textContent = String(i).padStart(2, "0");
        }
      });
      return;
    }

    // daily totals: scale to 7-only max so those stations remain readable.
    // Multi-line complexes are often much larger; cap them and mark as exceeding the scale.
    const cxs = (S.ridership && S.ridership.complexes) || [];
    const onlyMax = Math.max(1, Math.max.apply(null, cxs.filter((c) => !c.multi_line).map((c) => c.daily_sum[date] || 0)));
    const slot = (w - pad.l - pad.r) / cxs.length;
    const maxH = h - pad.t - pad.b;
    cxs.forEach((c, i) => {
      const v = c.daily_sum[date] || 0;
      const capped = Math.min(v, onlyMax);
      const bh = (capped / onlyMax) * maxH;
      const x = pad.l + i * slot;
      const attr = { x: x + 0.6, y: h - pad.b - bh, width: Math.max(1, slot - 1.2), height: Math.max(0, bh) };
      if (c.multi_line) {
        el("rect", Object.assign({}, attr, { fill: "none", stroke: "#8a8073", "stroke-width": 0.9 }), svg);
        if (v > onlyMax) {
          el("text", { x: x + slot / 2, y: h - pad.b - bh - 2, fill: "#8a8073", "font-size": 7, "font-family": "IBM Plex Sans, sans-serif", "text-anchor": "middle" }, svg).textContent = "▸";
        }
      } else {
        el("rect", Object.assign({}, attr, { fill: "rgba(232,223,208,0.72)" }), svg);
      }
    });
    el("text", { x: pad.l, y: h - 3, fill: "#534c44", "font-size": 8, "font-family": "IBM Plex Sans, sans-serif" }, svg).textContent = "日合计 · 尺度取 7 号线独有综合体；空心若封顶则该综合体超出本尺（含其他线路）";
  }

  root.LumenRender = {
    el, fmtClock, fmtSpan, stationIndex, scales,
    tripPathD, positionAt, drawMarey, highlightTrip, drawScrub,
    drawRibbon, drawDensity, drawRideBars
  };
})(window);
