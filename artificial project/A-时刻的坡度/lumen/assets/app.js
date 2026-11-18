(function () {
  const S = window.SPECIMEN;
  const R = window.LumenRender;
  if (!S || !R) return;

  const byId = R.stationIndex(S);
  const tripById = {};
  S.trips.forEach((t) => { tripById[t.id] = t; });
  const complexByStation = {};
  (S.ridership && S.ridership.complexes || []).forEach((c) => { complexByStation[c.gtfs_parent] = c; });

  const state = {
    time: 8 * 3600 + 30 * 60,
    hover: null,
    selected: null,
    station: null,
    dragging: false,
    defaultTimeNote: true
  };

  const svg = document.getElementById("marey");
  const ribbon = document.getElementById("ribbon");
  const density = document.getElementById("density");
  const ridehour = document.getElementById("ridehour");
  let sc = null;

  function layoutBox(node, pad) {
    const r = node.getBoundingClientRect();
    return { w: Math.max(200, r.width), h: Math.max(200, r.height), pad: pad };
  }

  function renderChart() {
    const box = layoutBox(svg, { t: 8, r: 10, b: 28, l: 158 });
    sc = R.scales(S, box);
    R.drawMarey(svg, S, sc);
    bindHits();
    paintFocus();
  }

  function renderSide() {
    const rw = ribbon.getBoundingClientRect().width || 292;
    R.drawRibbon(ribbon, S, rw, 64);
    const dw = density.getBoundingClientRect().width || 292;
    try { R.drawDensity(density, S, dw, 96); } catch (e) { console.error(e); }
    try { renderRide(); } catch (e) { console.error(e); }
  }

  function renderRide() {
    const w = ridehour.getBoundingClientRect().width || 292;
    const c = state.station ? complexByStation[state.station] : null;
    const legend = document.getElementById("rideLegend");
    if (c) {
      R.drawRideBars(ridehour, S, w, 88, { hourly: true, complex: c });
      legend.textContent = (c.complex_name) + " · 2026-08-03 各小时进站。单位是综合体进站量" + (c.multi_line ? "，该综合体包含其他线路，不能记作 7 号线独有。" : "（此站综合体名称中仅有 7 号线）。");
    } else {
      R.drawRideBars(ridehour, S, w, 88);
      legend.textContent = "2026-08-03 日合计，不是 11-11 的客流。实心：仅含 7 号线的综合体（用于定尺）。空心：含其他线路；若柱顶有 ▸，表示超出本尺，不能与实心柱直接比高低。";
    }
  }

  function paintFocus() {
    const on = R.drawScrub(svg, state.time, sc, S, byId) || [];
    const focus = state.hover || state.selected;
    R.highlightTrip(svg, focus, sc, byId, S);
    document.getElementById("clock").textContent = R.fmtClock(state.time);
    const sub = document.getElementById("clockSub");
    if (state.defaultTimeNote && !state.dragging) {
      sub.textContent = "初始时刻为设计选择（08:30，落在西向快车窗口内）。线上的点是插值位置，不是实时定位。";
    } else {
      sub.textContent = "表定服务日时钟 · 插值位置，不是实时定位";
    }
    const west = on.filter((p) => p.trip.dir === 1).length;
    const east = on.filter((p) => p.trip.dir === 0).length;
    const ex = on.filter((p) => p.trip.route === "7X").length;
    document.getElementById("onLine").textContent =
      "此时刻表定在途 " + on.length + " 列（西行 " + west + " · 东行 " + east + " · 其中快车 " + ex + "）。由到发时刻线性插值，非实测。";
    renderInspector(focus, on);
    const top = document.querySelector('.side-top');
    if (top) top.classList.toggle('is-inspecting', !!(focus || state.station));
  }

  function renderInspector(trip, on) {
    const box = document.getElementById("inspectBody");
    if (state.station && !trip) {
      box.className = "";
      box.innerHTML = stationHTML(state.station);
      return;
    }
    if (!trip) {
      box.className = "empty";
      box.innerHTML = "悬停一条斜线读取表定到发。点击站名查看间隔；8 月进站量在下方，日期不同。";
      return;
    }
    box.className = "";
    const dir = trip.dir === 1 ? "西行 · 开往 34 St-Hudson Yards" : ("东行 · 开往 " + trip.headsign);
    const kind = trip.route === "7X" ? "7X Express" : "7 Local";
    const first = trip.stops[0];
    const last = trip.stops[trip.stops.length - 1];
    const span = last.a - first.d;
    let rows = trip.stops.map((st) => {
      const same = st.a === st.d;
      const t = same ? R.fmtClock(st.a, { withSeconds: true }) : (R.fmtClock(st.a, { withSeconds: true }) + "–" + R.fmtClock(st.d, { withSeconds: true }));
      return "<div><span class='t'>" + t + "</span>　" + byId[st.s].name + "</div>";
    }).join("");
    box.innerHTML =
      "<div class='trip-head'><span class='hs'>" + trip.headsign + "</span><span class='tag'>" + kind + "</span></div>" +
      "<div class='kv'>" + dir + "<br>表定行程 " + R.fmtSpan(span) + " · " + trip.stops.length + " 站<br>" +
      "始发 " + R.fmtClock(first.d, { withSeconds: true }) + " · 终到 " + R.fmtClock(last.a, { withSeconds: true }) + "<br>" +
      "<b>trip_id</b> " + trip.id + "</div>" +
      "<div class='stops'>" + rows + "</div>";
  }

  function stationHTML(sid) {
    const st = byId[sid];
    const c = complexByStation[sid];
    const deps = { 0: [], 1: [] };
    S.trips.forEach((t) => {
      t.stops.forEach((s) => {
        if (s.s === sid) deps[t.dir].push(s.d);
      });
    });
    function hw(arr) {
      arr = arr.slice().sort((a, b) => a - b);
      if (arr.length < 2) return "—";
      const d = [];
      for (let i = 1; i < arr.length; i++) d.push(arr[i] - arr[i - 1]);
      d.sort((a, b) => a - b);
      return "最小 " + R.fmtSpan(d[0]) + " · 中位 " + R.fmtSpan(d[Math.floor(d.length / 2)]) + " · 共 " + arr.length + " 次出发";
    }
    const date = S.ridership.default_date;
    let ride = "";
    if (c) {
      ride = "<div class='kv' style='margin-top:8px'><b>进站量（" + date + "，非本营运日）</b><br>" +
        c.complex_name + "<br>当日合计 " + c.daily_sum[date].toLocaleString("en-US") + " 次进站" +
        (c.multi_line ? "。此为含其他线路的综合体，不能记作 7 号线独有。" : "。综合体名称中仅有 7 号线。") + "</div>";
    }
    const skip = S.meta.eastbound_local_skips.stations.indexOf(sid) >= 0
      ? "<div class='kv'>在本份 Weekday 时刻表中，东向所有 Local 均未写入本站；西向 Local 有停。按原文，未作修正。</div>"
      : "";
    return "<div class='trip-head'><span class='hs'>" + st.name + "</span></div>" +
      "<div class='kv'>纵轴投影里程 " + Math.round(st.chainage_m) + " m（由 shape 7..S97R 计算）<br>" +
      "西行出发：" + hw(deps[1]) + "<br>东行出发：" + hw(deps[0]) + "</div>" +
      skip + ride;
  }

  function nearestTrip(clientX, clientY) {
    const svgEl = svg;
    const pt = svgEl.createSVGPoint();
    pt.x = clientX; pt.y = clientY;
    const loc = pt.matrixTransform(svgEl.getScreenCTM().inverse());
    let best = null, bestD = 7; // px threshold in svg space
    svgEl.querySelectorAll("path.hit").forEach((p) => {
      try {
        const len = p.getTotalLength();
        // coarse sample
        const step = Math.max(8, len / 40);
        for (let s = 0; s <= len; s += step) {
          const q = p.getPointAtLength(s);
          const d = Math.hypot(q.x - loc.x, q.y - loc.y);
          if (d < bestD) { bestD = d; best = p.getAttribute("data-id"); }
        }
      } catch (e) {}
    });
    return best ? tripById[best] : null;
  }

  function bindHits() {
    svg.addEventListener("pointermove", (ev) => {
      if (state.dragging) return;
      if (ev.target.closest && ev.target.closest("text[data-station]")) {
        if (state.hover) { state.hover = null; paintFocus(); }
        return;
      }
      const t = nearestTrip(ev.clientX, ev.clientY);
      if (t !== state.hover) { state.hover = t; paintFocus(); }
    });
    svg.addEventListener("pointerleave", () => {
      if (state.dragging) return;
      state.hover = null;
      paintFocus();
    });
    svg.querySelectorAll("path.hit").forEach((p) => {
      p.addEventListener("click", (ev) => {
        ev.stopPropagation();
        state.selected = tripById[p.getAttribute("data-id")] || nearestTrip(ev.clientX, ev.clientY);
        paintFocus();
      });
    });
    svg.querySelectorAll("text[data-station]").forEach((t) => {
      t.addEventListener("click", (ev) => {
        ev.stopPropagation();
        state.station = t.getAttribute("data-station");
        state.selected = null;
        state.hover = null;
        renderRide();
        paintFocus();
      });
    });
  }

  function timeFromEvent(ev) {
    const r = svg.getBoundingClientRect();
    const x = ev.clientX - r.left;
    let t = sc.invX(x);
    t = Math.max(sc.t0, Math.min(sc.t1, t));
    return t;
  }

  svg.addEventListener("pointerdown", (ev) => {
    if (ev.target.closest && ev.target.closest("text[data-station]")) return;
    state.dragging = true;
    state.defaultTimeNote = false;
    try { svg.setPointerCapture(ev.pointerId); } catch (e) {}
    state.time = timeFromEvent(ev);
    paintFocus();
  });
  svg.addEventListener("pointermove", (ev) => {
    if (!state.dragging) return;
    state.time = timeFromEvent(ev);
    paintFocus();
  });
  window.addEventListener("pointerup", () => { state.dragging = false; });

  window.addEventListener("keydown", (ev) => {
    if (ev.key === "ArrowLeft" || ev.key === "ArrowRight") {
      state.defaultTimeNote = false;
      state.time += (ev.key === "ArrowRight" ? 60 : -60);
      state.time = Math.max(sc.t0, Math.min(sc.t1, state.time));
      paintFocus();
      ev.preventDefault();
    }
  });

  function resize() {
    renderChart();
    renderSide();
    paintFocus();
  }

  window.addEventListener("resize", resize);

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(resize);
  }
  resize();
})();
