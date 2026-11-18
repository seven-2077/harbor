(function () {
  "use strict";

  const state = {
    meta: null,
    lines: [],
    routes: [],
    stations: [],
    shapes: [],
    arrivals: {},
    analysis: null,
    activeLine: "ALL",
    activeView: "map",
    selectedStationId: null,
    arrivalLineFilter: "ALL",
    map: null,
    layerGroup: null,
    leafletReady: typeof window.L !== "undefined",
  };

  function $(id) {
    return document.getElementById(id);
  }

  function contrastText(hex) {
    if (!hex || hex[0] !== "#" || hex.length < 7) return "#111";
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    const y = (r * 299 + g * 587 + b * 114) / 1000;
    return y > 160 ? "#111" : "#fff";
  }

  function lineById(id) {
    return state.lines.find(function (l) { return l.id === id; });
  }

  function pill(lineId) {
    const line = lineById(lineId);
    const color = (line && line.color) || "#666";
    const text = (line && line.text_color) || contrastText(color);
    const span = document.createElement("span");
    span.className = "line-pill";
    span.textContent = lineId;
    span.style.background = color;
    span.style.color = text;
    return span;
  }

  async function loadJSON(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error("无法读取 " + path + "（HTTP " + res.status + "）");
    return res.json();
  }

  function renderSource() {
    const m = state.meta;
    const src = m.source || {};
    const box = $("source-box");
    box.innerHTML =
      "<strong>数据来源：</strong>" + escapeHtml(src.name || m.agency_name || "") + "<br>" +
      "机构：" + linkOrText(m.agency_name, m.agency_url) + "<br>" +
      "官方 permalink：<a href=\"" + escapeAttr(src.permalink || "#") + "\">" + escapeHtml(src.permalink || "") + "</a><br>" +
      "许可证：<a href=\"" + escapeAttr(src.license_url || "#") + "\">" + escapeHtml(src.license_name || "见官方协议") + "</a>" +
      "（使用、复制、再分发须遵守该协议；不得使用官方商标；不得主张对数据的所有权）<br>" +
      "样品服务日：<strong>" + escapeHtml(m.service_date) + "</strong>　时区：<strong>" + escapeHtml(m.timezone || "") + "</strong><br>" +
      "是否使用 Atlas 小样本：<strong>" + (src.used_atlas_sample ? "是" : "否") + "</strong>";
    if (m.disclaimer) $("disclaimer").textContent = m.disclaimer;
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function escapeAttr(s) {
    return escapeHtml(s).replace(/"/g, "&quot;");
  }
  function linkOrText(text, url) {
    if (url) return "<a href=\"" + escapeAttr(url) + "\">" + escapeHtml(text) + "</a>";
    return escapeHtml(text || "");
  }

  function renderLineFilters() {
    const host = $("line-filters");
    host.innerHTML = "";
    const all = document.createElement("button");
    all.type = "button";
    all.className = "chip is-active";
    all.dataset.line = "ALL";
    all.textContent = "全部线路";
    host.appendChild(all);
    state.lines.forEach(function (line) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      btn.dataset.line = line.id;
      const sw = document.createElement("span");
      sw.className = "swatch";
      sw.style.background = line.color;
      btn.appendChild(sw);
      btn.appendChild(document.createTextNode(line.name));
      host.appendChild(btn);
    });
    host.addEventListener("click", function (ev) {
      const btn = ev.target.closest(".chip");
      if (!btn) return;
      state.activeLine = btn.dataset.line;
      host.querySelectorAll(".chip").forEach(function (el) {
        el.classList.toggle("is-active", el === btn);
      });
      refreshViews();
    });
  }

  function stationVisible(st) {
    if (state.activeLine === "ALL") return true;
    return (st.line_ids || []).indexOf(state.activeLine) !== -1;
  }

  function refreshViews() {
    drawMap();
    renderStationTable();
    if (state.selectedStationId) renderStationPanel(state.selectedStationId);
  }

  function initMap() {
    if (!state.leafletReady) {
      $("map-hint").textContent =
        "未加载到本地 Leaflet，地图不可用。下面与右侧的列表/到站时刻仍可使用。请确认 app/vendor/leaflet/leaflet.js 存在，并通过本地 HTTP 服务打开本页（不要直接双击文件）。";
      return;
    }
    state.map = L.map("map", { scrollWheelZoom: true, attributionControl: true });
    L.control.attribution({ prefix: false }).addTo(state.map)
      .setPrefix("无在线底图 · 线路形状来自 GTFS shapes.txt");
    state.layerGroup = L.layerGroup().addTo(state.map);
    drawMap();
  }

  function drawMap() {
    if (!state.map || !state.layerGroup) return;
    state.layerGroup.clearLayers();
    const bounds = [];
    state.shapes.forEach(function (sh) {
      if (state.activeLine !== "ALL" && sh.line_id !== state.activeLine) return;
      const latlngs = (sh.coordinates || []).map(function (c) { return [c[1], c[0]]; });
      if (!latlngs.length) return;
      latlngs.forEach(function (p) { bounds.push(p); });
      L.polyline(latlngs, {
        color: sh.color || "#333",
        weight: 4,
        opacity: 0.85,
        lineJoin: "round",
      }).addTo(state.layerGroup);
    });
    state.stations.forEach(function (st) {
      if (st.lat == null || st.lon == null) return;
      if (!stationVisible(st)) return;
      bounds.push([st.lat, st.lon]);
      const selected = st.id === state.selectedStationId;
      const marker = L.circleMarker([st.lat, st.lon], {
        radius: selected ? 8 : 5,
        color: "#1c1a16",
        weight: selected ? 2 : 1,
        fillColor: "#fff",
        fillOpacity: 1,
      }).addTo(state.layerGroup);
      marker.bindTooltip(st.name);
      marker.on("click", function () { selectStation(st.id); });
    });
    if (bounds.length) {
      state.map.fitBounds(bounds, { padding: [24, 24], maxZoom: 12 });
    }
  }

  function renderStationTable() {
    const q = ($("station-search").value || "").trim().toLowerCase();
    const tbody = $("station-table").querySelector("tbody");
    tbody.innerHTML = "";
    state.stations.forEach(function (st) {
      if (!stationVisible(st)) return;
      if (q && (st.name || "").toLowerCase().indexOf(q) === -1 && (st.id || "").toLowerCase().indexOf(q) === -1) {
        return;
      }
      const tr = document.createElement("tr");
      tr.className = "is-clickable" + (st.id === state.selectedStationId ? " is-selected" : "");
      tr.addEventListener("click", function () { selectStation(st.id); });
      const nameTd = document.createElement("td");
      nameTd.textContent = st.name;
      const lineTd = document.createElement("td");
      (st.line_ids || []).forEach(function (id) { lineTd.appendChild(pill(id)); });
      const hoursTd = document.createElement("td");
      hoursTd.textContent = (st.service_start && st.service_end) ? (st.service_start + "–" + st.service_end) : "—";
      const cntTd = document.createElement("td");
      cntTd.textContent = st.arrival_count == null ? "—" : String(st.arrival_count);
      tr.appendChild(nameTd);
      tr.appendChild(lineTd);
      tr.appendChild(hoursTd);
      tr.appendChild(cntTd);
      tbody.appendChild(tr);
    });
  }

  function selectStation(id) {
    state.selectedStationId = id;
    state.arrivalLineFilter = "ALL";
    renderStationPanel(id);
    drawMap();
    renderStationTable();
  }

  function renderStationPanel(id) {
    const st = state.stations.find(function (s) { return s.id === id; });
    if (!st) return;
    $("station-title").textContent = st.name;
    $("station-meta").textContent =
      "车站代码 " + st.id + " · 服务日 " + state.meta.service_date +
      " · 时刻为 " + (state.meta.timezone || "GTFS 当地时区") + " 的计划到站时刻，不是北京时间。";
    $("station-hours").textContent =
      "服务时段（当天最早至最晚到站）：" +
      (st.service_start || "—") + " – " + (st.service_end || "—") +
      "，共 " + (st.arrival_count || 0) + " 次到站。超过 24:00 的时刻表示跨过午夜的车次。";
    $("station-body").hidden = false;

    const filt = $("station-line-filters");
    filt.innerHTML = "";
    const allBtn = document.createElement("button");
    allBtn.type = "button";
    allBtn.className = "chip" + (state.arrivalLineFilter === "ALL" ? " is-active" : "");
    allBtn.textContent = "该站全部线路";
    allBtn.addEventListener("click", function () {
      state.arrivalLineFilter = "ALL";
      renderStationPanel(id);
    });
    filt.appendChild(allBtn);
    (st.line_ids || []).forEach(function (lid) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip" + (state.arrivalLineFilter === lid ? " is-active" : "");
      const sw = document.createElement("span");
      sw.className = "swatch";
      const line = lineById(lid);
      sw.style.background = (line && line.color) || "#666";
      btn.appendChild(sw);
      btn.appendChild(document.createTextNode(lid));
      btn.addEventListener("click", function () {
        state.arrivalLineFilter = lid;
        renderStationPanel(id);
      });
      filt.appendChild(btn);
    });

    const rows = (state.arrivals[id] || []).filter(function (a) {
      if (state.activeLine !== "ALL" && a.line_id !== state.activeLine) return false;
      if (state.arrivalLineFilter !== "ALL" && a.line_id !== state.arrivalLineFilter) return false;
      return true;
    });
    const tbody = $("arrivals-table").querySelector("tbody");
    tbody.innerHTML = "";
    rows.forEach(function (a) {
      const tr = document.createElement("tr");
      const t = document.createElement("td");
      t.textContent = a.hhmm;
      const l = document.createElement("td");
      l.appendChild(pill(a.line_id));
      const h = document.createElement("td");
      h.textContent = a.headsign || ("方向 " + (a.direction_id || ""));
      tr.appendChild(t);
      tr.appendChild(l);
      tr.appendChild(h);
      tbody.appendChild(tr);
    });
  }

  function renderAnalysis() {
    const rows = (state.analysis && state.analysis.rows) || [];
    const tbody = $("headway-table").querySelector("tbody");
    tbody.innerHTML = "";
    rows.forEach(function (r) {
      const tr = document.createElement("tr");
      const tdLine = document.createElement("td");
      tdLine.appendChild(pill(r.line_id));
      const tdName = document.createElement("td");
      tdName.textContent = r.route_name || r.route_id;
      const tdTrips = document.createElement("td");
      tdTrips.textContent = r.trip_count;
      const tdSpan = document.createElement("td");
      tdSpan.textContent = (r.first_dep || "—") + "–" + (r.last_dep || "—");
      const tdMed = document.createElement("td");
      tdMed.textContent = r.median_headway_min == null ? "—" : String(r.median_headway_min);
      const tdMean = document.createElement("td");
      tdMean.textContent = r.mean_headway_min == null ? "—" : String(r.mean_headway_min);
      tr.appendChild(tdLine);
      tr.appendChild(tdName);
      tr.appendChild(tdTrips);
      tr.appendChild(tdSpan);
      tr.appendChild(tdMed);
      tr.appendChild(tdMean);
      tbody.appendChild(tr);
    });
    drawTripChart(rows);
    fillSpacetimeSelect();
    drawSpacetime();
  }

  function drawTripChart(rows) {
    const canvas = $("trip-chart");
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const byLine = {};
    rows.forEach(function (r) {
      if (!byLine[r.line_id]) byLine[r.line_id] = { count: 0, color: r.color };
      byLine[r.line_id].count += r.trip_count;
    });
    const keys = state.lines.map(function (l) { return l.id; }).filter(function (id) { return byLine[id]; });
    const max = Math.max.apply(null, keys.map(function (k) { return byLine[k].count; }).concat([1]));
    const padL = 48, padB = 36, padT = 20, padR = 16;
    const iw = w - padL - padR;
    const ih = h - padT - padB;
    const bw = iw / Math.max(keys.length, 1);
    ctx.fillStyle = "#5c564c";
    ctx.font = "12px sans-serif";
    ctx.fillText("班次数（两个方向合计，计划时刻）", padL, 14);
    keys.forEach(function (k, i) {
      const val = byLine[k].count;
      const bh = (val / max) * ih;
      const x = padL + i * bw + bw * 0.18;
      const y = padT + ih - bh;
      const line = lineById(k);
      ctx.fillStyle = (line && line.color) || byLine[k].color || "#336699";
      ctx.fillRect(x, y, bw * 0.64, bh);
      ctx.fillStyle = "#1c1a16";
      ctx.fillText(String(val), x, y - 4);
      ctx.fillText(k, x, padT + ih + 16);
    });
    ctx.strokeStyle = "#d9d0c3";
    ctx.beginPath();
    ctx.moveTo(padL, padT);
    ctx.lineTo(padL, padT + ih);
    ctx.lineTo(padL + iw, padT + ih);
    ctx.stroke();
  }

  function fillSpacetimeSelect() {
    const sel = $("spacetime-select");
    const groups = (state.analysis && state.analysis.spacetime) || [];
    sel.innerHTML = "";
    groups.forEach(function (g, i) {
      const opt = document.createElement("option");
      opt.value = String(i);
      opt.textContent = g.line_id + " · " + (g.label || ("方向 " + g.direction_id)) + "（" + g.trip_count + " 趟）";
      sel.appendChild(opt);
    });
    // 默认选停站较多、班次适中的线，便于一打开就能看清
    let best = 0, bestScore = -1;
    groups.forEach(function (g, i) {
      const score = (g.stations || []).length * 10 + Math.min(g.trip_count, 80);
      if (score > bestScore) { bestScore = score; best = i; }
    });
    sel.value = String(best);
    sel.onchange = drawSpacetime;
  }

  function drawSpacetime() {
    const canvas = $("spacetime-chart");
    const ctx = canvas.getContext("2d");
    const groups = (state.analysis && state.analysis.spacetime) || [];
    const idx = parseInt($("spacetime-select").value || "0", 10) || 0;
    const g = groups[idx];
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    if (!g) {
      ctx.fillStyle = "#5c564c";
      ctx.fillText("没有可绘制的时空图数据。", 16, 24);
      return;
    }
    const stations = g.stations || [];
    const trips = g.trips || [];
    const padL = 170, padR = 20, padT = 28, padB = 36;
    const iw = w - padL - padR;
    const ih = h - padT - padB;
    let tMin = 4 * 60, tMax = 26 * 60;
    trips.forEach(function (tr) {
      (tr.points || []).forEach(function (p) {
        if (p.t < tMin) tMin = Math.floor(p.t / 60) * 60;
        if (p.t > tMax) tMax = Math.ceil(p.t / 60) * 60;
      });
    });
    if (tMax <= tMin) tMax = tMin + 60;
    function xOf(t) { return padL + ((t - tMin) / (tMax - tMin)) * iw; }
    function yOf(i) {
      if (stations.length <= 1) return padT + ih / 2;
      return padT + (i / (stations.length - 1)) * ih;
    }
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "#eee8dc";
    ctx.fillStyle = "#5c564c";
    ctx.font = "11px sans-serif";
    ctx.textAlign = "center";
    for (let t = tMin; t <= tMax; t += 60) {
      const x = xOf(t);
      ctx.beginPath();
      ctx.moveTo(x, padT);
      ctx.lineTo(x, padT + ih);
      ctx.stroke();
      const hh = Math.floor(t / 60);
      const mm = t % 60;
      ctx.fillText((hh < 10 ? "0" : "") + hh + ":" + (mm < 10 ? "0" : "") + mm, x, padT + ih + 16);
    }
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    stations.forEach(function (s, i) {
      const y = yOf(i);
      ctx.strokeStyle = "#f0ebe1";
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(padL + iw, y);
      ctx.stroke();
      ctx.fillStyle = "#1c1a16";
      ctx.fillText(s.name, padL - 8, y);
    });
    ctx.globalAlpha = 0.72;
    ctx.strokeStyle = g.color || "#333";
    ctx.lineWidth = 1;
    trips.forEach(function (tr) {
      const pts = tr.points || [];
      if (pts.length < 2) return;
      ctx.beginPath();
      let started = false;
      let lastI = null;
      pts.forEach(function (p) {
        const x = xOf(p.t);
        const y = yOf(p.i);
        // 参考站序中不相邻则视为短交路/跳停，断开
        if (!started || lastI == null || Math.abs(p.i - lastI) > 1) {
          ctx.moveTo(x, y);
          started = true;
        } else {
          ctx.lineTo(x, y);
        }
        lastI = p.i;
      });
      ctx.stroke();
    });
    ctx.globalAlpha = 1;
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";
    ctx.fillStyle = "#5c564c";
    ctx.font = "12px sans-serif";
    ctx.fillText(g.line_id + " · " + (g.label || "") + " · " + trips.length + " 趟 · 横轴为当地计划时刻", padL, 16);
  }

  function bindTabs() {
    document.querySelectorAll(".tab").forEach(function (tab) {
      tab.addEventListener("click", function () {
        state.activeView = tab.dataset.view;
        document.querySelectorAll(".tab").forEach(function (t) {
          const on = t === tab;
          t.classList.toggle("is-active", on);
          t.setAttribute("aria-selected", on ? "true" : "false");
        });
        document.querySelectorAll(".view").forEach(function (v) {
          v.classList.toggle("is-active", v.id === "view-" + state.activeView);
        });
        if (state.activeView === "map" && state.map) {
          setTimeout(function () { state.map.invalidateSize(); }, 0);
        }
        if (state.activeView === "analysis") renderAnalysis();
      });
    });
    $("station-search").addEventListener("input", renderStationTable);
  }

  async function start() {
    try {
      const pack = await Promise.all([
        loadJSON("data/meta.json"),
        loadJSON("data/lines.json"),
        loadJSON("data/stations.json"),
        loadJSON("data/shapes.json"),
        loadJSON("data/arrivals.json"),
        loadJSON("data/analysis.json"),
      ]);
      state.meta = pack[0];
      state.lines = pack[1].lines || [];
      state.routes = pack[1].routes || [];
      state.stations = pack[2].stations || [];
      state.shapes = pack[3].shapes || [];
      state.arrivals = (pack[4].arrivals) || {};
      state.analysis = pack[5];
      renderSource();
      renderLineFilters();
      bindTabs();
      initMap();
      renderStationTable();
      renderAnalysis();
    } catch (err) {
      $("source-box").textContent =
        "数据加载失败：" + err.message +
        "。请先在 helix 目录运行 python3 scripts/prepare.py，再用 python3 -m http.server 从 helix 或 app 目录打开本页。";
    }
  }

  start();
})();
