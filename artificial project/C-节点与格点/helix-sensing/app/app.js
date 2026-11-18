(function () {
  "use strict";

  const state = { meta: null, summary: null, latest: {}, device: null, series: [] };

  const $ = (id) => document.getElementById(id);

  async function loadJSON(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(path + " HTTP " + res.status);
    return res.json();
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderMeta() {
    const m = state.meta;
    $("disclaimer").textContent = m.disclaimer;
    $("source-box").innerHTML =
      "<strong>数据性质：</strong>" + esc(m.protocol) + "。" + esc(m.baud_note || "") + "<br>" +
      "<strong>板型：</strong>主人所述「" + esc(m.board_claimed) + "」；推断为 " + esc(m.board_inferred) + "。" + esc(m.board_note) + "<br>" +
      "<strong>Atlas 样本：</strong>" + (m.used_atlas_sample ? "已使用" : "未使用") + "。<br>" +
      "<strong>请注意：</strong>" + esc(m.data_note) + "<br>" +
      esc(m.openmeteo_attribution || "") + " " + esc(m.openmeteo_license || "");
  }

  function renderTabs() {
    const host = $("node-tabs");
    host.innerHTML = "";
    (state.meta.nodes || []).forEach(function (n, i) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip" + ((state.device || (i === 0 && n.device_id)) === n.device_id ? " is-active" : "");
      btn.textContent = n.label + "（" + n.device_id + "）";
      btn.addEventListener("click", function () {
        state.device = n.device_id;
        renderTabs();
        refreshSeries();
      });
      host.appendChild(btn);
    });
    if (!state.device && state.meta.nodes && state.meta.nodes[0]) {
      state.device = state.meta.nodes[0].device_id;
    }
  }

  function metric(title, value, sub) {
    const d = document.createElement("div");
    d.className = "card";
    d.innerHTML = "<h3>" + esc(title) + "</h3><div class=\"val\">" + esc(value) + "</div><div class=\"sub\">" + esc(sub || "") + "</div>";
    return d;
  }

  function renderCards() {
    const host = $("cards");
    host.innerHTML = "";
    const row = (state.latest || {})[state.device];
    const node = (state.meta.nodes || []).find(function (n) { return n.device_id === state.device; }) || {};
    if (!row) {
      host.appendChild(metric("尚无读数", "—", node.place || ""));
      return;
    }
    host.appendChild(metric("温度（BME280）", Number(row.temp_c).toFixed(2) + " °C", "时间 " + (row.recv_ts || "")));
    host.appendChild(metric("相对湿度", Number(row.rh_pct).toFixed(2) + " %", node.label || ""));
    host.appendChild(metric("气压", Number(row.pressure_hpa).toFixed(2) + " hPa", "室内模拟值；可与室外模式格点对照"));
    host.appendChild(metric("照度（BH1750）", Number(row.lux).toFixed(1) + " lx", ""));
    host.appendChild(metric("MQ135 示意指数", Number(row.mq135_index).toFixed(2), "ADC " + row.mq135_adc + "（未校准，不是 ppm）"));
    host.appendChild(metric("片内温度", Number(row.mcu_temp_c).toFixed(2) + " °C", "更适于看相对变化，不是环境温度"));
  }

  function renderSummary() {
    const box = $("summary-box");
    const s = (state.summary && state.summary.nodes || []).find(function (n) { return n.device_id === state.device; });
    if (!s) { box.textContent = "暂无分析。"; return; }
    const cr = s.comfort_ratio == null ? "—" : (s.comfort_ratio * 100).toFixed(1) + "%";
    const mq = s.mq135_index_range ? (s.mq135_index_range.min.toFixed(2) + "–" + s.mq135_index_range.max.toFixed(2)) : "—";
    const cmp = state.summary.outdoor_compare;
    let cmpHtml = "";
    if (cmp) {
      cmpHtml = "<p>与 Open-Meteo 兰州格点在 " + esc(cmp.outdoor_time) + " 的对照（室内=模拟，室外=模式数据）：温度 "
        + cmp.indoor_temp_c + " / " + cmp.outdoor_temp_c + " °C，湿度 "
        + cmp.indoor_rh_pct + " / " + cmp.outdoor_rh_pct + " %，气压 "
        + cmp.indoor_pressure_hpa + " / " + cmp.outdoor_pressure_hpa + " hPa。"
        + esc(cmp.note) + "</p>";
    }
    box.innerHTML =
      "<p>" + esc((state.summary && state.summary.threshold_note) || "") + "</p>" +
      "<p>样本数：" + s.samples + "。温湿度落在参考舒适区的比例：<strong>" + cr + "</strong>。</p>" +
      "<p>本窗口 MQ135 示意指数范围：" + mq + "（未校准，不是气体 ppm）。</p>" +
      cmpHtml;

    const ul = $("alerts");
    ul.innerHTML = "";
    const items = (state.summary.alerts || []).filter(function (a) {
      return a.device_id === state.device;
    });
    if (!items.length) {
      const li = document.createElement("li");
      li.textContent = "当前该节点没有未恢复的提示（仅依据最新一条模拟读数）。";
      ul.appendChild(li);
      return;
    }
    items.forEach(function (a) {
      const li = document.createElement("li");
      li.className = a.level;
      li.textContent = a.text + "（" + a.recv_ts + "）";
      ul.appendChild(li);
    });
  }

  function drawLines(canvas, series, seriesSpecs, yHint) {
    const ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, w, h);
    const padL = 46, padR = 12, padT = 22, padB = 28;
    const iw = w - padL - padR, ih = h - padT - padB;
    if (!series.length) {
      ctx.fillStyle = "#5a6158";
      ctx.fillText("暂无序列", padL, 24);
      return;
    }
    let ymin = Infinity, ymax = -Infinity;
    seriesSpecs.forEach(function (sp) {
      series.forEach(function (p) {
        const v = p[sp.key];
        if (typeof v === "number") {
          if (v < ymin) ymin = v;
          if (v > ymax) ymax = v;
        }
      });
    });
    if (!(ymax > ymin)) { ymin -= 1; ymax += 1; }
    const pad = (ymax - ymin) * 0.08 || 1;
    ymin -= pad; ymax += pad;
    function xOf(i) { return padL + (series.length === 1 ? iw / 2 : i / (series.length - 1) * iw); }
    function yOf(v) { return padT + ih - (v - ymin) / (ymax - ymin) * ih; }
    ctx.strokeStyle = "#d5d8ce";
    ctx.beginPath();
    ctx.moveTo(padL, padT);
    ctx.lineTo(padL, padT + ih);
    ctx.lineTo(padL + iw, padT + ih);
    ctx.stroke();
    ctx.fillStyle = "#5a6158";
    ctx.font = "11px sans-serif";
    ctx.fillText(yHint || "", padL, 14);
    ctx.fillText(String(Math.round(ymax * 10) / 10), 4, padT + 8);
    ctx.fillText(String(Math.round(ymin * 10) / 10), 4, padT + ih);
    const first = series[0].recv_ts || "";
    const last = series[series.length - 1].recv_ts || "";
    ctx.fillText(first.slice(11, 19) || first, padL, padT + ih + 16);
    ctx.textAlign = "right";
    ctx.fillText(last.slice(11, 19) || last, padL + iw, padT + ih + 16);
    ctx.textAlign = "left";
    seriesSpecs.forEach(function (sp) {
      ctx.strokeStyle = sp.color;
      ctx.beginPath();
      let started = false;
      series.forEach(function (p, i) {
        const v = p[sp.key];
        if (typeof v !== "number") return;
        if (!started) { ctx.moveTo(xOf(i), yOf(v)); started = true; }
        else ctx.lineTo(xOf(i), yOf(v));
      });
      ctx.stroke();
      ctx.fillStyle = sp.color;
      ctx.fillText(sp.label, padL + 8 + seriesSpecs.indexOf(sp) * 120, 14);
    });
  }

  function renderCharts() {
    drawLines($("chart-env"), state.series, [
      { key: "temp_c", color: "#8b3d1e", label: "温度 °C" },
      { key: "rh_pct", color: "#245b6b", label: "相对湿度 %" },
    ], "温度 / 湿度");
    drawLines($("chart-air"), state.series, [
      { key: "mq135_index", color: "#2c5e4a", label: "MQ135 示意指数" },
      { key: "lux", color: "#8a6a00", label: "照度 lx" },
    ], "气体示意指数 / 光照");
  }

  async function refreshSeries() {
    if (!state.device) return;
    const pack = await loadJSON("/api/series?device=" + encodeURIComponent(state.device) + "&minutes=1440");
    state.series = pack.points || [];
    renderCards();
    renderSummary();
    renderCharts();
  }

  async function tick() {
    try {
      const [latest, summary] = await Promise.all([
        loadJSON("/api/latest"),
        loadJSON("/api/summary"),
      ]);
      state.latest = latest.latest || {};
      state.summary = summary;
      const ts = summary.generated_at || "";
      $("live-flag").textContent = "数据窗：" + ts + "（Asia/Shanghai）。这是 Atlas 模拟流回放，不是现场串口。";
      renderCards();
      renderSummary();
    } catch (err) {
      $("live-flag").textContent = "刷新失败：" + err.message;
    }
  }

  async function start() {
    try {
      state.meta = await loadJSON("/api/meta");
      renderMeta();
      renderTabs();
      await Promise.all([tick(), refreshSeries()]);
      setInterval(tick, 5000);
      setInterval(refreshSeries, 15000);
    } catch (err) {
      $("source-box").textContent = "无法加载接口：" + err.message + "。请在 sensing 目录运行 python3 scripts/serve.py，并打开 http://127.0.0.1:8766/app/ 。";
    }
  }

  start();
})();
