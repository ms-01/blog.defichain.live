import json
import html
import hashlib
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from html.parser import HTMLParser

root = Path.cwd()
out = root / "offline"
posts_dir = out / "posts"
media_dir = out / "media"

posts_dir.mkdir(parents=True, exist_ok=True)
media_dir.mkdir(parents=True, exist_ok=True)

posts = json.loads(
    (root / "all-posts.json").read_text(encoding="utf-8")
)
manifest = json.loads(
    (root / "media-manifest.json").read_text(encoding="utf-8")
)

media_map = {}
missing = []

for url, info in manifest.items():
    source = root / info["file"]
    if not source.is_file() or source.stat().st_size == 0:
        missing.append(url)
        continue

    data = source.read_bytes()
    ext = source.suffix.lower()

    # Dateityp anhand der Datei-Signatur korrigieren
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        ext = ".png"
    elif data.startswith(b"\xff\xd8\xff"):
        ext = ".jpg"
    elif data.startswith((b"GIF87a", b"GIF89a")):
        ext = ".gif"
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        ext = ".webp"

    target = media_dir / (source.stem + ext)
    if not target.exists():
        target.write_bytes(data)

    media_map[url] = "../media/" + target.name


def get_text(entry, key):
    value = entry.get(key, {})
    return value.get("$t", "") if isinstance(value, dict) else ""


def original_url(entry):
    for link in entry.get("link", []):
        if link.get("rel") == "alternate" and link.get("type") == "text/html":
            return link.get("href", "")
    return ""


class Rewriter(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        new = []
        for key, value in attrs:
            if value is not None:
                if key in ("src", "poster"):
                    value = media_map.get(value, value)
                elif key == "srcset":
                    items = []
                    for item in value.split(","):
                        fields = item.strip().split()
                        if fields:
                            fields[0] = media_map.get(fields[0], fields[0])
                            items.append(" ".join(fields))
                    value = ", ".join(items)

            if value is None:
                new.append(key)
            else:
                new.append(f'{key}="{html.escape(value, quote=True)}"')

        self.parts.append("<" + tag + (" " + " ".join(new) if new else "") + ">")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        self.parts.append(f"<!--{data}-->")


css = """
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif;
  background: #f6f7f9;
  color: #202733;
  line-height: 1.7;
}
header {
  background: #101b30;
  color: white;
  padding: 24px max(20px, calc((100% - 1000px)/2));
}
header a { color: white; text-decoration: none; }
main { max-width: 1000px; margin: 35px auto; padding: 0 20px; }
article, .entry {
  background: white;
  border-radius: 12px;
  padding: 26px;
  margin-bottom: 18px;
  overflow-wrap: anywhere;
}
a { color: #1674bd; }
h1 { line-height: 1.3; }
img, video, iframe { max-width: 100%; height: auto; }
pre { overflow-x: auto; }
.date { color: #687587; font-size: 14px; }
.entry a { text-decoration: none; }
footer { text-align: center; padding: 30px; color: #687587; }
"""

(out / "style.css").write_text(css, encoding="utf-8")

def page(title, content, prefix=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{prefix}style.css">
<link rel="stylesheet" href="{prefix}defichain-theme.css">
<link rel="icon" type="image/svg+xml" href="{prefix}assets/favicon.svg">
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="https://blog.defichain.live/" aria-label="DeFiChain Blog">
      <img src="{prefix}assets/dfi.png" alt="DeFiChain">
    </a>

  </div>
</header>
<main>{content}</main>
<footer class="blog-footer">
  <div class="footer-panel">
    <div class="footer-columns">
      <div class="footer-column">
        <h2>EXPLORE</h2>
        <a href="https://defichain.live/">DeFiChain.live</a>
        <a href="https://defichain.live/explore/dfi">$DFI</a>
        <a href="https://defichain.live/explore/masternodes">Masternodes</a>
      </div>
      <div class="footer-column">
        <h2>RESOURCES</h2>
        <a href="https://github.com/ms-01">GitHub</a>
        <a href="https://defiscan.live/">DeFiScan</a>
      </div>
      <div class="footer-column">
        <h2>COMMUNITY</h2>
        <a href="{prefix}index.html">Blog Archive</a>
        <a href="https://github.com/ms-01/defichain.live">Website Repository</a>
      </div>
    </div>
    <div class="footer-bottom">
      <a href="https://defichain.live/" aria-label="DeFiChain.live">
        <img src="{prefix}assets/dfi.png" alt="DeFiChain">
      </a>
      <p>
        Independent preservation of historical DeFiChain Blog content.
        Archived articles do not necessarily reflect the current state
        of the DeFiChain ecosystem.
      </p>
    </div>
  </div>
</footer>
</body>
</html>"""

entries = []
url_map = {}

for post in posts:
    title = get_text(post, "title") or "Untitled"
    date = get_text(post, "published")[:10]
    url = original_url(post)
    ident = get_text(post, "id")
    filename = hashlib.sha256(ident.encode()).hexdigest()[:20] + ".html"

    url_map[url] = filename
    entries.append((post, title, date, url, filename))


blog_hero = """
<section class="blog-hero" aria-label="Blog introduction">
  <p class="hero-label">NEWS &amp; COMMUNITY</p>
  <h1 class="visually-hidden">DeFiChain Blog</h1>
  <img class="blog-hero-banner"
       src="assets/blog-header-original.jpg"
       alt="DeFiChain Blog"
       width="1440"
       height="536">
  <div class="blog-hero-details">
    <p class="hero-description">
      News, announcements and developments from the DeFiChain ecosystem.
    </p>
    <p class="archive-count">213 archived articles · Historical archive</p>
  </div>
</section>

<section class="blog-features" aria-label="DeFiChain topics">
  <div class="feature">
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <rect x="12" y="12" width="34" height="34" fill="none" stroke="#888"/>
      <rect x="20" y="20" width="34" height="34" fill="none" stroke="#888"/>
      <rect x="12" y="36" width="14" height="10" fill="#ff00af"/>
    </svg>
    <span>NEWS</span>
    <small>Community &amp; Updates</small>
  </div>

  <div class="feature">
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <circle cx="29" cy="32" r="20" fill="none" stroke="#ff00af"/>
      <circle cx="37" cy="32" r="20" fill="none" stroke="#888"/>
      <circle cx="42" cy="32" r="14" fill="none" stroke="#888"/>
    </svg>
    <span>SECURITY</span>
    <small>Safety &amp; Incidents</small>
  </div>

  <div class="feature">
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <path d="M8 24L32 13L56 24L32 35Z" fill="#b000d8"/>
      <path d="M8 35L32 24L56 35L32 46Z" fill="none" stroke="#888"/>
      <path d="M8 46L32 35L56 46L32 57Z" fill="none" stroke="#888"/>
    </svg>
    <span>TECHNOLOGY</span>
    <small>Protocol &amp; Tokenomics</small>
  </div>

  <div class="feature">
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <path d="M8 18L32 55L56 18Z" fill="none" stroke="#888"/>
      <path d="M16 18L40 55L56 18Z" fill="none" stroke="#888"/>
      <path d="M28 18H56L42 43Z" fill="#ff00af"/>
    </svg>
    <span>DEVELOPMENT</span>
    <small>Software &amp; Tools</small>
  </div>
</section>

<h2 class="articles-heading">Latest articles</h2>
"""


# Reuse the four original SVG designs from the existing blog hero.
import re
from collections import defaultdict

icon_blocks = re.findall(
    r'<div class="feature">\s*(<svg.*?</svg>)\s*<span>(NEWS|SECURITY|TECHNOLOGY|DEVELOPMENT)</span>',
    blog_hero,
    flags=re.DOTALL,
)

icons = {category: svg for svg, category in icon_blocks}

if len(icons) != 4:
    raise RuntimeError("Expected four SVG category icons in blog_hero")


def classify_article(title, content):
    text = (title + " " + re.sub(r"<[^>]+>", " ", content)).lower()

    categories = {
        "SECURITY": [
            "security", "exploit", "vulnerability",
            "bug bounty", "attack", "hack", "incident",
        ],
        "DEVELOPMENT": [
            "developer", "development", "sdk", "api",
            "release", "hardfork", "hard fork", "github",
            "software update",
        ],
        "TECHNOLOGY": [
            "tokenomics", "blockchain", "consensus",
            "liquidity", "decentralized exchange",
            "dex", "smart contract", "masternode",
            "staking", "protocol",
        ],
    }

    title_lower = title.lower()
    scores = {}

    for category, keywords in categories.items():
        scores[category] = sum(
            5 * title_lower.count(keyword) + text.count(keyword)
            for keyword in keywords
        )

    category = max(scores, key=scores.get)
    return category if scores[category] > 0 else "NEWS"


def article_entry(title, date, filename, category):
    return (
        '<div class="entry archive-entry">'
        f'<span class="archive-entry-icon" aria-hidden="true">{icons[category]}</span>'
        '<div class="archive-entry-content">'
        f'<div class="date">{html.escape(date)}</div>'
        f'<a href="posts/{html.escape(filename, quote=True)}">'
        f'<strong>{html.escape(title)}</strong></a>'
        f'<div class="archive-category">{category}</div>'
        '</div></div>'
    )


# Load editorial categories from the maintained JSON file.
category_file = Path(__file__).with_name("article-categories.json")
category_records = json.loads(category_file.read_text(encoding="utf-8"))

valid_categories = {"NEWS", "SECURITY", "TECHNOLOGY", "DEVELOPMENT"}

category_map = {}

for record in category_records:
    article_id = record["id"]
    category = record["category"]

    if article_id in category_map:
        raise RuntimeError(f"Duplicate article ID: {article_id}")

    if category not in valid_categories:
        raise RuntimeError(f"Invalid category: {category}")

    category_map[article_id] = category

if len(category_map) != len(entries):
    raise RuntimeError(
        f"Category count mismatch: {len(category_map)} vs {len(entries)}"
    )

# Sort all articles by publication date, newest first.
entries.sort(key=lambda item: item[2], reverse=True)

index_parts = [
    blog_hero.replace(
        "213 archived articles",
        f"{len(posts)} archived articles"
    )
]

archive_by_year = defaultdict(list)

for index, (post, title, date, url, filename) in enumerate(entries):
    parser = Rewriter()
    parser.feed(get_text(post, "content"))
    content = "".join(parser.parts)

    # Preserve the existing local article-link rewriting.
    for original, local in url_map.items():
        if original:
            content = content.replace(
                html.escape(original, quote=True),
                html.escape(local, quote=True)
            )
            content = content.replace(original, local)

    source_link = (
        f'<p class="date">Original: '
        f'<a href="{html.escape(url, quote=True)}">'
        f'{html.escape(url)}</a></p>'
    ) if url else ""

    article = (
        '<nav class="article-back-nav" aria-label="Article navigation">'
        '<a href="../index.html">← Back to Blog</a>'
        '</nav>'
        f'<article><h1>{html.escape(title)}</h1>'
        f'<p class="date">{html.escape(date)}</p>'
        f'{content}{source_link}</article>'
    )

    (posts_dir / filename).write_text(
        page(title, article, "../"),
        encoding="utf-8"
    )

    category = category_map.get(get_text(post, "id"))
    if category is None:
        raise RuntimeError(f"Missing editorial category: {title}")
    card = article_entry(title, date, filename, category)

    if index < 3:
        index_parts.append(card)
    else:
        archive_by_year[date[:4]].append(card)

index_parts.append('<section class="year-archive">')
index_parts.append('<h2>Article archive</h2>')
index_parts.append(
    '<p class="archive-intro">Browse historical articles by year.</p>'
)

for year in sorted(archive_by_year, reverse=True):
    cards = archive_by_year[year]
    index_parts.append(
        '<details class="archive-year">'
        f'<summary><span>{html.escape(year)}</span>'
        f'<span class="archive-year-count">{len(cards)} articles</span>'
        '</summary>'
        '<div class="archive-year-entries">'
        + "\n".join(cards)
        + '</div></details>'
    )

index_parts.append('</section>')

(out / "index.html").write_text(
    page("DeFiChain Blog Archive", "\n".join(index_parts)),
    encoding="utf-8"
)

print("=== OFFLINE-ARCHIV ERSTELLT ===")
print("Artikel:", len(entries))
print("Lokale Medien:", len(media_map))
print("Fehlende Medien:", len(missing))
print("Startseite:", out / "index.html")

if missing:
    (out / "missing-media.txt").write_text(
        "\n".join(missing), encoding="utf-8"
    )
