#!/usr/bin/env python3
"""
BAYER Immobilien listing scraper.

Crawls https://bayerimmobilien.com/immobilien/ and extracts every active
property listing into a clean, GitHub-ready folder structure:

    listings/
        index.json                           master list
        <slug>/
            data.json                        full spec + description + image URLs
            images/
                01.jpg, 02.jpg, ...          all photos in max resolution
        ...

Usage:
    python3 scrape_bayer.py                   # first run: full scrape
    python3 scrape_bayer.py --skip-images     # metadata only, no downloads
    python3 scrape_bayer.py --refresh         # re-fetch detail pages even if cached

Dependencies:
    pip install requests beautifulsoup4

The script is idempotent: re-running only downloads missing files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Missing dependencies. Run:  pip install requests beautifulsoup4")

BASE = "https://bayerimmobilien.com"
INDEX_URL = f"{BASE}/immobilien/"
OUTPUT_DIR = Path("listings")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
REQUEST_DELAY = 0.4         # seconds between detail-page requests (polite)
IMAGE_WORKERS = 8           # parallel image downloads per listing
TIMEOUT = 30

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ---------- Discovery ----------

def fetch(url: str) -> str:
    r = SESSION.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def discover_listing_urls() -> list[str]:
    """Walk pagination until no new pages appear."""
    urls: set[str] = set()
    page = 1
    while True:
        page_url = INDEX_URL if page == 1 else f"{INDEX_URL}page/{page}/"
        try:
            html = fetch(page_url)
        except requests.HTTPError:
            break
        soup = BeautifulSoup(html, "html.parser")
        found = 0
        for a in soup.select('a[href*="/immobilien/"]'):
            href = urljoin(BASE, a["href"].strip())
            slug = href.rstrip("/").split("/")[-1]
            # Listing slugs start with a property-class prefix
            if slug and any(slug.startswith(p) for p in ("wohnung-", "haus-")):
                urls.add(href.split("#")[0].rstrip("/") + "/")
                found += 1
        print(f"  page {page}: +{found} listings (total {len(urls)})")
        # Stop if next-page link is missing
        next_link = soup.find("a", href=re.compile(rf"/page/{page + 1}/?"))
        if not next_link:
            break
        page += 1
    return sorted(urls)


# ---------- Parsing ----------

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _upgrade_image_url(url: str) -> str:
    """Strip WordPress size suffix (e.g. -475x316) to get the original upload."""
    return re.sub(r"-\d+x\d+(\.(?:jpe?g|png|webp))$", r"\1", url, flags=re.I)


def parse_listing(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    data: dict = {"url": url, "slug": url.rstrip("/").split("/")[-1]}

    # Title
    h1 = soup.find("h1")
    if h1:
        data["title"] = _clean(h1.get_text())

    # Sub-heading: "PLZ Stadt, Objekttyp"
    h2_first = soup.find("h2")
    if h2_first:
        data["headline"] = _clean(h2_first.get_text())

    # Spec sections: headings with sibling <ul> of key/value <li>
    spec_sections = {}
    for heading in soup.find_all(["h2", "h3"]):
        name = _clean(heading.get_text())
        if name not in ("Objektdaten", "Ausstattung / Merkmale", "Energieausweis"):
            continue
        ul = heading.find_next(["ul", "dl"])
        if not ul:
            continue
        if ul.name == "dl":
            kv = {}
            for dt, dd in zip(ul.find_all("dt"), ul.find_all("dd")):
                kv[_clean(dt.get_text())] = _clean(dd.get_text())
            spec_sections[name] = kv
        else:
            items = []
            kv = {}
            for li in ul.find_all("li", recursive=False):
                # Try to split label/value by child structure
                parts = list(li.stripped_strings)
                if len(parts) >= 2:
                    label, *value = parts
                    kv[label.rstrip(":")] = _clean(" ".join(value))
                elif parts:
                    items.append(parts[0])
            spec_sections[name] = kv if kv else items
    data["specs"] = spec_sections

    # Description blocks under "Objektbeschreibung" heading
    description = {}
    objbesch = soup.find(["h2", "h3"], string=re.compile(r"Objekt.?beschreibung", re.I))
    if objbesch:
        current_key = None
        buffer: list[str] = []
        def flush():
            if current_key and buffer:
                description[current_key] = "\n".join(buffer).strip()
        for sib in objbesch.find_all_next():
            # Stop at "Lage" or the Direktanfrage form
            if sib.name == "h2" and _clean(sib.get_text()) in ("Lage", "Direktanfrage", "Kontaktdaten"):
                break
            if sib.name == "h3":
                flush()
                current_key = _clean(sib.get_text())
                buffer = []
            elif sib.name == "p":
                buffer.append(_clean(sib.get_text()))
            elif sib.name in ("ul", "ol"):
                for li in sib.find_all("li"):
                    buffer.append("- " + _clean(li.get_text()))
        flush()
    data["description"] = description

    # Lage (location text)
    lage = soup.find(["h2", "h3"], string=re.compile(r"^Lage$"))
    if lage:
        parts = []
        for sib in lage.find_all_next():
            if sib.name == "h2":
                break
            if sib.name == "p":
                parts.append(_clean(sib.get_text()))
        data["lage"] = "\n\n".join(parts)

    # Images: anchors pointing to full-size uploads (strip WP size suffix)
    images: list[str] = []
    seen = set()
    for a in soup.select('a[href*="/wp-content/uploads/immomakler/"]'):
        href = a["href"].strip()
        if not re.search(r"\.(jpe?g|png|webp)$", href, re.I):
            continue
        full = _upgrade_image_url(urljoin(BASE, href))
        if full not in seen:
            seen.add(full)
            images.append(full)
    # Fallback: <img> tags if no anchors captured (rare)
    if not images:
        for img in soup.select('img[src*="/wp-content/uploads/immomakler/"]'):
            full = _upgrade_image_url(urljoin(BASE, img["src"].strip()))
            if full not in seen:
                seen.add(full)
                images.append(full)
    data["images"] = images

    return data


# ---------- Download ----------

def download_file(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return False
    try:
        r = SESSION.get(url, timeout=TIMEOUT, stream=True)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(16384):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"    ! image failed: {url} ({e})")
        if dest.exists():
            dest.unlink()
        return False


def download_images(image_urls: list[str], out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = []
    with ThreadPoolExecutor(max_workers=IMAGE_WORKERS) as pool:
        for idx, url in enumerate(image_urls, 1):
            ext = os.path.splitext(urlparse(url).path)[1].lower() or ".jpg"
            dest = out_dir / f"{idx:02d}{ext}"
            tasks.append(pool.submit(download_file, url, dest))
        downloaded = sum(1 for t in as_completed(tasks) if t.result())
    return downloaded


# ---------- Orchestration ----------

def process_listing(url: str, refresh: bool, skip_images: bool) -> dict | None:
    slug = url.rstrip("/").split("/")[-1]
    listing_dir = OUTPUT_DIR / slug
    data_path = listing_dir / "data.json"

    if data_path.exists() and not refresh:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    else:
        try:
            html = fetch(url)
        except Exception as e:
            print(f"  ! fetch failed: {e}")
            return None
        data = parse_listing(html, url)
        listing_dir.mkdir(parents=True, exist_ok=True)
        data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(REQUEST_DELAY)

    img_count_total = len(data.get("images", []))
    new_imgs = 0
    if not skip_images and data.get("images"):
        new_imgs = download_images(data["images"], listing_dir / "images")

    print(f"  OK  {slug:<70}  images: {img_count_total} (+{new_imgs})")

    od = data.get("specs", {}).get("Objektdaten", {})
    return {
        "slug": slug,
        "url": url,
        "title": data.get("title"),
        "headline": data.get("headline"),
        "id": od.get("Objekt ID") if isinstance(od, dict) else None,
        "kaufpreis": od.get("Kaufpreis") if isinstance(od, dict) else None,
        "kaltmiete": od.get("Kaltmiete") if isinstance(od, dict) else None,
        "wohnflaeche": od.get("Wohnfläche ca.") or od.get("Wohnfläche") if isinstance(od, dict) else None,
        "zimmer": od.get("Zimmer") if isinstance(od, dict) else None,
        "image_count": img_count_total,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--refresh", action="store_true", help="re-fetch detail pages even if data.json exists")
    parser.add_argument("--skip-images", action="store_true", help="parse metadata only; do not download images")
    parser.add_argument("--only", type=str, help="only process a listing whose slug contains this substring")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    print("> Discovering listings ...")
    urls = discover_listing_urls()
    if args.only:
        urls = [u for u in urls if args.only in u]
    print(f"> {len(urls)} listings to process\n")

    index = []
    for i, url in enumerate(urls, 1):
        print(f"[{i:>3}/{len(urls)}]  {url.rstrip('/').split('/')[-1]}")
        row = process_listing(url, refresh=args.refresh, skip_images=args.skip_images)
        if row:
            index.append(row)

    (OUTPUT_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n> Done. {len(index)} listings in ./{OUTPUT_DIR}/")
    print(f"  Master list: ./{OUTPUT_DIR}/index.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
