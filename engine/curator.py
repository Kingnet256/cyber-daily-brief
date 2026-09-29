"""Rank stories and write per-platform post text (template-based)."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from engine import config


def _age_hours(published):
    if not published:
        return 999
    return (datetime.now(timezone.utc) - published).total_seconds() / 3600.0


def score(item: dict, feed_weight: float) -> float:
    text = f"{item['title']} {item['summary']}".lower()
    kw = sum(w for k, w in config.IMPORTANCE_KEYWORDS.items() if k in text)
    age = _age_hours(item.get("published"))
    recency = max(0.0, 1.0 - age / config.MAX_AGE_HOURS)   # 1.0 now -> 0 at window edge
    return kw + feed_weight * 2 + recency * 3


def rank(all_items: list[dict]) -> list[dict]:
    fresh = [it for it in all_items if _age_hours(it.get("published")) <= config.MAX_AGE_HOURS]
    pool = fresh or all_items                                # fall back if nothing "fresh"
    def _is_noise(it):
        blob = (it["title"] + " " + it.get("link", "")).lower()
        return any(n in blob for n in config.NOISE_PATTERNS)
    pool = [it for it in pool if not _is_noise(it)] or pool
    seen, unique = set(), []
    for it in pool:
        key = re.sub(r"\W+", "", it["title"].lower())[:60]
        if key in seen:
            continue
        seen.add(key)
        it["_score"] = score(it, it.get("_weight", 1.0))
        unique.append(it)
    unique.sort(key=lambda x: x["_score"], reverse=True)
    return _diversify(unique)


_STOP = {"the", "and", "for", "with", "from", "that", "this", "have", "are",
         "new", "two", "says", "said", "amid", "into", "over", "after", "flaws",
         "flaw", "bug", "bugs", "attack", "attacks", "critical", "vulnerability",
         "vulnerabilities", "exploit", "exploited", "exploiting", "exploitation",
         "zero", "hackers", "hacker", "attackers", "cyber", "cybersecurity",
         "security", "data", "breach", "malware", "ransomware", "actively",
         "under", "warning", "confirms", "confirmed", "globally", "million",
         "users", "flaw", "code", "remote", "unpatched"}


def _tokens(title: str) -> set:
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if len(w) > 3 and w not in _STOP}


def _diversify(items: list[dict], overlap: float = 0.34) -> list[dict]:
    """Greedily drop near-duplicate stories so picks cover distinct topics."""
    picked, picked_tok = [], []
    for it in items:
        tok = _tokens(it["title"])
        dup = any(tok and pt and (len(tok & pt) >= 2 or
                  len(tok & pt) / len(tok | pt) > overlap)
                  for pt in picked_tok)
        if dup:
            continue
        picked.append(it)
        picked_tok.append(tok)
    return picked


def hashtags_for(item: dict) -> list[str]:
    text = f"{item['title']} {item['summary']}".lower()
    tags = list(config.BASE_HASHTAGS)
    for triggers, htags in config.HASHTAG_MAP:
        if any(re.search(r"\b" + re.escape(t), text) for t in triggers):
            for h in htags:
                if h not in tags:
                    tags.append(h)
    return tags[:5]


def _trim(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(",.;:") + "…"


def _takeaway(item: dict) -> str:
    """A short defensive 'why it matters' line based on detected topic."""
    text = f"{item['title']} {item['summary']}".lower()
    rules = [
        (("ransomware",), "Back up offline and test restores — it's your real recovery plan."),
        (("phishing", "email"), "Slow down on urgent emails; verify the sender before you click."),
        (("cve-", "vulnerability", "zero-day", "0-day", "exploit", "patch"),
         "Patch affected systems promptly and confirm the fix actually applied."),
        (("breach", "leak"), "Assume reused passwords are exposed — rotate them and turn on MFA."),
        (("mfa", "password", "identity"), "Enable phishing-resistant MFA on email first; it protects everything else."),
        (("malware", "backdoor", "spyware", "trojan"),
         "Keep endpoints updated and don't run unexpected attachments or installers."),
    ]
    for triggers, msg in rules:
        if any(t in text for t in triggers):
            return msg
    return "Stay patched, use MFA, and think before you click."


X_LIMIT = 280
TCO = 23                                  # X wraps every URL to 23 chars


def make_x_post(item: dict) -> str:
    tags = " ".join(hashtags_for(item))
    handle = config.BRAND["handle"]
    tail = f"\n\n{tags}"
    if handle:
        tail += f"\nvia {handle}"
    url_cost = TCO + 2                     # URL + newline/space
    budget = X_LIMIT - len(tail) - url_cost
    hook = _trim(item["title"], budget)
    return f"{hook}{tail}\n{item['link']}"


def make_linkedin_post(item: dict) -> str:
    tags = " ".join(hashtags_for(item))
    summary = _trim(item["summary"] or item["title"], 320)
    takeaway = _takeaway(item)
    src = item.get("_source", "")
    return (
        f"\U0001F510 {item['title']}\n\n"
        f"{summary}\n\n"
        f"⚡ Why it matters: {takeaway}\n\n"
        f"\U0001F517 Read the full story ({src}): {item['link']}\n\n"
        f"{tags}"
    )
