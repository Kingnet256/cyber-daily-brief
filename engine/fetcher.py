"""Fetch and parse RSS/Atom feeds using only the standard library."""
from __future__ import annotations

import html
import re
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

UA = "kasspar-cyber-daily/1.0 (+https://kasspar.com)"
_TAG = re.compile(r"<[^>]+>")


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = _TAG.sub(" ", text)          # strip HTML tags
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:                                 # RFC 822 (RSS pubDate)
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:                             # ISO 8601 (Atom updated/published)
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _text(el, *tags):
    for t in tags:
        found = el.find(t)
        if found is not None and (found.text or found.get("href")):
            return found.text or found.get("href")
    return None


def fetch_feed(url: str, timeout: float = 20.0) -> list[dict]:
    """Return a list of {title, link, summary, published} dicts."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    root = ET.fromstring(raw)

    # Namespace-agnostic: strip namespaces from tags so find() is simple.
    for el in root.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]

    items = []
    for node in root.iter():
        if node.tag not in ("item", "entry"):
            continue
        title = _clean(_text(node, "title"))
        link = _text(node, "link", "id")
        # Atom <link href="...">
        if not link:
            l = node.find("link")
            link = l.get("href") if l is not None else None
        summary = _clean(_text(node, "description", "summary", "content"))
        published = _parse_date(_text(node, "pubDate", "published", "updated", "date"))
        if title and link:
            items.append({"title": title, "link": link.strip(),
                          "summary": summary, "published": published})
    return items
