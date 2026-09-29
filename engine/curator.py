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

# Topic-aware, human-sounding hooks. Several per topic so posts feel varied;
# the choice is seeded by the title so it's stable for a given story.
_HOOKS = {
    "vuln": ["\U0001F6A8 Zero-day alert:", "⚠️ Patch now:",
             "\U0001F6A8 Actively exploited:", "\U0001F6E0️ Heads up, admins:"],
    "breach": ["\U0001F513 Breach alert:", "⚠️ Data exposed:",
               "\U0001F4E2 Another breach:"],
    "ransom": ["\U0001F512 Ransomware:", "\U0001F480 Ransomware hit:"],
    "phish": ["\U0001F3A3 Phishing watch:", "\U0001F4E7 Scam alert:"],
    "malware": ["\U0001F9A0 Malware alert:", "⚠️ New malware:"],
    "default": ["\U0001F6E1️ Security update:", "\U0001F510 Heads up:",
                "\U0001F4F0 Today in cyber:"],
}

# Short, punchy "why you should care" lines (fit inside 280).
_WHY_SHORT = {
    "vuln": "Patch fast — attackers already are.",
    "breach": "Reused that password anywhere? Change it + turn on MFA.",
    "ransom": "Offline backups you've actually tested = your lifeline.",
    "phish": "Slow down on urgent messages before you click.",
    "malware": "Keep devices updated; don't run surprise files.",
    "default": "Stay patched, use MFA, think before you click.",
}


def _topic(item: dict) -> str:
    text = f"{item['title']} {item['summary']}".lower()
    for key, triggers in (
        ("ransom", ("ransom",)),
        ("phish", ("phish",)),
        ("vuln", ("cve-", "vulnerab", "zero-day", "0-day", "exploit", "patch", "rce")),
        ("breach", ("data breach", "breach", "leaked", "stolen data")),
        ("malware", ("malware", "backdoor", "spyware", "trojan", "botnet")),
    ):
        if any(t in text for t in triggers):
            return key
    return "default"


def _pick(options: list, seed: int):
    return options[seed % len(options)]


def _first_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    m = re.search(r"(.+?[.!?])(?:\s|$)", text)
    sent = m.group(1) if m else text
    return sent.strip()


def _lower_first(s: str) -> str:
    return s[:1].lower() + s[1:] if s and s[0].isupper() and not s[1:2].isupper() else s


def make_x_post(item: dict) -> str:
    """A natural, eye-catching 3-line post that always fits within 280 chars.

    hook (topic emoji)  /  what happened (plain language)  /  why you care
    + hashtags + link.  Trims the middle line to fit; drops the 'why' line
    only if space is very tight.
    """
    topic = _topic(item)
    seed = abs(hash(item["title"]))
    hook = _pick(_HOOKS[topic], seed)
    why = _WHY_SHORT[topic]
    tags = " ".join(hashtags_for(item)[:2])
    handle = config.BRAND["handle"]
    url = item["link"]

    what_full = _first_sentence(item["summary"]) or item["title"]
    # If the summary sentence is very long or missing, fall back to the title.
    if len(what_full) > 200 or len(what_full) < 15:
        what_full = item["title"]

    tail_tags = f"\n{tags}"
    if handle:
        tail_tags += f" · via {handle}"

    for include_why in (True, False):
        why_line = f"\n{why}" if include_why else ""
        # overhead = hook + newline + WHAT + why + tags + newline + url(23)
        overhead = len(hook) + 1 + len(why_line) + len(tail_tags) + 1 + TCO
        budget_what = X_LIMIT - overhead
        if budget_what >= (30 if include_why else 15):
            what = _trim(what_full, budget_what)
            return f"{hook} {what}{why_line}{tail_tags}\n{url}"

    # Absolute fallback: hook + trimmed title + link (guaranteed to fit).
    budget = X_LIMIT - len(hook) - 1 - 1 - TCO
    return f"{hook} {_trim(item['title'], max(20, budget))}\n{url}"


def make_linkedin_post(item: dict) -> dict:
    """Return {'body', 'first_comment'}.

    Best practice: keep the outbound link OUT of the post body (LinkedIn
    suppresses/flags link posts) and paste it as the first comment instead.
    """
    tags = " ".join(hashtags_for(item))
    summary = _trim(item["summary"] or item["title"], 400)
    takeaway = _takeaway(item)
    src = item.get("_source", "")
    topic = _topic(item)
    opener = {
        "vuln": "A vulnerability worth acting on today \U0001F447",
        "breach": "Another reminder to lock down your accounts \U0001F447",
        "ransom": "Ransomware is still winning where backups are weak \U0001F447",
        "phish": "Phishing keeps evolving — here's the latest \U0001F447",
        "malware": "New malware activity to be aware of \U0001F447",
        "default": "Today's cybersecurity read \U0001F447",
    }[topic]

    body = (
        f"\U0001F510 {item['title']}\n\n"
        f"{opener}\n\n"
        f"{summary}\n\n"
        f"⚡ Why it matters: {takeaway}\n\n"
        f"Are your systems covered? What's your team doing about this? \U0001F4AC\n\n"
        f"{tags}"
    )
    first_comment = f"\U0001F517 Source ({src}): {item['link']}"
    return {"body": body, "first_comment": first_comment}
