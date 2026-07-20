"""Record live product sessions for the launch demo (Playwright, headless).

  PLAYWRIGHT_BROWSERS_PATH="/Volumes/SANDISK ELE/pw-browsers" \
  python -m scripts.record_session

Produces docs/devpost/_rec/{create,run,final,wall}.webm — real usage: a visible
cursor, live typing, tab navigation, hover-played takes, the final cut playing.
Read-only interactions only (never clicks Start production / Regen / takes).
"""
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
REC = Path("docs/devpost/_rec")

CURSOR_JS = """
(() => {
  function mount() {
    if (document.getElementById('__pwcur')) return;
    const c = document.createElement('div');
    c.id = '__pwcur';
    c.style.cssText = 'position:fixed;left:-40px;top:-40px;width:22px;height:22px;'
      + 'border-radius:50%;background:rgba(255,92,122,.92);border:2.5px solid #fff;'
      + 'box-shadow:0 0 16px rgba(255,92,122,.85);z-index:2147483647;pointer-events:none;'
      + 'transform:translate(-50%,-50%);transition:width .1s,height .1s';
    document.documentElement.appendChild(c);
    document.addEventListener('mousemove', e => {
      c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px';
    }, true);
    document.addEventListener('mousedown', () => {
      c.style.width = '32px'; c.style.height = '32px';
    }, true);
    document.addEventListener('mouseup', () => {
      c.style.width = '22px'; c.style.height = '22px';
    }, true);
  }
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
"""

BRIEF = "深夜便利店的女店员发现监控画面里的自己,正在做出她从未做过的动作"


def scene(pw, name, fn):
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080},
                              record_video_dir=str(REC / "raw"),
                              record_video_size={"width": 1920, "height": 1080})
    ctx.add_init_script(CURSOR_JS)
    page = ctx.new_page()
    fn(page)
    video = page.video
    ctx.close()
    path = Path(video.path())
    dest = REC / f"{name}.webm"
    shutil.move(path, dest)
    browser.close()
    print("recorded:", dest)


def sc_create(page):
    page.goto(f"{BASE}/?view=create")
    page.wait_for_timeout(1400)
    page.mouse.move(300, 300)
    box = page.locator("#brief").bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(cx, cy, steps=42)
    page.mouse.click(cx, cy)
    page.keyboard.press("Meta+a")
    page.keyboard.press("Backspace")
    page.wait_for_timeout(350)
    page.keyboard.type(BRIEF, delay=52)
    page.wait_for_timeout(900)
    # bump Scenes 4 -> 6: the estimate re-prices live
    sb = page.locator("#scenes").bounding_box()
    page.mouse.move(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2, steps=30)
    page.mouse.click(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2)
    page.keyboard.press("Meta+a")
    page.keyboard.type("6", delay=80)
    page.wait_for_timeout(1100)
    # glide to the estimate next to Start (do NOT click Start)
    st = page.locator("#go").bounding_box()
    page.mouse.move(st["x"] + st["width"] + 150, st["y"] + st["height"] / 2, steps=45)
    page.wait_for_timeout(1600)


def sc_run(page):
    page.goto(f"{BASE}/?run=20260706-023130&tab=bible")
    page.wait_for_timeout(2400)
    page.mouse.move(500, 500)
    tab = page.locator(".step .s", has_text="Production").first.bounding_box()
    page.mouse.move(tab["x"] + tab["width"] / 2, tab["y"] + tab["height"] / 2, steps=40)
    page.mouse.click(tab["x"] + tab["width"] / 2, tab["y"] + tab["height"] / 2)
    page.wait_for_timeout(1300)
    vid = page.locator(".card.shot video").first.bounding_box()
    page.mouse.move(vid["x"] + vid["width"] / 2, vid["y"] + vid["height"] / 2, steps=45)
    page.wait_for_timeout(4200)          # hover -> the take plays
    badge = page.locator(".qa").first.bounding_box()
    if badge:
        page.mouse.move(badge["x"] + 120, badge["y"] + badge["height"] / 2, steps=35)
    page.wait_for_timeout(2000)


def sc_final(page):
    page.goto(f"{BASE}/?run=20260706-110141&tab=final")
    page.wait_for_timeout(2200)
    page.mouse.move(500, 400)
    v = page.locator(".final video").first
    vb = v.bounding_box()
    page.mouse.move(vb["x"] + vb["width"] / 2, vb["y"] + vb["height"] / 2, steps=45)
    v.evaluate("el => { el.muted = true; el.play(); }")
    page.wait_for_timeout(9000)          # the drama plays, burned subs visible
    page.mouse.move(vb["x"] + vb["width"] + 220, vb["y"] + 120, steps=40)
    page.wait_for_timeout(1500)


def sc_wall(page):
    page.goto(f"{BASE}/?view=runs")
    page.wait_for_timeout(1600)
    page.mouse.move(300, 400)
    tiles = page.locator(".card.tile")
    n = min(tiles.count(), 4)
    for i in range(n):
        b = tiles.nth(i).bounding_box()
        page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] * 0.45, steps=26)
        page.wait_for_timeout(750)
    page.wait_for_timeout(800)


def main():
    (REC / "raw").mkdir(parents=True, exist_ok=True)
    todo = [("create", sc_create), ("run", sc_run),
            ("final", sc_final), ("wall", sc_wall)]
    with sync_playwright() as pw:
        for name, fn in todo:
            if not (REC / f"{name}.webm").exists():
                scene(pw, name, fn)
    shutil.rmtree(REC / "raw", ignore_errors=True)


if __name__ == "__main__":
    main()
