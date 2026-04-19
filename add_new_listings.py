#!/usr/bin/env python3
"""
Add the two manually-curated Ladenburg listings to the site.

Run this AFTER the scraper (scrape_bayer.py) and BEFORE build_site.py:

    python add_new_listings.py
    python build_site.py

The script is idempotent: re-running it overwrites the two target folders
cleanly, so it is safe to run after every scraper update.

Source photos (already on your disk):
    NEUE ANZEIGEN/Anzeige 1/*.jpg   -> Ladenburg Etagenwohnung (OG)
    NEUE ANZEIGEN/Anzeige 2/*.jpg   -> Ladenburg Erdgeschosswohnung

Output:
    listings/wohnung-etagenwohnung-in-ladenburg-mieten-20260250/
    listings/wohnung-erdgeschosswohnung-in-ladenburg-mieten-20260220/
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

# ---------- Paths ----------

ROOT = Path(__file__).resolve().parent
LISTINGS_DIR = ROOT / "listings"
SOURCE_DIR = ROOT / "NEUE ANZEIGEN"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


# ---------- Shared content ----------

LAGE_LADENBURG = (
    "Ladenburg ist eine historische Kleinstadt am Neckar und liegt zentral "
    "in der Metropolregion Rhein-Neckar — mit einer der ältesten Altstädte "
    "Deutschlands und rund 12.000 Einwohnern.\n\n"
    "Die Lage zwischen Mannheim und Heidelberg bietet eine hervorragende "
    "Verkehrsanbindung: die Bundesautobahnen A5 und A6 sind in wenigen "
    "Minuten erreichbar, die S-Bahn RheinNeckar verbindet Ladenburg direkt "
    "mit den Hauptbahnhöfen beider Städte. Der Frankfurter Flughafen ist "
    "in unter einer Stunde erreichbar.\n\n"
    "Vor Ort steht eine umfassende Infrastruktur zur Verfügung: "
    "Grundschulen, weiterführende Schulen, Kindertagesstätten, Ärzte, "
    "Einkaufsmöglichkeiten für den täglichen Bedarf sowie Gastronomie "
    "und Kulturangebote in der denkmalgeschützten Altstadt. "
    "Grüngürtel und Neckar-Uferwege laden zu Erholung und Freizeit ein."
)


# ---------- Listing definitions ----------

LISTINGS = [
    {
        "slug": "wohnung-etagenwohnung-in-ladenburg-mieten-20260250",
        "source_folder": "Anzeige 1",
        "data": {
            "title": "Exklusive 3-Zimmer-Wohnung mit Balkon in Ladenburg!",
            "headline": "68526 Ladenburg, Etagenwohnung",
            # Controls grid position. Lexicographic reverse sort.
            # Adjust if you want these higher or lower in the grid.
            "sort_key": "20260250",
            "description": {
                "Objektbeschreibung": (
                    "Moderne 3-Zimmer-Wohnung im 1. Obergeschoss eines "
                    "Neubauobjekts (Baujahr 2026) in Ladenburg. Die Wohnung "
                    "überzeugt durch eine hochwertige, energieeffiziente "
                    "Bauweise mit Energieeffizienzklasse A+ (Endenergiebedarf "
                    "19 kWh/(m²·a)), Wärmepumpenheizung und Fußbodenheizung "
                    "in allen Räumen.\n"
                    "Ein hochwertiger Vinyl-Boden zieht sich durch die "
                    "Wohnräume; Kunststofffenster mit elektrischen "
                    "Rollläden sorgen für Komfort und Sicherheit. Das "
                    "Tageslichtbad ist mit bodenebener Dusche, Badewanne "
                    "und Waschmaschinenanschluss ausgestattet.\n"
                    "Der nach Osten ausgerichtete Balkon lädt zum "
                    "morgendlichen Frühstück im Freien ein. Ein "
                    "Personenaufzug erschließt alle Etagen, eine digitale "
                    "Gegensprechanlage mit Kamera und App-Steuerung sorgt "
                    "für modernen Komfort. Zur Wohnung gehören zudem ein "
                    "Tiefgaragenstellplatz sowie Fahrradstellplätze in "
                    "der Tiefgarage. Der Hausmeisterservice ist "
                    "inklusive."
                ),
                "Ausstattung": (
                    "Das Objekt ist in gehobener Qualität ausgestattet und "
                    "befindet sich in neuwertigem Zustand."
                ),
            },
            "lage": LAGE_LADENBURG,
            "specs": {
                "Objektdaten": {
                    "Objekt ID": "20260250",
                    "Kaltmiete": "1.280,87 €",
                    "Nebenkosten": "200,00 €",
                    "Heizkosten": "140,00 €",
                    "Warmmiete": "1.620,87 €",
                    "Kaution": "4.862,60 €",
                    "Preis/m²": "17,46 €/m²",
                    "Wohnfläche": "73,36 m²",
                    "Zimmer": "3",
                    "Schlafzimmer": "2",
                    "Badezimmer": "1",
                    "Etage": "1 von 3",
                    "Baujahr": "2026",
                    "Zustand": "Neuwertig",
                    "Ausstattung": "Gehobene Qualität",
                    "Verfügbar ab": "Nach Vereinbarung",
                    "Haustiere": "Nach Vereinbarung",
                    "Garage/Stellplatz": "1 Tiefgaragen-Stellplatz",
                    "Miete Stellplatz": "70,00 €",
                },
                "Ausstattung / Merkmale": [
                    "Ostbalkon",
                    "Kunststofffenster mit elektrischen Rollläden",
                    "Personenaufzug",
                    "Tageslichtbad mit bodenebener Dusche und Badewanne",
                    "Waschmaschinenanschluss im Badezimmer",
                    "Tiefgaragenstellplatz",
                    "Hochwertiger Vinyl-Boden",
                    "Fußbodenheizung in allen Räumen",
                    "Fahrradstellplätze in der Tiefgarage",
                    "Hochwertige Bauweise, energieeffizient und nachhaltig",
                    "Digitale Gegensprechanlage mit Kamera und App-Steuerung",
                    "Hausmeisterservice",
                ],
                "Energieausweis": {
                    "Energieausweistyp": "Bedarfsausweis",
                    "Baujahr": "2026",
                    "Heizungsart": "Wärmepumpe",
                    "Wesentlicher Energieträger": "Umweltwärme",
                    "Endenergiebedarf": "19 kWh/(m²·a)",
                    "Energieeffizienzklasse": "A+",
                },
            },
        },
    },
    {
        "slug": "wohnung-erdgeschosswohnung-in-ladenburg-mieten-20260220",
        "source_folder": "Anzeige 2",
        "data": {
            "title": "Charmante Erdgeschoss-Wohnung mit Terrasse in Ladenburg!",
            "headline": "68526 Ladenburg, Erdgeschosswohnung",
            "sort_key": "20260220",
            "description": {
                "Objektbeschreibung": (
                    "Charmante 3-Zimmer-Erdgeschosswohnung mit eigener "
                    "Terrasse in einem Neubauobjekt in Ladenburg "
                    "(Baujahr 2026). Der offene Wohn-Essbereich bildet "
                    "das Herzstück der Wohnung und schafft ein großzügiges "
                    "Raumgefühl.\n"
                    "Der stufenlose Zugang und ein Personenaufzug machen "
                    "die Wohnung altersgerecht und barrierearm. Das "
                    "Tageslichtbad ist mit Badewanne und Dusche ausgestattet.\n"
                    "Geheizt wird über eine moderne Wärmepumpe mit "
                    "Umweltwärme als wesentlichem Energieträger — "
                    "die Wohnung erreicht Energieeffizienzklasse A+ "
                    "(Endenergiebedarf 19 kWh/(m²·a)).\n"
                    "Zur Wohnung gehören ein Kellerabteil und ein "
                    "Tiefgaragenstellplatz."
                ),
                "Ausstattung": (
                    "Das Objekt ist in normaler Qualität ausgestattet "
                    "und gepflegt."
                ),
            },
            "lage": LAGE_LADENBURG,
            "specs": {
                "Objektdaten": {
                    "Objekt ID": "20260220",
                    "Kaltmiete": "1.350,59 €",
                    "Nebenkosten": "200,00 €",
                    "Heizkosten": "140,00 €",
                    "Warmmiete": "1.690,59 €",
                    "Kaution": "5.071,77 €",
                    "Preis/m²": "17,17 €/m²",
                    "Wohnfläche": "78,66 m²",
                    "Zimmer": "3",
                    "Schlafzimmer": "2",
                    "Badezimmer": "1",
                    "Etage": "0 von 0",
                    "Baujahr": "2026",
                    "Zustand": "Gepflegt",
                    "Ausstattung": "Normale Qualität",
                    "Verfügbar ab": "Nach Vereinbarung",
                    "Haustiere": "Nach Vereinbarung",
                    "Garage/Stellplatz": "1 Tiefgaragen-Stellplatz",
                    "Miete Stellplatz": "70,00 €",
                },
                "Ausstattung / Merkmale": [
                    "Terrasse",
                    "Keller",
                    "Personenaufzug",
                    "Stufenloser Zugang",
                    "Tageslichtbad mit Badewanne und Dusche",
                    "Tiefgaragenstellplatz",
                    "Wärmepumpenheizung",
                    "Offener Wohn-Essbereich",
                ],
                "Energieausweis": {
                    "Energieausweistyp": "Bedarfsausweis",
                    "Baujahr": "2026",
                    "Heizungsart": "Wärmepumpe",
                    "Wesentlicher Energieträger": "Umweltwärme",
                    "Endenergiebedarf": "19 kWh/(m²·a)",
                    "Energieeffizienzklasse": "A+",
                },
            },
        },
    },
]


# ---------- Helpers ----------

def collect_source_images(src_dir: Path) -> list[Path]:
    """Return image files in src_dir, sorted by filename."""
    if not src_dir.exists():
        return []
    imgs = [
        p for p in src_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]
    imgs.sort(key=lambda p: p.name.lower())
    return imgs


def write_listing(entry: dict) -> tuple[int, int]:
    """
    Create listings/<slug>/ with data.json and a fresh images/ folder.
    Returns (images_copied, images_found_in_source).
    """
    slug = entry["slug"]
    target_dir = LISTINGS_DIR / slug
    images_dir = target_dir / "images"

    target_dir.mkdir(parents=True, exist_ok=True)

    # Wipe existing images so re-runs don't accumulate duplicates.
    if images_dir.exists():
        shutil.rmtree(images_dir)
    images_dir.mkdir()

    src_dir = SOURCE_DIR / entry["source_folder"]
    src_imgs = collect_source_images(src_dir)

    copied = 0
    for i, src in enumerate(src_imgs, start=1):
        ext = src.suffix.lower()
        # Normalise .jpeg -> .jpg for consistency.
        if ext == ".jpeg":
            ext = ".jpg"
        dst = images_dir / f"{i:02d}{ext}"
        shutil.copy2(src, dst)
        copied += 1

    # Write data.json
    (target_dir / "data.json").write_text(
        json.dumps(entry["data"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return copied, len(src_imgs)


def main() -> int:
    if not SOURCE_DIR.exists():
        print(f"! Source folder not found: {SOURCE_DIR}")
        print("  Expected layout:")
        print(f"    {SOURCE_DIR / 'Anzeige 1'}  (photos for listing 1)")
        print(f"    {SOURCE_DIR / 'Anzeige 2'}  (photos for listing 2)")
        return 1

    LISTINGS_DIR.mkdir(exist_ok=True)

    print(f"> Adding {len(LISTINGS)} manual listings from {SOURCE_DIR} ...")
    for entry in LISTINGS:
        copied, found = write_listing(entry)
        status = "OK" if copied > 0 else "WARN: 0 images"
        print(
            f"  [{status}] {entry['slug']}  "
            f"({copied}/{found} images from '{entry['source_folder']}')"
        )

    print("\n> Done. Next step:  python build_site.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
