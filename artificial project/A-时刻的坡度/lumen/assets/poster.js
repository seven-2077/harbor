(function () {
  const S = window.SPECIMEN;
  const R = window.LumenRender;
  const svg = document.getElementById("marey");
  function go() {
    const box = {
      w: svg.getBoundingClientRect().width,
      h: svg.getBoundingClientRect().height,
      pad: { t: 16, r: 20, b: 48, l: 280 }
    };
    const sc = R.scales(S, box);
    R.drawMarey(svg, S, sc);
    // slightly stronger typography already from pad; add 08:30 scrub as a quiet marker
    const byId = R.stationIndex(S);
    R.drawScrub(svg, 8 * 3600 + 30 * 60, sc, S, byId);
    // caption for the red line
    const g = svg.querySelector("g.scrub");
    const x = sc.x(8 * 3600 + 30 * 60);
    const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
    t.setAttribute("x", x + 6);
    t.setAttribute("y", sc.pad.t + 14);
    t.setAttribute("fill", "#c45a3a");
    t.setAttribute("font-size", "16");
    t.setAttribute("font-family", "IBM Plex Sans, Noto Serif SC, sans-serif");
    t.textContent = "08:30  设计取景（西向快车窗口内）";
    g.appendChild(t);
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(go);
  else go();
})();
