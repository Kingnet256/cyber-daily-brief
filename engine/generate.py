#!/usr/bin/env python3
"""
Kasspar Cyber Daily — build today's post dashboard + browsable archive.

Fetches curated cybersecurity feeds, ranks the day's top stories, writes
engaging X + LinkedIn post text and a branded image card for each, and
renders:
  - site/index.html                 today's dashboard (always the latest)
  - site/archive/<date>/index.html  a permanent snapshot of each day
  - site/archive/index.html         an index of every past day
  - site/archive.json               machine-readable history

Run: python3 -m engine.generate
"""
from __future__ import annotations

import html
import json
import os
import urllib.parse
from datetime import datetime, timezone

from engine import cardgen, config, curator
from engine.fetcher import fetch_feed

ROOT = os.path.dirname(os.path.dirname(__file__))
SITE = os.path.join(ROOT, "site")
ARCHIVE_DIR = os.path.join(SITE, "archive")
ARCHIVE_JSON = os.path.join(SITE, "archive.json")


def collect() -> list[dict]:
    items = []
    for feed in config.FEEDS:
        try:
            for it in fetch_feed(feed["url"]):
                it["_weight"] = feed["weight"]
                it["_source"] = feed["name"]
                items.append(it)
        except Exception as e:
            print(f"  ! {feed['name']} failed: {e}")
    print(f"  collected {len(items)} items from {len(config.FEEDS)} feeds")
    return items


def build_story(item: dict, idx: int, date_str: str, day_dir: str) -> dict:
    """Write the card into the day's folder and assemble post text."""
    card_name = f"card_{idx}.png"
    cardgen.make_card(item["title"], item.get("_source", ""), date_str,
                      os.path.join(day_dir, card_name))
    x_post = curator.make_x_post(item)
    li = curator.make_linkedin_post(item)
    x_intent = "https://x.com/intent/tweet?text=" + urllib.parse.quote(x_post)
    # X counts every URL as 23 chars (t.co), so the "real" length is shorter
    # than the raw string. Show the X-counted length in the UI.
    x_count = len(x_post) - len(item["link"]) + curator.TCO
    return {
        "title": item["title"], "source": item.get("_source", ""),
        "link": item["link"], "card": card_name,
        "x_post": x_post, "x_intent": x_intent, "x_count": x_count,
        "li_body": li["body"], "li_comment": li["first_comment"],
        "score": round(item.get("_score", 0), 1),
    }


def esc(s: str) -> str:
    return html.escape(s)


# --------------------------------------------------------------------------- #
#  HTML rendering
# --------------------------------------------------------------------------- #

STYLE = """
  :root {
    --teal:#0B6B72; --teal-d:#08535A; --orange:#E9A24C; --cream:#F4F1EA;
    --ink:#0d2a2c; --card:#ffffff; --muted:#5b6f70;
  }
  * { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  body { margin:0; font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    background:var(--cream); color:var(--ink);
    padding:env(safe-area-inset-top) 0 40px; }
  header { background:linear-gradient(135deg,var(--teal),var(--teal-d)); color:#fff;
    padding:26px 20px 22px; }
  header .wrap { max-width:680px; margin:0 auto; }
  header h1 { margin:0; font-size:20px; letter-spacing:.5px; }
  header p { margin:4px 0 0; color:#bfe3e5; font-size:14px; }
  header .nav { margin-top:10px; }
  header .nav a { color:#fff; background:rgba(255,255,255,.16); text-decoration:none;
    font-size:13px; font-weight:600; padding:6px 12px; border-radius:999px; }
  main { max-width:680px; margin:0 auto; padding:16px; }
  .card { background:var(--card); border-radius:16px; padding:16px; margin:16px 0;
    box-shadow:0 2px 14px rgba(8,83,90,.10); }
  .card.primary { border:2px solid var(--orange); }
  .badge { display:inline-block; font-size:11px; font-weight:700; letter-spacing:.8px;
    color:var(--teal-d); background:#e7f1f1; padding:5px 10px; border-radius:999px; }
  .thumb { width:100%; border-radius:12px; margin:12px 0; display:block; }
  h2 { font-size:18px; line-height:1.35; margin:6px 0 2px; }
  .src { color:var(--muted); font-size:13px; margin:0 0 6px; }
  .post { margin-top:14px; }
  .post-h { font-size:12px; font-weight:700; color:var(--muted); text-transform:uppercase;
    letter-spacing:.6px; display:flex; justify-content:space-between; }
  pre { white-space:pre-wrap; word-wrap:break-word; background:#f3f6f6; border:1px solid #e2ecec;
    border-radius:10px; padding:12px; font:14px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;
    margin:6px 0 10px; }
  .hint { font-size:12px; color:var(--muted); margin:2px 0 6px; }
  .btns { display:flex; gap:10px; flex-wrap:wrap; }
  .btn { flex:1 1 auto; text-align:center; text-decoration:none; border:0; cursor:pointer;
    padding:13px 14px; border-radius:12px; font-size:15px; font-weight:600; }
  .btn.x { background:#111; color:#fff; }
  .btn.li { background:#0a66c2; color:#fff; }
  .btn.ghost { background:#eef3f3; color:var(--teal-d); flex:0 0 auto; }
  .arc-list { list-style:none; padding:0; margin:0; }
  .arc-list li { background:var(--card); border-radius:12px; padding:14px 16px; margin:10px 0;
    box-shadow:0 1px 8px rgba(8,83,90,.08); }
  .arc-list a { color:var(--teal-d); font-weight:700; text-decoration:none; }
  .arc-list .titles { color:var(--muted); font-size:13px; margin-top:4px; }
  footer { text-align:center; color:var(--muted); font-size:13px; padding:24px 16px; }
  .toast { position:fixed; left:50%; bottom:28px; transform:translateX(-50%);
    background:var(--teal-d); color:#fff; padding:12px 18px; border-radius:12px;
    opacity:0; transition:opacity .2s; pointer-events:none; font-size:14px; }
  .toast.show { opacity:1; }
"""

SCRIPT = """
function toast(msg){var t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');
  clearTimeout(window._tt);window._tt=setTimeout(function(){t.classList.remove('show')},1600);}
function copyEl(id,btn,openUrl){
  var txt=document.getElementById(id).innerText;
  function done(){toast(openUrl?'Copied — paste into LinkedIn':'Copied to clipboard');
    if(openUrl) setTimeout(function(){window.open(openUrl,'_blank')},350);}
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(txt).then(done,function(){fallback(txt);done();});
  } else { fallback(txt); done(); }
}
function fallback(txt){var ta=document.createElement('textarea');ta.value=txt;
  ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);
  ta.focus();ta.select();try{document.execCommand('copy')}catch(e){}document.body.removeChild(ta);}
"""


def _page(title: str, head_sub: str, nav: str, body_main: str, icon: str) -> str:
    b = config.BRAND
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
<title>{esc(title)}</title>
<meta name="description" content="Your daily cybersecurity post, ready to review and share."/>
<meta name="theme-color" content="#0B6B72"/>
<link rel="apple-touch-icon" href="{esc(icon)}"/>
<style>{STYLE}</style>
</head>
<body>
<header><div class="wrap">
  <h1>\U0001F6E1️ {esc(b['name'])}</h1>
  <p>{head_sub}</p>
  <div class="nav">{nav}</div>
</div></header>
<main>
{body_main}
</main>
<footer>Auto-curated from trusted security sources. You approve every post.<br/>{esc(b['site'])}</footer>
<div id="toast" class="toast"></div>
<script>{SCRIPT}</script>
</body>
</html>"""


def render_dashboard(stories: list[dict], date_str: str, card_prefix: str, nav: str) -> str:
    cards_html = []
    for i, s in enumerate(stories):
        primary = " primary" if i == 0 else ""
        badge = "TODAY'S TOP STORY" if i == 0 else f"ALSO WORTH SHARING #{i}"
        cards_html.append(f"""
      <article class="card{primary}">
        <div class="badge">{esc(badge)}</div>
        <img class="thumb" src="{esc(card_prefix + s['card'])}" alt="headline card" loading="lazy"/>
        <h2>{esc(s['title'])}</h2>
        <p class="src">{esc(s['source'])}</p>

        <div class="post">
          <div class="post-h">X / Twitter <span>{s['x_count']}/280</span></div>
          <pre id="x{i}">{esc(s['x_post'])}</pre>
          <div class="btns">
            <a class="btn x" href="{esc(s['x_intent'])}" target="_blank" rel="noopener">Post to X ↗</a>
            <button class="btn ghost" onclick="copyEl('x{i}',this)">Copy</button>
          </div>
        </div>

        <div class="post">
          <div class="post-h">LinkedIn</div>
          <pre id="li{i}">{esc(s['li_body'])}</pre>
          <div class="btns">
            <button class="btn li" onclick="copyEl('li{i}',this,'https://www.linkedin.com/feed/?shareActive=true')">Copy &amp; open LinkedIn ↗</button>
            <button class="btn ghost" onclick="copyEl('li{i}',this)">Copy</button>
          </div>
          <p class="hint">✅ Tip: post the text above, then add the link below as the <b>first comment</b> (keeps reach up &amp; avoids spam flags).</p>
          <pre id="lc{i}">{esc(s['li_comment'])}</pre>
          <div class="btns">
            <button class="btn ghost" onclick="copyEl('lc{i}',this)">Copy link for first comment</button>
          </div>
        </div>
      </article>""")
    icon = card_prefix + (stories[0]["card"] if stories else "")
    return _page(config.BRAND["name"],
                 f"{esc(date_str)} — review, tweak if you like, then post.",
                 nav, "".join(cards_html), icon)


def render_archive_index(hist: list[dict], nav: str) -> str:
    items = []
    for entry in hist:
        date = entry["date"]
        titles = " · ".join(s["title"] for s in entry.get("stories", [])[:3])
        items.append(f"""
      <li>
        <a href="{esc(date)}/">{esc(date)}</a>
        <div class="titles">{esc(titles)}</div>
      </li>""")
    body = f'<ul class="arc-list">{"".join(items)}</ul>' if items else "<p>No archived days yet.</p>"
    icon = f"{hist[0]['date']}/card_0.png" if hist else ""
    return _page(f"Archive — {config.BRAND['name']}",
                 "Every past daily brief, kept for good.",
                 nav, body, icon)


# --------------------------------------------------------------------------- #

def main():
    now = datetime.now(timezone.utc)
    date_iso = now.strftime("%Y-%m-%d")
    date_str = now.strftime("%A, %d %B %Y")
    day_dir = os.path.join(ARCHIVE_DIR, date_iso)
    os.makedirs(day_dir, exist_ok=True)

    print("Fetching feeds...")
    items = collect()
    ranked = curator.rank(items)
    top = ranked[: config.TOP_N]
    if not top:
        print("No stories found; leaving previous dashboard in place.")
        return

    print(f"Building {len(top)} stories...")
    stories = [build_story(it, i, date_str, day_dir) for i, it in enumerate(top)]

    # Today's dashboard (cards live in the archive folder; reference them there)
    today_nav = '<a href="archive/">\U0001F4DA Archive</a>'
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_dashboard(stories, date_str, f"archive/{date_iso}/", today_nav))

    # Permanent snapshot for this day (cards are in the same folder)
    snap_nav = '<a href="../../">← Latest brief</a> &nbsp; <a href="../">\U0001F4DA Archive</a>'
    with open(os.path.join(day_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_dashboard(stories, date_str, "", snap_nav))

    # Update history, newest first, de-duplicating today's date
    hist = []
    if os.path.exists(ARCHIVE_JSON):
        try:
            hist = json.load(open(ARCHIVE_JSON, encoding="utf-8"))
        except Exception:
            hist = []
    hist = [h for h in hist if h.get("date") != date_iso]
    hist.insert(0, {"date": date_iso,
                    "stories": [{k: s[k] for k in ("title", "source", "link")} for s in stories]})
    hist = hist[:400]
    json.dump(hist, open(ARCHIVE_JSON, "w", encoding="utf-8"), indent=2)

    # Archive index page
    arc_nav = '<a href="../">← Latest brief</a>'
    with open(os.path.join(ARCHIVE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_archive_index(hist, arc_nav))

    print(f"Done. Top story: {stories[0]['title'][:70]}")
    print(f"Archived {len(hist)} day(s). Latest: site/index.html")


if __name__ == "__main__":
    main()
