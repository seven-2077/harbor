(function () {
  const S = window.SPECIMEN, R = window.LumenB;
  if (!S || !R) return;
  const inn = S.indoor, C = inn.comfort_design, n = inn.seq.length;
  const state = { i: 90, dragging: false, scene: "classroom" };
  let inv = null;

  const SCENES = {
    classroom: "这间教室被当作午间过后的值守样本。按阅读口径，前五分钟 22 / 30 个点还在 300 lx 以上，后五分钟全部低于该线（0 / 30）。温度全程略高于 26 °C 上沿。湿度在带内。这是同一条模拟流上的产品文案，不是某间真实教室的实测。",
    lab: "实验室更关心半小时是否稳态。本条模拟流温度极差仅 0.84 °C，湿度极差 3.07%。温度仍略高于设计口径上沿。气体指数未标定，不能当作实验环境的空气质量结论。这是同一条模拟流上的产品文案，不是某间真实实验室的实测。",
    office: "办公位关心是否偏热、光线是否够用。半小时均温 26.60 °C，略高于设计口径；照度从首五分钟约 308 lx 降到末五分钟约 252 lx。湿度在带内。这是同一条模拟流上的产品文案，不是某间真实办公室的实测。"
  };

  function box(el) {
    const r = el.getBoundingClientRect();
    return { w: Math.max(160, r.width), h: Math.max(80, r.height) };
  }

  function renderTape() {
    const svg = document.getElementById("tape");
    const b = box(svg);
    inv = R.drawTape(svg, {
      w: b.w, h: b.h, times: inn.times, cursor: state.i, comfort: C,
      lanes: [
        { kind: "t", label: "温度", series: inn.series.temperature, spark: true },
        { kind: "rh", label: "湿度", series: inn.series.relative_humidity, spark: true },
        { kind: "lux", label: "照度", series: inn.series.illuminance, spark: true }
      ]
    });
  }

  function paint() {
    const i = state.i;
    const T = inn.series.temperature[i], H = inn.series.relative_humidity[i];
    const P = inn.series.pressure[i], L = inn.series.illuminance[i];
    const G = inn.series.gas_index[i], M = inn.series.mcu_temperature[i];
    const tOk = R.inBand("t", T, C), hOk = R.inBand("rh", H, C), lOk = R.inBand("lux", L, C);

    document.getElementById("clock").textContent = R.fmtClock(inn.times[i], true) + "  ·  采样 " + (i + 1) + " / " + n;
    document.getElementById("heroVal").textContent = R.num(T, 2);
    const tag = document.getElementById("heroTag");
    tag.textContent = tOk ? "温度在设计口径 20–26 °C 内" : "略高于设计口径上沿 26 °C · 不是国标结论";
    tag.className = "hero-tag" + (tOk ? " is-ok" : "");

    document.getElementById("metrics").innerHTML =
      "<div class='metric " + (hOk ? "is-ok" : "is-out") + "'><div class='k'>相对湿度</div><div class='v'>" + R.num(H, 1) + " %</div><div class='s'>" + (hOk ? "在设计口径 40–60% 内" : "超出设计口径") + "</div></div>" +
      "<div class='metric " + (lOk ? "is-ok" : "is-out") + "'><div class='k'>照度</div><div class='v'>" + R.num(L, 0) + " lx</div><div class='s'>" + (lOk ? "达到阅读线 300 lx" : "低于阅读线 300 lx") + "</div></div>" +
      "<div class='metric'><div class='k'>气压</div><div class='v'>" + R.num(P, 1) + " hPa</div><div class='s'>室内通道 · 模拟</div></div>" +
      "<div class='metric'><div class='k'>气体指数 / 片内温度</div><div class='v'>" + R.num(G, 1) + "</div><div class='s'>未标定指数　片内 " + R.num(M, 2) + " °C（非气温）</div></div>";

    document.getElementById("sceneCopy").textContent = SCENES[state.scene];

    const st = inn.stats;
    document.getElementById("brief").innerHTML =
      "半小时温度极差 <b>" + st.temperature.span.toFixed(2) + " °C</b>（标准差 " + st.temperature.std.toFixed(2) + "），均值 " + st.temperature.mean.toFixed(2) + " °C。" +
      "设计口径 20–26 °C：<b>" + C.t_in_band + " / " + C.n + "</b> 落入（全部略高于上沿）。湿度 40–60%：<b>" + C.rh_in_band + " / " + C.n + "</b>。" +
      "照度 ≥ 300 lx：<b>" + C.lux_ge_300 + " / " + C.n + "</b>；首五分钟 " + C.lux_ge_300_first5min + " / 30，末五分钟 " + C.lux_ge_300_last5min + " / 30。口径不是国标。";

    document.getElementById("proto").innerHTML =
      "周期 <b>SEQ=" + inn.seq[i] + "</b>　SRC=simulated　固件 " + S.meta.firmware_rev +
      "　<b>" + R.fmtClock(inn.times[i], true) + "</b>";

    const fields = document.getElementById("fields");
    if (fields) {
      fields.innerHTML =
        "<div>BME280_T_C <b>" + R.num(T, 2) + "</b></div>" +
        "<div>BME280_RH_PCT <b>" + R.num(H, 2) + "</b></div>" +
        "<div>BME280_P_HPA <b>" + R.num(P, 2) + "</b></div>" +
        "<div>BH1750_LUX <b>" + R.num(L, 1) + "</b></div>" +
        "<div>MQ135_INDEX <b>" + R.num(G, 2) + "</b></div>" +
        "<div>MCU_TS_C <b>" + R.num(M, 2) + "</b></div>";
    }
    const raw = S.usart.lines[i] || "";
    document.getElementById("usart").textContent = raw;

    document.getElementById("tips").innerHTML =
      "<li class='out'>温度 <b>0 / 181</b> 落入 20–26 °C，最低 26.18 °C，全部略高于上沿。这是设计口径，不是国标或实测房间结论。</li>" +
      "<li class='out'>照度后段偏弱：末五分钟均值约 <b>252 lx</b>，0 / 30 达到阅读线。若按此口径，可检查灯具或遮光——须待实机验证。</li>" +
      "<li class='ok'>相对湿度 <b>181 / 181</b> 落在 40–60%。</li>" +
      "<li>片内温度均值 <b>33.40 °C</b>，不能当作室内气温。MQ135 指数未标定，不是 ppm，不做浓度告警。</li>";
  }

  function setI(i) {
    state.i = Math.max(0, Math.min(n - 1, i | 0));
    renderTape();
    paint();
  }

  const svg = document.getElementById("tape");
  svg.addEventListener("pointerdown", (ev) => {
    state.dragging = true;
    try { svg.setPointerCapture(ev.pointerId); } catch (e) {}
    const r = svg.getBoundingClientRect();
    if (inv) setI(inv.invX(ev.clientX - r.left));
  });
  svg.addEventListener("pointermove", (ev) => {
    if (!state.dragging || !inv) return;
    const r = svg.getBoundingClientRect();
    setI(inv.invX(ev.clientX - r.left));
  });
  window.addEventListener("pointerup", () => { state.dragging = false; });
  window.addEventListener("keydown", (ev) => {
    if (ev.key === "ArrowLeft") { setI(state.i - 1); ev.preventDefault(); }
    if (ev.key === "ArrowRight") { setI(state.i + 1); ev.preventDefault(); }
  });

  document.querySelectorAll(".scene-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.scene = btn.getAttribute("data-scene");
      document.querySelectorAll(".scene-btn").forEach((b) => b.classList.toggle("is-on", b === btn));
      paint();
    });
  });

  function resize() { renderTape(); paint(); }
  window.addEventListener("resize", resize);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () {
    resize();
    requestAnimationFrame(resize);
  });
  resize();
  requestAnimationFrame(resize);
})();
