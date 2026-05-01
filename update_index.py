#!/usr/bin/env python3
"""
Update index.html so each <article class="post-card" data-post="X">
links to /artigos/X.html, and update nav links to standalone pages.

Idempotent: re-running won't double-wrap links.
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

ROOT = Path(__file__).parent
INDEX = ROOT / "index.html"

# nav: hash -> standalone URL
NAV_REWRITES = {
    "#sobre": "/sobre.html",
    "#contato": "/contato.html",
    "#privacidade": "/politica-privacidade.html",
    "#termos": "/termos.html",
    "#aviso-legal": "/aviso-legal.html",
}


def main():
    soup = BeautifulSoup(INDEX.read_text(encoding="utf-8"), "html.parser")

    # 1. Rewrite nav links
    nav = soup.find("nav")
    if nav:
        for a in nav.find_all("a"):
            href = a.get("href", "")
            if href in NAV_REWRITES:
                a["href"] = NAV_REWRITES[href]

    # 2. Wrap each post-card so it links to /artigos/SLUG.html
    cards = soup.find_all("article", class_="post-card")
    wrapped = 0
    for card in cards:
        slug = card.get("data-post")
        if not slug:
            continue
        target = f"/artigos/{slug}.html"

        # Mark href on card itself for JS
        card["data-href"] = target

        # Find post-readmore span and convert to <a>
        readmore = card.find("span", class_="post-readmore")
        if readmore:
            new_a = soup.new_tag("a", href=target)
            new_a["class"] = "post-readmore"
            new_a.string = readmore.get_text(strip=True)
            readmore.replace_with(new_a)

        # Wrap title <h3> in link too
        h3 = card.find("h3")
        if h3 and not h3.find("a"):
            children = list(h3.children)
            link = soup.new_tag("a", href=target)
            link["style"] = "color:inherit;text-decoration:none;"
            for child in children:
                link.append(child.extract() if hasattr(child, 'extract') else child)
            h3.append(link)

        wrapped += 1

    # 3. Add JS to make whole card clickable (preserves filter UX)
    body = soup.find("body")
    existing = body.find("script", id="card-link-handler")
    if not existing:
        new_script = soup.new_tag("script", id="card-link-handler")
        new_script.string = """
(function() {
  document.addEventListener('click', function(e) {
    var card = e.target.closest('article.post-card[data-href]');
    if (!card) return;
    if (e.target.closest('a')) return;
    if (e.target.closest('button')) return;
    window.location.href = card.getAttribute('data-href');
  });
})();
"""
        body.append(new_script)

    INDEX.write_text(str(soup), encoding="utf-8")
    print(f"Updated {wrapped} post-cards with /artigos/ links")
    print(f"Rewrote {sum(1 for k in NAV_REWRITES if k in str(soup))} nav links to standalone pages")


if __name__ == "__main__":
    main()
