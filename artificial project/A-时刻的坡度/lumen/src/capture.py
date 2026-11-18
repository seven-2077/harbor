#!/usr/bin/env python3
"""Visual QA screenshots for the Lumen specimen. Uses system Chrome."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("/workspace/research/bishe-night/lumen")
REV = ROOT / "review"
REV.mkdir(exist_ok=True)
INDEX = ROOT.joinpath("index.html").as_uri()
POSTER = ROOT.joinpath("poster.html").as_uri()
CHROME = "/usr/bin/google-chrome"


def wait_ready(page):
    page.wait_for_function("() => window.SPECIMEN && window.LumenRender && document.getElementById('marey') && document.getElementById('marey').querySelectorAll('path.trip').length > 100")
    page.evaluate("() => document.fonts && document.fonts.ready")
    page.wait_for_timeout(400)


def shot_index(browser):
    page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=2)
    page.goto(INDEX, wait_until="load")
    wait_ready(page)
    page.screenshot(path=str(REV / "index-1600x1000.png"), full_page=False)
    print("wrote index-1600x1000")

    # 1920x1080
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.wait_for_timeout(300)
    page.screenshot(path=str(REV / "index-1920x1080.png"), full_page=False)
    print("wrote index-1920x1080")

    # 1440x900
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_timeout(300)
    page.screenshot(path=str(REV / "index-1440x900.png"), full_page=False)
    print("wrote index-1440x900")

    # hover a westbound express near 08:30
    page.set_viewport_size({"width": 1600, "height": 1000})
    page.wait_for_timeout(300)
    handle = page.evaluate("""() => {
      const svg = document.getElementById('marey');
      const hits = [...svg.querySelectorAll('path.hit')];
      const S = window.SPECIMEN;
      const trip = S.trips.find(t => t.route === '7X' && t.dir === 1);
      if (!trip) return null;
      const el = hits.find(h => h.getAttribute('data-id') === trip.id);
      if (!el) return null;
      const len = el.getTotalLength();
      const pt = el.getPointAtLength(len * 0.35);
      const ctm = el.getScreenCTM();
      const sx = ctm.a * pt.x + ctm.c * pt.y + ctm.e;
      const sy = ctm.b * pt.x + ctm.d * pt.y + ctm.f;
      return {x: sx, y: sy, id: trip.id};
    }""")
    if handle:
        page.mouse.move(handle["x"], handle["y"])
        page.wait_for_timeout(250)
        page.screenshot(path=str(REV / "index-hover-express.png"), full_page=False)
        print("wrote index-hover-express", handle["id"])

    # click Flushing station label
    loc = page.locator("text[data-station='701']")
    if loc.count():
        loc.first.click()
        page.wait_for_timeout(250)
        page.screenshot(path=str(REV / "index-station-flushing.png"), full_page=False)
        print("wrote index-station-flushing")

    # later evening time scrub 17:30
    page.evaluate("""() => {
      const ev = new PointerEvent('pointerdown', {bubbles:true, clientX: 0, clientY: 0});
    }""")
    # compute x of 17:30 and click the chart
    pos = page.evaluate("""() => {
      const svg = document.getElementById('marey');
      const r = svg.getBoundingClientRect();
      // 17.5h / 26h of plot width; pad l=158, r=10
      const padL = 158, padR = 10;
      const x = r.left + padL + ((17.5*3600)/ (26*3600)) * (r.width - padL - padR);
      const y = r.top + r.height * 0.5;
      return {x, y};
    }""")
    page.mouse.click(pos["x"], pos["y"])
    page.wait_for_timeout(250)
    page.screenshot(path=str(REV / "index-scrub-1730.png"), full_page=False)
    print("wrote index-scrub-1730")
    page.close()


def shot_poster(browser):
    page = browser.new_page(viewport={"width": 2400, "height": 3600}, device_scale_factor=1)
    page.goto(POSTER, wait_until="load")
    page.wait_for_function("() => document.getElementById('marey') && document.getElementById('marey').querySelectorAll('path.trip').length > 100")
    page.evaluate("() => document.fonts && document.fonts.ready")
    page.wait_for_timeout(600)
    # clip to the poster artboard
    el = page.locator("#poster")
    el.screenshot(path=str(ROOT / "poster.png"))
    el.screenshot(path=str(REV / "poster-full.png"))
    page.pdf(path=str(ROOT / "poster.pdf"), width="2400px", height="3600px", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    print("wrote poster.png and poster.pdf")
    # detail crops
    page.screenshot(path=str(REV / "poster-top.png"), clip={"x": 0, "y": 0, "width": 2400, "height": 1400})
    page.screenshot(path=str(REV / "poster-mid.png"), clip={"x": 0, "y": 1100, "width": 2400, "height": 1400})
    page.screenshot(path=str(REV / "poster-bottom.png"), clip={"x": 0, "y": 2200, "width": 2400, "height": 1400})
    print("wrote poster crops")
    page.close()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=["--allow-file-access-from-files"])
        shot_index(browser)
        shot_poster(browser)
        browser.close()


if __name__ == "__main__":
    main()
