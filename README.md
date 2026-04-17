# Roesch & Klein — Website Rebuild

This folder contains everything needed to extract all active real-estate
listings from the old BAYER Immobilien website (`https://bayerimmobilien.com/immobilien/`)
into a clean, structured folder, ready for a new static website on GitHub Pages.

## What's in here

| Path                             | What it is                                                                 |
| -------------------------------- | -------------------------------------------------------------------------- |
| `scraper/scrape_bayer.py`        | Self-contained Python scraper. Run this once locally.                      |
| `listings/index_preview.json`    | Preview summary of all 95 active listings (IDs, titles, prices, hero photo). |
| `listings/` (after run)          | Populated by the scraper: one sub-folder per listing with JSON + images.   |

## Step 1 — Run the scraper on your computer

You only need to do this once. It's idempotent, so re-running is safe
(it only downloads what's missing).

### Prerequisites

- Python 3.9 or newer
- Two Python packages:

```bash
pip install requests beautifulsoup4
```

### Run it

From inside this folder:

```bash
python3 scraper/scrape_bayer.py
```

That's it. Expect roughly 5–10 minutes: discovery, 95 detail pages, and
all photos in maximum resolution.

### Optional flags

| Flag               | Purpose                                                       |
| ------------------ | ------------------------------------------------------------- |
| `--skip-images`    | Parse metadata only (useful for a first quick pass).          |
| `--refresh`        | Re-fetch detail pages even if `data.json` already exists.     |
| `--only <slug>`    | Only process listings whose slug contains the given string.   |

Examples:

```bash
python3 scraper/scrape_bayer.py --skip-images
python3 scraper/scrape_bayer.py --only bergkamen
python3 scraper/scrape_bayer.py --refresh
```

## Step 2 — What you get

After a successful run, `listings/` looks like this:

```
listings/
├── index.json                                         # master list, one row per listing
├── index_preview.json                                 # preview list (created earlier)
├── wohnung-3-zimmer-wohnung-in-wuppertal-...-20260402/
│   ├── data.json                                      # full specs + description + image URLs
│   └── images/
│       ├── 01.jpg
│       ├── 02.jpg
│       └── ...
├── haus-doppelhaushaelfte-in-bergkamen-kaufen-20240301/
│   ├── data.json
│   └── images/
└── ...                                                # ~95 folders total
```

### Shape of a single `data.json`

```json
{
  "url": "https://bayerimmobilien.com/immobilien/.../",
  "slug": "haus-doppelhaushaelfte-in-bergkamen-kaufen-20240301",
  "title": "Doppelhaushälfte in Bergkamen",
  "headline": "59192 Bergkamen, Doppelhaushälfte",
  "specs": {
    "Objektdaten": {
      "Objekt ID": "20240301",
      "Kaufpreis": "...",
      "Wohnfläche ca.": "...",
      "Grundstück ca.": "...",
      "Zimmer": "..."
    },
    "Ausstattung / Merkmale": { "...": "..." },
    "Energieausweis":        { "...": "..." }
  },
  "description": {
    "Objektbeschreibung": "...",
    "Ausstattung":        "...",
    "Sonstiges":          "..."
  },
  "lage": "...",
  "images": [
    "https://bayerimmobilien.com/wp-content/uploads/immomakler/...01.jpg",
    "..."
  ]
}
```

### Shape of `index.json`

One row per listing, built from each `data.json`:

```json
[
  {
    "slug": "...",
    "url": "...",
    "title": "...",
    "headline": "...",
    "id": "20260402",
    "kaufpreis": "89.500 €",
    "kaltmiete": null,
    "wohnflaeche": "38 m²",
    "zimmer": "1,5",
    "image_count": 12
  }
]
```

## Step 3 — Build the new website (next session)

When the `listings/` folder is fully populated, come back here and we'll
generate a static HTML site from `index.json`:

- Home page with a filterable/sortable listing grid
- One detail page per listing (using its `data.json`)
- Image galleries pulled from each listing's `images/` folder
- A `/404.html`, `/impressum.html`, and simple responsive design
- Ready to commit to a GitHub repository and serve via GitHub Pages

No database, no CMS, no server — just static files. Updates later are
easy: re-run the scraper (it's idempotent), regenerate the pages, commit,
push.

## Notes

- The scraper downloads **maximum-resolution originals** by stripping
  WordPress size suffixes (e.g. `-475x316.jpg` → the original upload).
- It's polite: 0.4 s delay between detail-page requests, max 8 parallel
  image downloads per listing.
- Failed image downloads are logged and retried on the next run.
- No credentials or scraping-blockers are involved — the site is public.
