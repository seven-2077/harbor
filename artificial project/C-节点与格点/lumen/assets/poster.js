(function () {
  const S = window.SPECIMEN, R = window.LumenC;
  const inn = S.indoor, out = S.outdoor, C = inn.comfort_design;
  function go() {
    const mid = 90; // 12:15
    function pane(id, cfg) {
      const svg = document.getElementById(id);
      const r = svg.getBoundingClientRect();
      R.drawChannel(svg, Object.assign({
        w: r.width, h: r.height, times: inn.times, cursor: mid, digits: cfg.digits, scale: 2.4
      }, cfg));
    }
    pane("ch-temp", {
      series: inn.series.temperature, color: "#c4a07a",
      title: "CH  TEMP  °C   ·   推断的 BME280，模拟",
      ref: out.overlap.t, refLabel: "室外整点  25.8 °C",
      band: C.t_band, bandLabel: "设计口径 20–26 °C", digits: 1
    });
    pane("ch-rh", {
      series: inn.series.relative_humidity, color: "#7fa8a4",
      title: "CH  RH  %   ·   推断的 BME280，模拟",
      ref: out.overlap.rh, refLabel: "室外整点  49 %",
      band: C.rh_band, bandLabel: "设计口径 40–60 %", digits: 0
    });
    pane("ch-lux", {
      series: inn.series.illuminance, color: "#c8bd8e",
      title: "CH  LUX   ·   推断的 BH1750，模拟  ·  无室外对照通道",
      ref: 300, refLabel: "设计口径  阅读 300 lx", digits: 0
    });
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(go);
  else go();
})();
