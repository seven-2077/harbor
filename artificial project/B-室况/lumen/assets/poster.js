(function () {
  const S = window.SPECIMEN, R = window.LumenB;
  const inn = S.indoor, C = inn.comfort_design, mid = 90;
  function go() {
    const svg = document.getElementById("tape");
    const r = svg.getBoundingClientRect();
    R.drawTape(svg, {
      w: r.width, h: r.height, times: inn.times, cursor: mid, comfort: C, scale: 2.2,
      lanes: [
        { kind: "t", label: "温度", series: inn.series.temperature, spark: true },
        { kind: "rh", label: "湿度", series: inn.series.relative_humidity, spark: true },
        { kind: "lux", label: "照度", series: inn.series.illuminance, spark: true }
      ]
    });
    const T = inn.series.temperature[mid], H = inn.series.relative_humidity[mid];
    const P = inn.series.pressure[mid], L = inn.series.illuminance[mid];
    const G = inn.series.gas_index[mid], M = inn.series.mcu_temperature[mid];
    document.getElementById("fields").innerHTML =
      "<div>BME280_T_C <b>" + R.num(T, 2) + "</b></div>" +
      "<div>BME280_RH_PCT <b>" + R.num(H, 2) + "</b></div>" +
      "<div>BME280_P_HPA <b>" + R.num(P, 2) + "</b></div>" +
      "<div>BH1750_LUX <b>" + R.num(L, 1) + "</b></div>" +
      "<div>MQ135_INDEX <b>" + R.num(G, 2) + "</b></div>" +
      "<div>MCU_TS_C <b>" + R.num(M, 2) + "</b></div>";
    document.getElementById("usartLine").textContent = S.usart.lines[mid];
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(go);
  else go();
})();
