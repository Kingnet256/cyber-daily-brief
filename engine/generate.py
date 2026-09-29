#!/usr/bin/env python3
"""
Kasspar Cyber Daily — build today's post dashboard.

Fetches curated cybersecurity feeds, ranks the day's top stories, writes
X + LinkedIn post text and a branded image card for each, and renders a
mobile-friendly dashboard (site/index.html) plus a JSON archive.

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
IMG_DIR = os.path.join(SITE, "cards")


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


def build_story(item: dict, idx: int, date_str: str) -> dict:
    card_rel = f"cards/card_{idx}.png"
    cardgen.make_card(item["title"], item.get("_source", ""), date_str,
                      os.path.join(SITE, card_rel))
    x_post = curator.make_x_post(item)
    li_post = curator.make_linkedin_post(item)
    x_intent = "https://x.com/intent/tweet?text=" + urllib.parse.quote(x_post)
    return {
        "title": item["title"], "source": item.get("_source", ""),
        "link": item["link"], "card": card_rel,
        "x_post": x_post, "x_intent": x_intent,
        "linkedin_post": li_post, "score": round(item.get("_score", 0), 1),
    }


def esc(s: str) -> str:
    return html.escape(s)


def render_html(stories: list[dict], date_str: str) -> str:
    b = config.BRAND
    cards_html = []
    for i, s in enumerate(stories):
        primary = " primary" if i == 0 else ""
        badge = "TODAY'S TOP STORY" if i == 0 else f"ALSO WORTH SHARING #{i}"
        cards_html.append(f"""
      <article class="card{primary}">
        <div class="badge">{esc(badge)}</div>
        <img class="thumb" src="{esc(s['card'])}" alt="headline card" loading="lazy"/>
        <h2>{esc(s['title'])}</h2>
        <p class="src">{esc(s['source'])}</p>

        <div class="post">
          <div class="post-h">X / Twitter <span>{len(s['x_post'])}/280</span></div>
          <pre id="x{i}">{esc(s['x_post'])}</pre>
          <div class="btns">
            <a class="btn x" href="{esc(s['x_intent'])}" target="_blank" rel="noopener">Post to X ↗</a>
            <button class="btn ghost" onclick="copyEl('x{i}',this)">Copy</button>
          </div>
        </div>

        <div class="post">
          <div class="post-h">LinkedIn</div>
          <pre id="li{i}">{esc(s['linkedin_post'])}</pre>
          <div class="btns">
            <button class="btn li" onclick="copyEl('li{i}',this,'https://www.linkedin.com/feed/?shareActive=true')">Copy &amp; open LinkedIn ↗</button>
            <button class="btn ghost" onclick="copyEl('li{i}',this)">Copy</button>
          </div>
        </div>
      </article>""")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
<title>{esc(b['name'])}</title>
<meta name="description" content="Your daily cybersecurity post, ready to review and share."/>
<meta name="theme-color" content="#0B6B72"/>
<link rel="apple-touch-icon" href="cards/card_0.png"/>
<style>
  :root {{
    --teal:#0B6B72; --teal-d:#08535A; --orange:#E9A24C; --cream:#F4F1EA;
    --ink:#0d2a2c; --card:#ffffff; --muted:#5b6f70;
  }}
  * {{ box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
  body {{ margin:0; font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    background:var(--cream); color:var(--ink);
    padding:env(safe-area-inset-top) 0 40px; }}
  header {{ background:linear-gradient(135deg,var(--teal),var(--teal-d)); color:#fff;
    padding:26px 20px 22px; }}
  header .wrap {{ max-width:680px; margin:0 auto; }}
  header h1 {{ margin:0; font-size:20px; letter-spacing:.5px; }}
  header p {{ margin:4px 0 0; color:#bfe3e5; font-size:14px; }}
  main {{ max-width:680px; margin:0 auto; padding:16px; }}
  .card {{ background:var(--card); border-radius:16px; padding:16px; margin:16px 0;
    box-shadow:0 2px 14px rgba(8,83,90,.10); }}
  .card.primary {{ border:2px solid var(--orange); }}
  .badge {{ display:inline-block; font-size:11px; font-weight:700; letter-spacing:.8px;
    color:var(--teal-d); background:#e7f1f1; padding:5px 10px; border-radius:999px; }}
  .thumb {{ width:100%; border-radius:12px; margin:12px 0; display:block; }}
  h2 {{ font-size:18px; line-height:1.35; margin:6px 0 2px; }}
  .src {{ color:var(--muted); font-size:13px; margin:0 0 6px; }}
  .post {{ margin-top:14px; }}
  .post-h {{ font-size:12px; font-weight:700; color:var(--muted); text-transform:uppercase;
    letter-spacing:.6px; display:flex; justify-content:space-between; }}
  pre {{ white-space:pre-wrap; word-wrap:break-word; background:#f3f6f6; border:1px solid #e2ecec;
    border-radius:10px; padding:12px; font:14px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;
    margin:6px 0 10px; }}
  .btns {{ display:flex; gap:10px; flex-wrap:wrap; }}
  .btn {{ flex:1 1 auto; text-align:center; text-decoration:none; border:0; cursor:pointer;
    padding:13px 14px; border-radius:12px; font-size:15px; font-weight:600; }}
  .btn.x {{ background:#111; color:#fff; }}
  .btn.li {{ background:#0a66c2; color:#fff; }}
  .btn.ghost {{ background:#eef3f3; color:var(--teal-d); flex:0 0 auto; }}
  footer {{ text-align:center; color:var(--muted); font-size:13px; padding:24px 16px; }}
  .toast {{ position:fixed; left:50%; bottom:28px; transform:translateX(-50%);
    background:var(--teal-d); color:#fff; padding:12px 18px; border-radius:12px;
    opacity:0; transition:opacity .2s; pointer-events:none; font-size:14px; }}
  .toast.show {{ opacity:1; }}
</style>
</head>
<body>
<header><div class="wrap">
  <h1>\U0001F6E1️ {esc(b['name'])}</h1>
  <p>{esc(date_str)} — review, tweak if you like, then post.</p>
</div></header>
<main>
{''.join(cards_html)}
</main>
<footer>Auto-curated from trusted security sources. You approve every post.<br/>{esc(b['site'])}</footer>
<div id="toast" class="toast"></div>
<script>
function toast(msg){{var t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');
  clearTimeout(window._tt);window._tt=setTimeout(function(){{t.classList.remove('show')}},1600);}}
function copyEl(id,btn,openUrl){{
  var txt=document.getElementById(id).innerText;
  function done(){{toast(openUrl?'Copied — paste into LinkedIn':'Copied to clipboard');
    if(openUrl) setTimeout(function(){{window.open(openUrl,'_blank')}},350);}}
  if(navigator.clipboard&&navigator.clipboard.writeText){{
    navigator.clipboard.writeText(txt).then(done,function(){{fallback(txt);done();}});
  }} else {{ fallback(txt); done(); }}
}}
function fallback(txt){{var ta=document.createElement('textarea');ta.value=txt;
  ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);
  ta.focus();ta.select();try{{document.execCommand('copy')}}catch(e){{}}document.body.removeChild(ta);}}
</script>
</body>
</html>"""


def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%A, %d %B %Y")

    print("Fetching feeds...")
    items = collect()
    ranked = curator.rank(items)
    top = ranked[: config.TOP_N]
    if not top:
        print("No stories found; leaving previous dashboard in place.")
        return

    print(f"Building {len(top)} stories...")
    stories = [build_story(it, i, date_str) for i, it in enumerate(top)]

    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_html(stories, date_str))

    archive = os.path.join(SITE, "archive.json")
    hist = []
    if os.path.exists(archive):
        try:
            hist = json.load(open(archive, encoding="utf-8"))
        except Exception:
            hist = []
    hist.insert(0, {"date": now.strftime("%Y-%m-%d"),
                    "stories": [{k: s[k] for k in ("title", "source", "link")} for s in stories]})
    json.dump(hist[:120], open(archive, "w", encoding="utf-8"), indent=2)

    print(f"Done. Top story: {stories[0]['title'][:70]}")
    print(f"Wrote {os.path.join(SITE, 'index.html')}")


if __name__ == "__main__":
    main()
