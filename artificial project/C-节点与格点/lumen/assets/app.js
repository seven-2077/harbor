(function () {
  const S = window.SPECIMEN, R = window.LumenC;
  if (!S || !R) return;
  const inn = S.indoor, out = S.outdoor, C = inn.comfort_design;
  const n = inn.seq.length;
  const state = { i: 90, dragging: false }; // start mid-window 12:15
  const inv = {};

  function box(el) {
    const r = el.getBoundingClientRect();
    return { w: Math.max(120, r.width), h: Math.max(80, r.height) };
  }

  function renderCharts() {
    const common = { times: inn.times, cursor: state.i };
    let b;
    b = box(document.getElementById("ch-temp"));
    inv.temp = R.drawChannel(document.getElementById("ch-temp"), Object.assign({
      w: b.w, h: b.h, series: inn.series.temperature, color: "#c4a07a",
      title: "CH  TEMP  °C   ·   推断的 BME280，模拟",
      ref: out.overlap.t, refLabel: "室外整点  25.8 °C",
      band: C.t_band, bandLabel: "设计口径 20–26 °C",
      digits: 1
    }, common));
    b = box(document.getElementById("ch-rh"));
    inv.rh = R.drawChannel(document.getElementById("ch-rh"), Object.assign({
      w: b.w, h: b.h, series: inn.series.relative_humidity, color: "#7fa8a4",
      title: "CH  RH  %   ·   推断的 BME280，模拟",
      ref: out.overlap.rh, refLabel: "室外整点  49 %",
      band: C.rh_band, bandLabel: "设计口径 40–60 %",
      digits: 0
    }, common));
    b = box(document.getElementById("ch-lux"));
    inv.lux = R.drawChannel(document.getElementById("ch-lux"), Object.assign({
      w: b.w, h: b.h, series: inn.series.illuminance, color: "#c8bd8e",
      title: "CH  LUX   ·   推断的 BH1750，模拟  ·  无室外对照通道",
      ref: 300, refLabel: "设计口径  阅读 300 lx",
      digits: 0
    }, common));
    // 300 is a mark; a zero-thickness band may vanish — drawChannel uses band as fill between 300 and 300.
    // That's ok if we also have the label; a line is better. Already a fill of 0 height. Label still shows near 300.
  }

  function renderSide() {
    const wT = document.getElementById("weekT").getBoundingClientRect().width || 300;
    const hT = document.getElementById("weekT").getBoundingClientRect().height || 58;
    const hP = document.getElementById("weekP").getBoundingClientRect().height || 50;
    R.drawWeek(document.getElementById("weekT"), out.hours, "t", { w: wT, h: hT, color: "#6a8aa8", title: "室外温度 °C", digits: 0 });
    R.drawWeek(document.getElementById("weekP"), out.hours, "pm25", { w: wT, h: hP, color: "#8b9398", title: "室外 PM2.5  μg/m³", digits: 0 });
    const g = document.getElementById("gasSpark").getBoundingClientRect().width || 300;
    const gH = document.getElementById("gasSpark").getBoundingClientRect().height || 36;
    R.drawSpark(document.getElementById("gasSpark"), inn.series.gas_index, { w: g, h: gH, color: "#8b9398", cursor: state.i });
    paintText();
  }

  function paintText() {
    const i = state.i;
    document.getElementById("clock").textContent = R.fmtClock(inn.times[i], true);
    document.getElementById("clockSub").textContent = "室内采样点 " + (i + 1) + " / " + n + " · 不对室外做 10 秒插值";
    const T = inn.series.temperature[i], H = inn.series.relative_humidity[i];
    const P = inn.series.pressure[i], L = inn.series.illuminance[i];
    const G = inn.series.gas_index[i], M = inn.series.mcu_temperature[i];
    document.getElementById("readout").innerHTML =
      "<b class='cu'>温度</b> " + R.num(T, 2) + " °C　" +
      "<b class='te'>湿度</b> " + R.num(H, 2) + " %　" +
      "<b class='st'>气压</b> " + R.num(P, 2) + " hPa<br>" +
      "<b class='la'>照度</b> " + R.num(L, 1) + " lx　" +
      "<b>气体指数</b> " + R.num(G, 2) + "（未标定）　" +
      "<b class='ph'>片内温度</b> " + R.num(M, 2) + " °C（非气温）";

    const ov = out.overlap, st = inn.stats;
    document.getElementById("pair").innerHTML =
      "<div><div class='k'>温度</div><div class='v cu'>" + st.temperature.mean.toFixed(2) + " °C</div><div class='s'>室内半小时均值 · 模拟</div></div>" +
      "<div><div class='k'>温度</div><div class='v stl'>" + ov.t.toFixed(1) + " °C</div><div class='s'>室外格点整点值</div></div>" +
      "<div><div class='k'>相对湿度</div><div class='v te'>" + st.relative_humidity.mean.toFixed(1) + " %</div><div class='s'>室内半小时均值 · 模拟</div></div>" +
      "<div><div class='k'>相对湿度</div><div class='v stl'>" + ov.rh.toFixed(0) + " %</div><div class='s'>室外格点整点值</div></div>" +
      "<div><div class='k'>气压</div><div class='v st'>" + st.pressure.mean.toFixed(2) + " hPa</div><div class='s'>室内半小时均值 · 模拟</div></div>" +
      "<div><div class='k'>气压</div><div class='v stl'>" + ov.p.toFixed(1) + " hPa</div><div class='s'>室外格点整点值</div></div>";

    const dT = st.temperature.mean - ov.t;
    const dH = st.relative_humidity.mean - ov.rh;
    document.getElementById("steady").innerHTML =
      "室内温度极差 <b>" + st.temperature.span.toFixed(2) + " °C</b>（标准差 " + st.temperature.std.toFixed(2) + "）。" +
      "同日室外格点 14.3–28.3 °C。半小时变幅远小于日较差——这是<b>本条模拟流的形态</b>，用来演示稳态观察。<br>" +
      "设计口径 20–26 °C：<b>" + C.t_in_band + " / " + C.n + "</b>（全部略高于上沿）；湿度 40–60%：<b>" + C.rh_in_band + " / " + C.n + "</b>；照度 ≥ 300 lx：<b>" + C.lux_ge_300 + " / " + C.n + "</b>。口径不是国标。" +
      "均值与整点之差：温度 " + (dT >= 0 ? "+" : "") + dT.toFixed(2) + " °C，湿度 " + (dH >= 0 ? "+" : "") + dH.toFixed(1) + " %（样品构造，非实测效应）。";

    document.getElementById("mcu").innerHTML =
      "此刻片内温度 <b class='ph'>" + R.num(M, 2) + " °C</b>（半小时均值 " + inn.stats.mcu_temperature.mean.toFixed(2) + " °C），同时刻空气通道 " + R.num(T, 2) + " °C。<b>不能当作室内气温</b>。本列仍是模拟值。";
  }

  function setI(i) {
    state.i = Math.max(0, Math.min(n - 1, i | 0));
    renderCharts();
    const g = document.getElementById("gasSpark").getBoundingClientRect().width || 300;
    const gH = document.getElementById("gasSpark").getBoundingClientRect().height || 36;
    R.drawSpark(document.getElementById("gasSpark"), inn.series.gas_index, { w: g, h: gH, color: "#8b9398", cursor: state.i });
    paintText();
  }

  function bindPane(id, which) {
    const svg = document.getElementById(id);
    svg.addEventListener("pointerdown", (ev) => {
      state.dragging = true;
      try { svg.setPointerCapture(ev.pointerId); } catch (e) {}
      const r = svg.getBoundingClientRect();
      const invFn = inv[which] && inv[which].invX;
      if (invFn) setI(invFn(ev.clientX - r.left));
    });
    svg.addEventListener("pointermove", (ev) => {
      if (!state.dragging) return;
      const r = svg.getBoundingClientRect();
      const invFn = inv[which] && inv[which].invX;
      if (invFn) setI(invFn(ev.clientX - r.left));
    });
  }
  window.addEventListener("pointerup", () => { state.dragging = false; });
  window.addEventListener("keydown", (ev) => {
    if (ev.key === "ArrowLeft") { setI(state.i - 1); ev.preventDefault(); }
    if (ev.key === "ArrowRight") { setI(state.i + 1); ev.preventDefault(); }
  });

  bindPane("ch-temp", "temp");
  bindPane("ch-rh", "rh");
  bindPane("ch-lux", "lux");

  function resize() { renderCharts(); renderSide(); }
  window.addEventListener("resize", resize);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(resize);
  resize();
})();
