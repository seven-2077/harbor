#!/usr/bin/env python3
"""Visual QA screenshots for the Lumen B specimen. Uses system Chrome, file://."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("/workspace/research/bishe-night/lumen/b-sensing")
REV = ROOT / "review"
REV.mkdir(exist_ok=True)
INDEX = ROOT.joinpath("index.html").as_uri()
POSTER = ROOT.joinpath("poster.html").as_uri()
CHROME = "/usr/bin/google-chrome"


def wait_ready(page):
    page.wait_for_function(
        """() => {
          const svg = document.getElementById('tape');
          return !!(window.SPECIMEN && window.LumenB && svg && svg.querySelectorAll('rect').length > 10);
        }"""
    )
    page.evaluate("() => document.fonts && document.fonts.ready")
    page.wait_for_timeout(500)


def fonts_ok(page):
    return page.evaluate(
        """() => {
          const fams = [
            {family: 'IBM Plex Sans', weight: '400'},
            {family: 'Newsreader', weight: '400'},
            {family: 'Noto Serif SC', weight: '500'}
          ];
          return fams.map(f => ({
            family: f.family,
            check: document.fonts.check(f.weight + ' 16px "' + f.family + '"'),
            loaded: [...document.fonts].filter(x => x.family.replace(/['\"]/g,'') === f.family).map(x => x.status)
          }));
        }"""
    )


def shot_index(browser):
    page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=2)
    page.goto(INDEX, wait_until="load")
    wait_ready(page)
    print("fonts", fonts_ok(page))
    page.screenshot(path=str(REV / "index-1600x1000.png"), full_page=False)
    print("wrote index-1600x1000")

    page.set_viewport_size({"width": 1920, "height": 1080})
    page.wait_for_timeout(400)
    page.screenshot(path=str(REV / "index-1920x1080.png"), full_page=False)
    print("wrote index-1920x1080")

    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_timeout(400)
    page.screenshot(path=str(REV / "index-1440x900.png"), full_page=False)
    print("wrote index-1440x900")

    # switch to lab scene + late scrub
    page.set_viewport_size({"width": 1600, "height": 1000})
    page.wait_for_timeout(300)
    page.locator('button[data-scene="lab"]').click()
    box = page.evaluate(
        """() => {
          const svg = document.getElementById('tape');
          const r = svg.getBoundingClientRect();
          return {x: r.left + r.width * 0.86, y: r.top + r.height * 0.5};
        }"""
    )
    page.mouse.move(box["x"], box["y"])
    page.mouse.down()
    page.mouse.up()
    page.wait_for_timeout(250)
    page.screenshot(path=str(REV / "index-lab-scrub-late.png"), full_page=False)
    print("wrote index-lab-scrub-late")

    page.set_viewport_size({"width": 1280, "height": 800})
    page.wait_for_timeout(400)
    page.screenshot(path=str(REV / "index-1280x800.png"), full_page=False)
    page.screenshot(path=str(REV / "index-1280x800-full.png"), full_page=True)
    print("wrote index-1280")
    page.close()


def shot_poster(browser):
    page = browser.new_page(viewport={"width": 2400, "height": 3600}, device_scale_factor=1)
    page.goto(POSTER, wait_until="load")
    page.wait_for_function(
        """() => {
          const svg = document.getElementById('tape');
          return !!(window.SPECIMEN && window.LumenB && svg && svg.querySelectorAll('rect').length > 10);
        }"""
    )
    page.evaluate("() => document.fonts && document.fonts.ready")
    page.wait_for_timeout(700)
    print("poster fonts", fonts_ok(page))
    el = page.locator("#poster")
    el.screenshot(path=str(ROOT / "poster.png"))
    el.screenshot(path=str(REV / "poster-full.png"))
    page.pdf(
        path=str(ROOT / "poster.pdf"),
        width="2400px",
        height="3600px",
        print_background=True,
        margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
    )
    print("wrote poster.png and poster.pdf")
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
