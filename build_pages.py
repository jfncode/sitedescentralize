#!/usr/bin/env python3
"""
Build multi-page site from SPA index.html.

Output:
  /artigos/<slug>.html  — one page per <article class="article-full">
  /sobre.html
  /politica-privacidade.html
  /contato.html
  /termos.html
  /aviso-legal.html
  /sitemap.xml          — regenerated with all URLs
"""

from __future__ import annotations
import re
import shutil
from pathlib import Path
from datetime import date
from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).parent
SRC = ROOT / "index.html"
ARTIGOS_DIR = ROOT / "artigos"
SITE_URL = "https://descentralize.com.br"
TODAY = date.today().isoformat()

HEADER_NAV_REWRITES = {
    "#home": "/",
    "#blog": "/#blog",
    "#ferramentas": "/#ferramentas",
    "#sobre": "/sobre.html",
    "#contato": "/contato.html",
    "#privacidade": "/politica-privacidade.html",
    "#termos": "/termos.html",
    "#aviso-legal": "/aviso-legal.html",
}


def rewrite_header_links(header_soup):
    for a in header_soup.find_all("a"):
        href = a.get("href", "")
        if href in HEADER_NAV_REWRITES:
            a["href"] = HEADER_NAV_REWRITES[href]
    return header_soup


def rewrite_internal_article_links(content_soup):
    """Transform '#post-X-completo' anchors into '/artigos/<slug>.html' URLs."""
    for a in content_soup.find_all("a"):
        href = a.get("href", "")
        if not href.startswith("#post-"):
            continue
        anchor_id = href[1:]
        slug = slug_from_article_id(anchor_id)
        if slug:
            a["href"] = f"/artigos/{slug}.html"
    return content_soup


SLUG_OVERRIDES = {
    "post-aave-kelp-completo": "aave-kelp-hack",
    "post-ir-completo": "ir-cripto",
    "post-stablecoins-completo": "stablecoins-br",
    "post-seguranca-completo": "seguranca-cripto",
}

SECTION_PAGES = {
    "sobre": ("sobre.html", "Sobre — Descentralize", "Quem é Jefferson Tavares e por que o Descentralize existe."),
    "privacidade": ("politica-privacidade.html", "Política de Privacidade — Descentralize", "Como tratamos dados pessoais e cookies no Descentralize."),
    "contato": ("contato.html", "Contato — Descentralize", "Fale com Jefferson Tavares: e-mail, redes sociais e parcerias."),
    "termos": ("termos.html", "Termos de Uso — Descentralize", "Termos de uso do site Descentralize."),
    "aviso-legal": ("aviso-legal.html", "Aviso Legal — Descentralize", "Aviso legal sobre o conteúdo educacional do Descentralize."),
}


def slug_from_article_id(article_id: str) -> str:
    if article_id in SLUG_OVERRIDES:
        return SLUG_OVERRIDES[article_id]
    s = re.sub(r"^post-", "", article_id)
    s = re.sub(r"-completo$", "", s)
    return s


def extract_title(article: Tag) -> str:
    h2 = article.find("h2")
    return h2.get_text(strip=True) if h2 else "Artigo"


def extract_description(article: Tag) -> str:
    p = article.find("p")
    if not p:
        return ""
    txt = p.get_text(" ", strip=True)
    return (txt[:155] + "...") if len(txt) > 155 else txt


def extract_category(article: Tag) -> str:
    cat = article.select_one(".post-category")
    return cat.get_text(strip=True) if cat else ""


def extract_date(article: Tag) -> str:
    meta = article.select_one(".post-meta")
    if not meta:
        return TODAY
    spans = meta.find_all("span")
    for s in spans:
        t = s.get_text(strip=True)
        m = re.match(r"(\d{2})/(\d{2})/(\d{4})", t)
        if m:
            d, mo, y = m.groups()
            return f"{y}-{mo}-{d}"
    return TODAY


def base_template(title: str, description: str, canonical_path: str, body_main: str, css: str, scripts_head: str, header: str, footer: str, scripts_body: str) -> str:
    canonical = f"{SITE_URL}/{canonical_path.lstrip('/')}"
    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#ff9900">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="author" content="Jefferson Tavares">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
    <meta name="googlebot" content="index, follow">
    <link rel="canonical" href="{canonical}">

    <meta name="google-adsense-account" content="ca-pub-9518840979833525">

    <meta property="og:site_name" content="Descentralize">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{canonical}">
    <meta property="og:locale" content="pt_BR">
    <meta property="og:image" content="{SITE_URL}/og-image.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@jeffw3b">
    <meta name="twitter:creator" content="@jeffw3b">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">

    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='50' cy='50' r='45' fill='none' stroke='%23ff8c00' stroke-width='4'/%3E%3Ctext x='50' y='66' font-family='monospace' font-size='52' font-weight='700' text-anchor='middle' fill='%23ff8c00'%3E%E2%82%BF%3C/text%3E%3C/svg%3E">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

{scripts_head}

    <style>
{css}
    .article-page-wrap {{ max-width: 820px; margin: 60px auto 80px; padding: 0 24px; }}
    .article-page-wrap .breadcrumb {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--muted); margin-bottom: 24px; }}
    .article-page-wrap .breadcrumb a {{ color: var(--accent); text-decoration: none; }}
    .article-page-wrap .breadcrumb a:hover {{ text-decoration: underline; }}
    .article-page-wrap .back-link {{ display: inline-block; margin-top: 40px; padding: 10px 20px; background: var(--bg-2); border: 1px solid var(--border); color: var(--accent); text-decoration: none; font-family: 'JetBrains Mono', monospace; font-size: 14px; border-radius: 6px; }}
    .article-page-wrap .back-link:hover {{ background: var(--bg-3); }}
    </style>
</head>
<body>
{header}
    <main class="article-page-wrap">
        <div class="breadcrumb"><a href="/">home</a> / <a href="/#blog">blog</a> / <span>{title}</span></div>
{body_main}
        <a href="/#blog" class="back-link">← voltar para todos os artigos</a>
    </main>
{footer}
{scripts_body}
</body>
</html>
"""


def render_section_template(title: str, description: str, canonical_path: str, body_main: str, css: str, scripts_head: str, header: str, footer: str, scripts_body: str) -> str:
    canonical = f"{SITE_URL}/{canonical_path.lstrip('/')}"
    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#ff9900">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="author" content="Jefferson Tavares">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{canonical}">

    <meta name="google-adsense-account" content="ca-pub-9518840979833525">

    <meta property="og:site_name" content="Descentralize">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical}">
    <meta property="og:locale" content="pt_BR">
    <meta property="og:image" content="{SITE_URL}/og-image.png">

    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='50' cy='50' r='45' fill='none' stroke='%23ff8c00' stroke-width='4'/%3E%3Ctext x='50' y='66' font-family='monospace' font-size='52' font-weight='700' text-anchor='middle' fill='%23ff8c00'%3E%E2%82%BF%3C/text%3E%3C/svg%3E">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

{scripts_head}

    <style>
{css}
    .static-page-wrap {{ max-width: 820px; margin: 60px auto 80px; padding: 0 24px; }}
    .static-page-wrap .breadcrumb {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--muted); margin-bottom: 24px; }}
    .static-page-wrap .breadcrumb a {{ color: var(--accent); text-decoration: none; }}
    .static-page-wrap .back-link {{ display: inline-block; margin-top: 40px; padding: 10px 20px; background: var(--bg-2); border: 1px solid var(--border); color: var(--accent); text-decoration: none; font-family: 'JetBrains Mono', monospace; font-size: 14px; border-radius: 6px; }}
    </style>
</head>
<body>
{header}
    <main class="static-page-wrap">
        <div class="breadcrumb"><a href="/">home</a> / <span>{title.split(' — ')[0]}</span></div>
{body_main}
        <a href="/" class="back-link">← voltar para a home</a>
    </main>
{footer}
{scripts_body}
</body>
</html>
"""


def main():
    src_html = SRC.read_text(encoding="utf-8")
    soup = BeautifulSoup(src_html, "html.parser")

    style_tag = soup.find("style")
    css = style_tag.string if style_tag and style_tag.string else ""

    # collect all <script> in head, all <link> for fonts already in template
    head_scripts = []
    for s in soup.head.find_all("script"):
        head_scripts.append(str(s))
    scripts_head = "\n".join(head_scripts)

    # body-end scripts: collect all <script> at end of body
    body_scripts = []
    for s in soup.body.find_all("script"):
        body_scripts.append(str(s))
    scripts_body = "\n".join(body_scripts)

    header_tag = soup.find("header")
    if header_tag:
        # Clone and rewrite hash-only links to absolute URLs (works from any page)
        header_clone = BeautifulSoup(str(header_tag), "html.parser")
        rewrite_header_links(header_clone)
        header = str(header_clone)
    else:
        header = ""

    footer_tag = soup.find("footer")
    if footer_tag:
        footer_clone = BeautifulSoup(str(footer_tag), "html.parser")
        rewrite_header_links(footer_clone)
        footer = str(footer_clone)
    else:
        footer = ""

    ARTIGOS_DIR.mkdir(exist_ok=True)

    sitemap_urls = [(SITE_URL + "/", TODAY, "1.0", "daily")]

    # ---- ARTICLES ----
    articles = soup.find_all("article", class_="article-full")
    print(f"Found {len(articles)} full articles")

    for art in articles:
        art_id = art.get("id", "")
        slug = slug_from_article_id(art_id)
        if not slug:
            continue
        title_text = extract_title(art)
        description = extract_description(art)
        category = extract_category(art)
        date_iso = extract_date(art)

        page_title = f"{title_text} — Descentralize"
        art_clone = BeautifulSoup(str(art), "html.parser")
        rewrite_internal_article_links(art_clone)
        body = str(art_clone)

        page = base_template(
            title=page_title,
            description=description,
            canonical_path=f"artigos/{slug}.html",
            body_main=body,
            css=css,
            scripts_head=scripts_head,
            header=header,
            footer=footer,
            scripts_body=scripts_body,
        )
        out = ARTIGOS_DIR / f"{slug}.html"
        out.write_text(page, encoding="utf-8")
        sitemap_urls.append((f"{SITE_URL}/artigos/{slug}.html", date_iso, "0.8", "monthly"))
        print(f"  -> /artigos/{slug}.html  ({len(page)} bytes)  [{category} · {date_iso}]")

    # ---- SECTION PAGES (sobre, privacidade, contato, termos, aviso-legal) ----
    for section_id, (filename, page_title, description) in SECTION_PAGES.items():
        section = soup.find("section", id=section_id)
        if not section:
            print(f"  ! section #{section_id} not found, skipping")
            continue
        sec_clone = BeautifulSoup(str(section), "html.parser")
        rewrite_internal_article_links(sec_clone)
        body = str(sec_clone)
        page = render_section_template(
            title=page_title,
            description=description,
            canonical_path=filename,
            body_main=body,
            css=css,
            scripts_head=scripts_head,
            header=header,
            footer=footer,
            scripts_body=scripts_body,
        )
        out = ROOT / filename
        out.write_text(page, encoding="utf-8")
        sitemap_urls.append((f"{SITE_URL}/{filename}", TODAY, "0.5", "yearly"))
        print(f"  -> /{filename}  ({len(page)} bytes)")

    # ---- SITEMAP ----
    sitemap_lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lastmod, prio, freq in sitemap_urls:
        sitemap_lines.append("    <url>")
        sitemap_lines.append(f"        <loc>{url}</loc>")
        sitemap_lines.append(f"        <lastmod>{lastmod}</lastmod>")
        sitemap_lines.append(f"        <changefreq>{freq}</changefreq>")
        sitemap_lines.append(f"        <priority>{prio}</priority>")
        sitemap_lines.append("    </url>")
    sitemap_lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sitemap_lines), encoding="utf-8")
    print(f"\nSitemap: {len(sitemap_urls)} URLs")


if __name__ == "__main__":
    main()
