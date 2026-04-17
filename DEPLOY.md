# Website Setup & Deployment

This folder contains everything you need to turn your scraped `listings/`
data into a live website on GitHub Pages.

## What's in this package

```
website_package/
├── build_site.py         ← site generator (run once, re-run after scrape)
├── assets/
│   ├── style.css         ← design system
│   └── main.js           ← filter + gallery
├── impressum.html        ← legal placeholder (German law)
├── datenschutz.html      ← legal placeholder (German law)
├── 404.html              ← not-found page
└── DEPLOY.md             ← this file
```

## Step 1 — Drop these files into your website folder

Copy **every file and folder listed above** into:

```
C:\Users\marin\Repo\Roesch Klein Website\
```

So the final folder looks like this:

```
C:\Users\marin\Repo\Roesch Klein Website\
├── scraper\              (existing)
├── listings\             (existing, 95 listings + photos)
├── build_site.py         (new)
├── assets\               (new)
├── impressum.html        (new)
├── datenschutz.html      (new)
├── 404.html              (new)
└── DEPLOY.md             (new)
```

## Step 2 — Personalize the contact info

Open **build_site.py** in Notepad (or any editor). Near the top, change
these four lines to your real data:

```python
CONTACT_EMAIL = "info@roesch-klein.de"   # your email
BRAND = "Roesch & Klein Immobilien"
BRAND_SHORT = "Roesch & Klein"
PHONE_DISPLAY = "+49 (0) 000 000 000"    # your phone number
CITY_STAMP = "Dortmund"                   # your HQ city
```

Also open **impressum.html** and **datenschutz.html** and replace every
`[…]` placeholder with your real information. The Impressum is legally
required in Germany — without a correct one you can be abgemahnt.

## Step 3 — Generate the website

In PowerShell:

```powershell
cd "C:\Users\marin\Repo\Roesch Klein Website"
python build_site.py
```

You'll see:

```
> Loading listings ...
  95 listings loaded
> Writing home page ...
> Writing detail pages ...
  95 detail pages written

> Done. Open index.html in your browser to preview.
```

## Step 4 — Preview locally

Just double-click **index.html** in Windows Explorer. The site opens in
your browser. Click through listings, try the filter, check the image
galleries.

If something needs changing, edit `build_site.py` (content/logic) or
`assets/style.css` (look & feel), then re-run `python build_site.py`.

## Step 5 — Push to GitHub

You'll need a free GitHub account: <https://github.com/signup>

### One-time setup

Install Git for Windows from <https://git-scm.com/download/win> (accept
defaults during install). Open a fresh PowerShell window and verify:

```powershell
git --version
```

Tell Git who you are:

```powershell
git config --global user.name "Marin Kolev"
git config --global user.email "kolev@munichig.de"
```

### Create the GitHub repository

1. Go to <https://github.com/new>
2. Repository name: **roesch-klein** (or any name you want — this becomes part of the URL)
3. Visibility: **Public** (required for free GitHub Pages)
4. Do **not** initialize with README, .gitignore, or license — your folder already has content
5. Click **Create repository**

GitHub will show a page with a URL like `https://github.com/<your-username>/roesch-klein.git`. Copy it.

### First push from your folder

```powershell
cd "C:\Users\marin\Repo\Roesch Klein Website"
git init
git branch -M main
git add .
git commit -m "Initial site"
git remote add origin https://github.com/<your-username>/roesch-klein.git
git push -u origin main
```

It will ask you to log in the first time — use your GitHub account.

### Enable GitHub Pages

1. On GitHub, open your repository.
2. Click **Settings** → **Pages** (left sidebar).
3. Under **Source**, choose **Deploy from a branch**.
4. Branch: **main**, Folder: **/ (root)**. Save.
5. Wait 30–60 seconds. Your site will be live at:

   `https://<your-username>.github.io/roesch-klein/`

### Later: updating the site

Whenever you add/remove listings, re-scrape and re-generate, then push:

```powershell
cd "C:\Users\marin\Repo\Roesch Klein Website"
python scraper\scrape_bayer.py          # refresh listings + images
python build_site.py                     # regenerate HTML
git add .
git commit -m "Update listings"
git push
```

GitHub Pages redeploys automatically in under a minute.

## Optional — use your own domain

If you own a domain (e.g. `roesch-klein.de`), you can point it at the
GitHub-Pages site instead of using the `.github.io` URL. In the GitHub
Pages settings, add your domain under "Custom domain" and follow the DNS
instructions GitHub shows you. Happy to help with that when you're
ready.

## Notes on the design

- **Navy + serif** palette: professional, premium, trustworthy — the
  look most German real-estate brokerages use.
- **Responsive**: works on phone, tablet, desktop.
- **Zero tracking**: no cookies, no analytics, no third-party scripts —
  keeps the Datenschutz page short.
- **Client-side filter**: all 95 listings load on the home page and the
  filter (city / type / Kauf / Miete / price) works without reloading.
  This is fine for ~100 listings; if you ever grow past 500 we'd switch
  to pagination.
- **Contact button**: a `mailto:` link pre-fills the email subject with
  the Objekt-ID and address, so inquiries arrive already labelled.

## Troubleshooting

**"python not recognized"** — you need to open a fresh PowerShell
window after installing Python (done earlier).

**Images don't show up in preview** — check that `listings/<slug>/images/`
contains files. Re-run `python scraper\scrape_bayer.py` if needed.

**Site works locally but not on GitHub Pages** — GitHub Pages serves the
site under a sub-path (`/roesch-klein/`), so absolute paths starting
with `/` would break. This site uses only relative paths, so it works
in both places. If you ever edit HTML by hand, keep paths relative.

**"Repository too large" on push** — if the `listings/images/` folders
total more than 1 GB, GitHub will warn. Check with:

```powershell
git ls-files | Measure-Object -Property Length -Sum
```

If it's too big, we can switch to a separate image-hosting approach.
