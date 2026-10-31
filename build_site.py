#!/usr/bin/env python3
"""
Static-site generator for Roesch & Klein Immobilien.

Reads the `listings/` folder produced by scraper/scrape_bayer.py and writes
GitHub-Pages-ready HTML at the repo root:

    index.html                                 home page with filter grid
    immobilien/<slug>/index.html               one detail page per listing
    immobilien/<slug>/images/                  referenced by relative path

The listings/ folder already contains all images, so we reference them
relative to the detail pages (no duplication).

Run:
    python build_site.py

Idempotent: safe to re-run after scraping new listings.
"""

from __future__ import annotations

import html
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# ---------- Paths ----------

ROOT = Path(__file__).resolve().parent
LISTINGS_DIR = ROOT / "listings"
OUT_IMMO_DIR = ROOT / "immobilien"
ASSETS_DIR = ROOT / "assets"

CONTACT_EMAIL = "info@roesch-klein.de"   # TODO: replace
BRAND = "Roesch & Klein Immobilien"
BRAND_SHORT = "Roesch & Klein"
PHONE_DISPLAY = "+49 (0) 000 000 000"    # TODO: replace
CITY_STAMP = "Dortmund"                   # TODO: replace with your HQ city


# ---------- Helpers ----------

def slugify_safe(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse_price(value: str | None) -> int | None:
    if not value:
        return None
    digits = re.sub(r"[^\d]", "", value)
    return int(digits) if digits else None


def parse_area(value: str | None) -> float | None:
    if not value:
        return None
    m = re.search(r"([\d.,]+)", value)
    if not m:
        return None
    num = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(num)
    except ValueError:
        return None


def extract_city(headline: str | None, slug: str) -> str:
    # Headline typically "12345 Stadtname, Objekttyp"
    if headline:
        m = re.search(r"\d{5}\s+([^,]+)", headline)
        if m:
            return m.group(1).strip()
    # Fallback: parse slug
    parts = slug.split("-")
    for i, p in enumerate(parts):
        if p == "in" and i + 1 < len(parts):
            # Take up to "-kaufen" or "-mieten"
            rest = []
            for q in parts[i + 1:]:
                if q in ("kaufen", "mieten"):
                    break
                rest.append(q)
            return " ".join(x.capitalize() for x in rest)
    return "—"


TYPE_MAP = {
    "einfamilienhaus": "Einfamilienhaus",
    "doppelhaushaelfte": "Doppelhaushälfte",
    "mehrfamilienhaus": "Mehrfamilienhaus",
    "zweifamilienhaus": "Zweifamilienhaus",
    "reiheneckhaus": "Reiheneckhaus",
    "reihenendhaus": "Reihenendhaus",
    "reihenmittelhaus": "Reihenmittelhaus",
    "eigentumswohnung": "Eigentumswohnung",
    "dachgeschosswohnung": "Dachgeschosswohnung",
    "erdgeschosswohnung": "Erdgeschosswohnung",
    "etagenwohnung": "Etagenwohnung",
    "maisonettewohnung": "Maisonettewohnung",
    "penthousewohnung": "Penthouse",
}


def extract_type(slug: str) -> str:
    for key, label in TYPE_MAP.items():
        if key in slug:
            return label
    if slug.startswith("haus-"):
        return "Haus"
    if slug.startswith("wohnung-"):
        return "Wohnung"
    return "Immobilie"


def mode_from_slug(slug: str) -> str:
    if "-mieten-" in slug or slug.endswith("-mieten"):
        return "miete"
    return "kauf"


def get_specs(data: dict, section: str) -> dict:
    s = data.get("specs", {}).get(section)
    return s if isinstance(s, dict) else {}


def get_features(data: dict) -> list[str]:
    """Ausstattung / Merkmale can be dict (key: value) or list."""
    a = data.get("specs", {}).get("Ausstattung / Merkmale")
    if isinstance(a, dict):
        return [f"{k}: {v}" for k, v in a.items()]
    if isinstance(a, list):
        return a
    return []


def load_listings() -> list[dict]:
    """
    Scan listings/*/data.json directly. Do NOT rely on listings/index.json,
    because the scraper overwrites it on every run and would otherwise
    silently drop any manually-curated listings added via add_new_listings.py.
    """
    listings = []
    if not LISTINGS_DIR.exists():
        return listings
    for slug_dir in sorted(LISTINGS_DIR.iterdir()):
        if not slug_dir.is_dir():
            continue
        data_path = slug_dir / "data.json"
        if not data_path.exists():
            continue
        slug = slug_dir.name
        try:
            data = json.loads(data_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"! Skipping {slug}: invalid data.json ({e})")
            continue
        images_dir = slug_dir / "images"
        images = (
            sorted(p.name for p in images_dir.iterdir() if p.is_file())
            if images_dir.exists() else []
        )
        od = get_specs(data, "Objektdaten")
        mode = mode_from_slug(slug)
        price_str = od.get("Kaufpreis") if mode == "kauf" else (
            od.get("Kaltmiete") or od.get("Warmmiete")
        )
        listings.append({
            "slug": slug,
            "url_rel": f"immobilien/{slug}/index.html",
            "title": data.get("title") or slug,
            "headline": data.get("headline") or "",
            "mode": mode,
            "type": extract_type(slug),
            "city": extract_city(data.get("headline"), slug),
            "price_str": price_str,
            "price_num": parse_price(price_str),
            "wohnflaeche": od.get("Wohnfläche ca.") or od.get("Wohnfläche"),
            "wohnflaeche_num": parse_area(od.get("Wohnfläche ca.") or od.get("Wohnfläche")),
            "zimmer": od.get("Zimmer"),
            "grundstueck": od.get("Grundstück ca.") or od.get("Grundstücksfläche"),
            "objekt_id": od.get("Objekt ID") or od.get("Objektnummer"),
            "description": data.get("description", {}),
            "lage": data.get("lage", ""),
            "od": od,
            "features": get_features(data),
            "energie": get_specs(data, "Energieausweis"),
            "hero": f"listings/{slug}/images/{images[0]}" if images else "",
            "hero_rel_detail": f"images/{images[0]}" if images else "",
            "images": images,
            "image_count": len(images),
            # Optional: lets add_new_listings.py control grid position without
            # having to game Objekt-IDs. Falls back to Objekt-ID if unset.
            "sort_key": data.get("sort_key"),
        })
    # Newest first by sort_key (if set) or Objekt-ID. Lexicographic reverse.
    listings.sort(
        key=lambda x: (x["sort_key"] or x["objekt_id"] or ""),
        reverse=True,
    )
    return listings


# ---------- HTML templates ----------

def esc(s) -> str:
    return html.escape(str(s)) if s is not None else ""


BASE_HEAD = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="{assets_prefix}assets/style.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='14' fill='%23fff'/%3E%3Ctext x='27' y='71' font-size='58' font-family='Georgia,serif' text-anchor='middle' fill='%230f2e4b'%3ER%3C/text%3E%3Crect x='49' y='20' width='3' height='60' fill='%23b8935a'/%3E%3Ctext x='75' y='71' font-size='58' font-family='Georgia,serif' text-anchor='middle' fill='%230f2e4b'%3EK%3C/text%3E%3C/svg%3E">
</head>
<body>
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="{home_href}">
      <span class="brand-mark" aria-hidden="true">R<span class="brand-rule"></span>K</span>
      <span class="brand-name"><span class="brand-title">Roesch &amp; Klein</span><span class="brand-sub">Immobilien</span></span>
    </a>
    <nav class="site-nav">
      <a href="{home_href}">Immobilien</a>
      <a href="{home_href}#kontakt">Kontakt</a>
    </nav>
  </div>
</header>
<main>
"""

BASE_FOOT = """</main>
<footer class="site-footer" id="kontakt">
  <div class="container footer-grid">
    <div>
      <div class="footer-brand"><span class="brand-mark" aria-hidden="true">R<span class="brand-rule"></span>K</span><span>{brand}</span></div>
      <div class="footer-sub">Ihr Immobilienmakler — persönlich, transparent, zuverlässig.</div>
    </div>
    <div>
      <div class="footer-label">Kontakt</div>
      <a href="mailto:{email}">{email}</a>
    </div>
    <div>
      <div class="footer-label">Rechtliches</div>
      <a href="{assets_prefix}impressum.html">Impressum</a><br>
      <a href="{assets_prefix}datenschutz.html">Datenschutz</a>
    </div>
  </div>
  <div class="container footer-bottom">© {year} {brand}. Alle Rechte vorbehalten.</div>
</footer>
</body>
</html>
"""


def render_base(title: str, description: str, body: str, assets_prefix: str = "", home_href: str = "index.html") -> str:
    head = BASE_HEAD.format(
        title=esc(title),
        description=esc(description),
        assets_prefix=assets_prefix,
        home_href=home_href,
        brand=BRAND,
    )
    foot = BASE_FOOT.format(
        brand=BRAND,
        email=CONTACT_EMAIL,
        phone=PHONE_DISPLAY,
        phone_plain=re.sub(r"[^\d+]", "", PHONE_DISPLAY),
        assets_prefix=assets_prefix,
        year=datetime.now().year,
    )
    return head + body + foot


def format_price(listing: dict) -> str:
    if listing["price_str"]:
        return listing["price_str"]
    return "Preis auf Anfrage"


def render_card(listing: dict) -> str:
    price = format_price(listing)
    hero = (
        f'<img src="{esc(listing["hero"])}" alt="{esc(listing["title"])}" loading="lazy">'
        if listing["hero"]
        else '<div class="no-photo">Kein Foto</div>'
    )
    specs = []
    if listing["zimmer"]:
        specs.append(f'<span>{esc(listing["zimmer"])} Zi.</span>')
    if listing["wohnflaeche"]:
        specs.append(f'<span>{esc(listing["wohnflaeche"])}</span>')
    if listing["grundstueck"]:
        specs.append(f'<span>Grund. {esc(listing["grundstueck"])}</span>')
    mode_badge = "Kauf" if listing["mode"] == "kauf" else "Miete"
    return f'''
<a class="card"
   href="{esc(listing["url_rel"])}"
   data-mode="{listing["mode"]}"
   data-city="{esc(listing["city"].lower())}"
   data-type="{esc(listing["type"].lower())}"
   data-price="{listing["price_num"] or ""}">
  <div class="card-photo">{hero}<span class="badge badge-{listing["mode"]}">{mode_badge}</span></div>
  <div class="card-body">
    <div class="card-title">{esc(listing["type"])} in {esc(listing["city"])}</div>
    <div class="card-price">{esc(price)}</div>
    <div class="card-specs">{" · ".join(specs) if specs else ""}</div>
  </div>
</a>
'''


def render_home(listings: list[dict]) -> str:
    cities = sorted({l["city"] for l in listings if l["city"] and l["city"] != "—"})
    types = sorted({l["type"] for l in listings})

    city_opts = "\n".join(f'<option value="{esc(c.lower())}">{esc(c)}</option>' for c in cities)
    type_opts = "\n".join(f'<option value="{esc(t.lower())}">{esc(t)}</option>' for t in types)

    cards_html = "\n".join(render_card(l) for l in listings)

    body = f'''
<section class="hero">
  <div class="container">
    <h1>Ihr Zuhause. Persönlich vermittelt.</h1>
    <p class="lead">{len(listings)} aktuelle Immobilienangebote — Häuser, Wohnungen und Anlageobjekte. Persönlich betreut, transparent vermittelt.</p>
  </div>
</section>

<section class="filter-section">
  <div class="container">
    <form class="filter-bar" id="filter-form" onsubmit="return false;">
      <div class="filter-group">
        <label>Angebot</label>
        <div class="seg">
          <button type="button" class="seg-btn is-active" data-filter="mode" data-value="all">Alle</button>
          <button type="button" class="seg-btn" data-filter="mode" data-value="kauf">Kauf</button>
          <button type="button" class="seg-btn" data-filter="mode" data-value="miete">Miete</button>
        </div>
      </div>
      <div class="filter-group">
        <label for="f-city">Stadt</label>
        <select id="f-city"><option value="">Alle Städte</option>{city_opts}</select>
      </div>
      <div class="filter-group">
        <label for="f-type">Typ</label>
        <select id="f-type"><option value="">Alle Typen</option>{type_opts}</select>
      </div>
      <div class="filter-group">
        <label for="f-pmin">Preis von</label>
        <input type="number" id="f-pmin" placeholder="0" min="0" step="10000">
      </div>
      <div class="filter-group">
        <label for="f-pmax">bis</label>
        <input type="number" id="f-pmax" placeholder="∞" min="0" step="10000">
      </div>
      <button type="button" class="btn-reset" id="f-reset">Zurücksetzen</button>
    </form>
    <div class="result-count"><span id="result-count">{len(listings)}</span> von {len(listings)} Immobilien</div>
  </div>
</section>

<section class="listings">
  <div class="container">
    <div class="grid" id="listing-grid">
      {cards_html}
    </div>
    <div class="empty-state" id="empty-state" hidden>
      Keine Immobilien entsprechen Ihren Filterkriterien.
    </div>
  </div>
</section>

<script src="assets/main.js"></script>
'''
    return render_base(
        title=f"{BRAND} — Häuser & Wohnungen",
        description=f"{len(listings)} aktuelle Immobilienangebote — Häuser, Wohnungen und Anlageobjekte. {BRAND}.",
        body=body,
        assets_prefix="",
        home_href="index.html",
    )


def render_gallery(listing: dict) -> str:
    if not listing["images"]:
        return '<div class="gallery gallery-empty">Keine Fotos verfügbar.</div>'
    main_src = f'images/{listing["images"][0]}'
    thumbs = "\n".join(
        f'<button type="button" class="thumb{" is-active" if i == 0 else ""}" data-src="images/{esc(img)}"><img src="images/{esc(img)}" alt="" loading="lazy"></button>'
        for i, img in enumerate(listing["images"])
    )
    return f'''
<div class="gallery">
  <div class="gallery-main">
    <img id="gallery-hero" src="{esc(main_src)}" alt="{esc(listing["title"])}">
  </div>
  <div class="gallery-thumbs">
    {thumbs}
  </div>
</div>
'''


def render_spec_table(od: dict) -> str:
    if not od:
        return ""
    # Preferred order
    order = [
        "Objekt ID", "Objektnummer",
        "Kaufpreis", "Kaltmiete", "Warmmiete", "Nebenkosten", "Kaution",
        "Zimmer", "Wohnfläche ca.", "Wohnfläche",
        "Nutzfläche", "Grundstück ca.", "Grundstücksfläche",
        "Etage", "Etagen", "Baujahr", "Zustand",
        "Verfügbar ab", "Provision", "Käuferprovision", "Courtage",
    ]
    seen = set()
    rows = []
    for key in order:
        if key in od:
            rows.append((key, od[key]))
            seen.add(key)
    for k, v in od.items():
        if k not in seen:
            rows.append((k, v))
    html_rows = "\n".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in rows)
    return f'<div class="spec-wrap"><h3>Objektdaten</h3><table class="specs">{html_rows}</table></div>'


def render_features(features: list[str]) -> str:
    if not features:
        return ""
    items = "\n".join(f"<li>{esc(f)}</li>" for f in features)
    return f'<div class="features"><h3>Ausstattung &amp; Merkmale</h3><ul>{items}</ul></div>'


def render_energie(energie: dict) -> str:
    if not energie:
        return ""
    rows = "\n".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in energie.items())
    return f'<div class="spec-wrap"><h3>Energieausweis</h3><table class="specs">{rows}</table></div>'


def render_description(desc: dict) -> str:
    if not desc:
        return ""
    parts = []
    for key, text in desc.items():
        paras = "\n".join(f"<p>{esc(p)}</p>" for p in text.split("\n") if p.strip())
        parts.append(f'<div class="prose-block"><h3>{esc(key)}</h3>{paras}</div>')
    return '<section class="prose">' + "\n".join(parts) + "</section>"


def render_lage(lage: str) -> str:
    if not lage:
        return ""
    paras = "\n".join(f"<p>{esc(p)}</p>" for p in lage.split("\n\n") if p.strip())
    return f'<section class="prose"><div class="prose-block"><h3>Lage</h3>{paras}</div></section>'


def render_detail(listing: dict) -> str:
    price = format_price(listing)
    mode_label = "Kauf" if listing["mode"] == "kauf" else "Miete"

    summary = []
    if listing["zimmer"]:
        summary.append(f'<div><dt>Zimmer</dt><dd>{esc(listing["zimmer"])}</dd></div>')
    if listing["wohnflaeche"]:
        summary.append(f'<div><dt>Wohnfläche</dt><dd>{esc(listing["wohnflaeche"])}</dd></div>')
    if listing["grundstueck"]:
        summary.append(f'<div><dt>Grundstück</dt><dd>{esc(listing["grundstueck"])}</dd></div>')
    if listing["objekt_id"]:
        summary.append(f'<div><dt>Objekt-ID</dt><dd>{esc(listing["objekt_id"])}</dd></div>')
    summary_html = "<dl class='summary-dl'>" + "".join(summary) + "</dl>" if summary else ""

    subject = f"Anfrage zu Objekt {listing['objekt_id'] or listing['slug']}: {listing['type']} in {listing['city']}"
    mailto = f"mailto:{CONTACT_EMAIL}?subject={quote(subject)}"
    phone_plain = re.sub(r"[^\d+]", "", PHONE_DISPLAY)

    body = f'''
<div class="container detail">
  <a class="back-link" href="../../index.html">← Zur Übersicht</a>

  <div class="detail-head">
    <div class="detail-titles">
      <span class="badge badge-{listing["mode"]}">{mode_label}</span>
      <h1>{esc(listing["title"])}</h1>
      <div class="headline">{esc(listing["headline"])}</div>
    </div>
    <div class="detail-price">{esc(price)}</div>
  </div>

  {render_gallery(listing)}

  {summary_html}

  <div class="detail-grid">
    <div class="detail-main">
      {render_description(listing["description"])}
      {render_lage(listing["lage"])}
      {render_features(listing["features"])}
    </div>
    <aside class="detail-side">
      <div class="contact-card">
        <h3>Interesse an diesem Objekt?</h3>
        <p>Nehmen Sie Kontakt mit uns auf — wir beraten Sie gerne und organisieren einen Besichtigungstermin.</p>
        <a class="btn-primary" href="{esc(mailto)}">Jetzt anfragen</a>
        <div class="contact-meta">
          <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
        </div>
      </div>
      {render_spec_table(listing["od"])}
      {render_energie(listing["energie"])}
    </aside>
  </div>
</div>

<script src="../../assets/main.js"></script>
'''
    return render_base(
        title=f"{listing['type']} in {listing['city']} — {BRAND}",
        description=f"{listing['type']} in {listing['city']}. {price}. {BRAND}.",
        body=body,
        assets_prefix="../../",
        home_href="../../index.html",
    )


# ---------- Main ----------

def main() -> int:
    if not LISTINGS_DIR.exists():
        print(f"! listings/ folder not found at {LISTINGS_DIR}. Run scraper first.")
        return 1

    print("> Loading listings ...")
    listings = load_listings()
    print(f"  {len(listings)} listings loaded")

    print("> Writing home page ...")
    (ROOT / "index.html").write_text(render_home(listings), encoding="utf-8")

    print("> Writing detail pages ...")
    OUT_IMMO_DIR.mkdir(exist_ok=True)
    written = 0
    for l in listings:
        out_dir = OUT_IMMO_DIR / l["slug"]
        out_dir.mkdir(exist_ok=True)
        # Link or copy images into the immobilien/<slug>/images/ folder
        src_imgs = LISTINGS_DIR / l["slug"] / "images"
        dst_imgs = out_dir / "images"
        if src_imgs.exists():
            dst_imgs.mkdir(exist_ok=True)
            for img in src_imgs.iterdir():
                target = dst_imgs / img.name
                if not target.exists():
                    try:
                        # Hard link for speed; fallback to copy
                        target.hardlink_to(img)
                    except (OSError, AttributeError):
                        shutil.copy2(img, target)
        (out_dir / "index.html").write_text(render_detail(l), encoding="utf-8")
        written += 1
    print(f"  {written} detail pages written")

    print(f"\n> Done. Open index.html in your browser to preview.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
