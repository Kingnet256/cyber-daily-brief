# Kasspar Cyber Daily

An automated engine that turns the day's top cybersecurity news into a
**ready-to-post X + LinkedIn brief**, published every morning to a
mobile-friendly page you open on your phone, review, and post with a tap.

> The goal: keep people aware and updated on security — one clean, credible
> post per day, with **you** approving every single one before it goes out.

## How it works

```
 RSS feeds ──▶ rank & de-dupe ──▶ write posts ──▶ branded image card ──▶ dashboard
 (THN, CISA,      (freshness +      (X ≤280 +       (1200×675 PNG)        (site/index.html)
  Krebs, …)        importance)       LinkedIn)
```

1. **Fetch** — pulls curated feeds (The Hacker News, BleepingComputer,
   Krebs on Security, CISA advisories, Dark Reading, Schneier). Standard
   library only, no API keys.
2. **Curate** — ranks by freshness, source authority, and importance
   keywords (zero-day, actively exploited, ransomware, breach…); drops
   webinars/sponsored noise; de-duplicates so the picks are distinct stories.
3. **Write** — per-platform templates: a ≤280-char X post and a longer,
   professional LinkedIn post, each with a defensive "why it matters" line
   and relevant hashtags.
4. **Illustrate** — generates an on-brand headline card for each story.
5. **Publish** — renders `site/index.html`, a phone-first dashboard.

## Posting from your phone

Open the dashboard on your iPhone (add it to your Home Screen for one-tap access):

- **Post to X** → opens the X app with your post **pre-filled**. Read it,
  tweak if you like, post. ✅
- **Copy & open LinkedIn** → copies the post to your clipboard and opens
  LinkedIn, where you paste and post.
  *(LinkedIn no longer lets links pre-fill post text — spam prevention — so
  copy-and-paste is the best any tool can do there.)*

**You review and confirm every post. Nothing is ever posted automatically.**

## Automation

`.github/workflows/daily.yml` runs every morning (06:00 UTC), regenerates
the brief, and deploys it to **GitHub Pages**. You can also trigger it
manually from the Actions tab ("Run workflow").

## Run it locally

```bash
pip install -r requirements.txt
python -m engine.generate
# open site/index.html in a browser
```

## Configure

Everything lives in [`engine/config.py`](engine/config.py): feeds and their
weights, freshness window, number of stories, importance keywords, hashtag
mapping, noise filters, and branding colors. Set `BRAND["handle"]` to your
`@handle` to append "via @you" to X posts.

## License

MIT — see [LICENSE](LICENSE). News content belongs to the linked publishers;
this tool links to them and never republishes their articles in full.
