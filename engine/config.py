"""Configuration: sources, ranking weights, hashtag map, branding."""

# RSS/Atom feeds. `weight` biases ranking toward more authoritative sources.
FEEDS = [
    {"name": "The Hacker News",   "url": "https://feeds.feedburner.com/TheHackersNews", "weight": 1.0},
    {"name": "BleepingComputer",  "url": "https://www.bleepingcomputer.com/feed/",       "weight": 1.0},
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/",            "weight": 1.2},
    {"name": "CISA Advisories",   "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml", "weight": 1.3},
    {"name": "Dark Reading",      "url": "https://www.darkreading.com/rss.xml",          "weight": 0.9},
    {"name": "Schneier on Security", "url": "https://www.schneier.com/feed/atom/",       "weight": 1.0},
]

# Only consider items published within this many hours (freshness window).
MAX_AGE_HOURS = 48

# How many stories to surface on the daily dashboard.
TOP_N = 3

# Keywords that boost a story's importance (lowercased, substring match).
IMPORTANCE_KEYWORDS = {
    "zero-day": 5, "zero day": 5, "0-day": 5, "actively exploited": 5,
    "ransomware": 4, "breach": 4, "data breach": 4, "critical": 4,
    "cve-": 3, "vulnerability": 3, "exploit": 3, "patch": 2, "phishing": 3,
    "malware": 3, "supply chain": 4, "backdoor": 4, "leak": 3, "spyware": 3,
    "mfa": 2, "passwordless": 2, "nation-state": 4, "apt": 3,
}

# Map detected topics -> hashtags (first match wins, plus the base tags).
HASHTAG_MAP = [
    (("ransom",), ["#Ransomware"]),
    (("phish",), ["#Phishing"]),
    (("cve-", "vulnerab", "exploit", "zero-day", "0-day", "patch"), ["#VulnManagement", "#PatchNow"]),
    (("breach", "leak"), ["#DataBreach"]),
    (("malware", "backdoor", "spyware", "trojan"), ["#Malware"]),
    (("mfa", "password", "identity", "authentication"), ["#IdentitySecurity"]),
    (("genai", "artificial intelligence", "chatgpt", "llm"), ["#AISecurity"]),
    (("cloud", "aws", "azure", "kubernetes"), ["#CloudSecurity"]),
]
BASE_HASHTAGS = ["#CyberSecurity", "#InfoSec"]

BRAND = {
    "name": "Kasspar Cyber Daily",
    "handle": "",                       # e.g. "@Kingnet256" -> appended to X posts if set
    "site": "kasspar.com",
    "teal": (11, 107, 114),             # #0B6B72
    "teal_dark": (8, 83, 90),           # #08535A
    "orange": (233, 162, 76),           # #E9A24C
    "cream": (244, 241, 234),           # #F4F1EA
}

# Titles/links matching these (lowercased substrings) are dropped as non-news
# (webinars, sponsored content, roundups, product marketing).
NOISE_PATTERNS = [
    "virtual event", "webinar", "[sponsored]", "sponsored:", "register now",
    "join us", "on-demand", "podcast", "newsletter", "weekly recap",
    "week in review", "deals", "coupon", "/events/", "cracking the code",
    "name that toon", "caption contest",
]
