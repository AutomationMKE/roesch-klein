#!/usr/bin/env python3
"""
Add the five rental listings from the Calw / Gechingen new-build projects.

Run this BEFORE build_site.py:

    python add_calw_listings.py
    python build_site.py

The script is idempotent: re-running it overwrites the five target folders
cleanly.

Source photos and floor plans (local only, not in git):
    Neubauprojekte_Calw_Gechingen/01_Datensatz/projects/<projekt>/media/<wohnung>/

Photos are resized to max. 1600 px and saved as JPEG. PDF floor plans are
rendered to JPEG (needs pymupdf). Floor plans are always the last image.

Rents: cold rent per m² is at least 15,50 €/m² for every listing.
Calw-Stammheim (20261102) is set to 16,20 €/m² (92,50 m² x 16,20 =
1.498,50 €, rounded to 1.499 €).
"""

from __future__ import annotations

import io
import json
import shutil
from pathlib import Path

import pymupdf
from PIL import Image

# ---------- Paths ----------

ROOT = Path(__file__).resolve().parent
LISTINGS_DIR = ROOT / "listings"
SOURCE_DIR = ROOT / "Neubauprojekte_Calw_Gechingen" / "01_Datensatz" / "projects"

MAX_PX = 1600
JPEG_QUALITY = 82


# ---------- Shared content ----------

LAGE_GECHINGEN = (
    "Das neue Wohnquartier Talaue liegt ruhig am Ortsrand von Gechingen "
    "im Landkreis Calw, direkt an einem Naturschutzgebiet mit Spazier-, "
    "Rad- und Joggingwegen. Zwischen den Häusern entsteht ein grünes, "
    "parkartiges Wohnumfeld.\n"
    "Bäcker, Lebensmittelgeschäfte und Restaurants im Ortszentrum sind in "
    "wenigen Gehminuten erreichbar, ein Kindergarten liegt gegenüber.\n"
    "Fahrzeiten mit dem Auto (ca.): Calw 15 Minuten, A81 (Anschlussstelle "
    "Gärtringen) 15 Minuten, Herrenberg 18 Minuten, Böblingen 22 Minuten, "
    "Sindelfingen 23 Minuten, Flughafen und Messe Stuttgart 35 Minuten, "
    "Stuttgart Zentrum 40 Minuten."
)

LAGE_STAMMHEIM = (
    "Die Wohnung liegt im Ortskern von Calw-Stammheim. Geschäfte, Ärzte "
    "und Dienstleister sind zu Fuß erreichbar, Kinderkrippe, Kindergarten "
    "und Schulen bis zum Gymnasium befinden sich in der Nähe.\n"
    "Die Bushaltestelle ist rund 4 Gehminuten entfernt, die Calwer "
    "Innenstadt erreichen Sie mit dem Auto in etwa 5 Minuten. Die "
    "Hermann-Hesse-Bahn verbindet Calw mit Böblingen und Stuttgart, die "
    "Autobahnen A81 (Gärtringen) und A8 (Renningen) sind gut erreichbar."
)

ENERGIE_TALAUE_7 = {
    "Energieausweistyp": "Bedarfsausweis",
    "Baujahr": "2026",
    "Heizungsart": "Zentralheizung mit Fußbodenheizung",
    "Wesentlicher Energieträger": "Holzpellets",
    "Endenergiebedarf": "59 kWh/(m²·a)",
    "Energieeffizienzklasse": "B",
}

ENERGIE_TALAUE_9 = {
    "Energieausweistyp": "Bedarfsausweis",
    "Baujahr": "2026",
    "Heizungsart": "Zentralheizung mit Fußbodenheizung",
    "Wesentlicher Energieträger": "Holzpellets",
    "Endenergiebedarf": "64 kWh/(m²·a)",
    "Energieeffizienzklasse": "B",
}


# ---------- Listing definitions ----------
# "images": file names in the source folder, in display order.

LISTINGS = [
    {
        "slug": "wohnung-etagenwohnung-in-gechingen-mieten-20261105",
        "source": "talaue_gechingen/media/talaue_miete_171838146",
        "images": [
            "bild_01_aussenansicht.jpg", "bild_05_wohn_und_essbereich.jpg",
            "bild_07_wohn_koch_und_essbereich.jpg", "bild_04_offener_wohnbereich.jpg",
            "bild_09_moderne_einbaukueche.jpg", "bild_12_balkon_mit_weitblick.jpg",
            "bild_10_separates_zimmer.jpg", "bild_11_weiteres_zimmer.jpg",
            "bild_13_badezimmer.jpg", "bild_14_zweites_badezimmer.jpg",
            "bild_15_abschliessbares_kellerabteil.jpg", "bild_02_aussenansicht.jpg",
            "bild_16_luftaufnahme.jpg", "bild_17_luftaufnahme.jpg",
            "grundriss_01_grundriss_2_obergeschoss.jpg",
        ],
        "data": {
            "title": "Erstbezug: 4-Zimmer-Wohnung in der obersten Etage mit Balkon und Weitblick",
            "headline": "75391 Gechingen, Etagenwohnung",
            "sort_key": "20261105",
            "description": {
                "Objektbeschreibung": (
                    "Diese 4-Zimmer-Wohnung liegt im 2. Obergeschoss und damit "
                    "auf der obersten Wohnetage eines Neubaus im Quartier Talaue. "
                    "Über Ihnen wohnt niemand, der Aufzug bringt Sie bis auf "
                    "Ihre Etage.\n"
                    "Auf 108,17 m² Wohnfläche bildet der helle Wohn-, Koch- und "
                    "Essbereich mit rund 43 m² das Herzstück. Von hier aus "
                    "betreten Sie den Balkon mit Blick ins Grüne. Drei weitere "
                    "Zimmer eignen sich als Schlaf-, Kinder-, Gäste- oder "
                    "Arbeitszimmer.\n"
                    "Zwei Bäder mit bodengleichen Duschen, ein Abstellraum in "
                    "der Wohnung und ein Kellerabteil bieten Komfort und "
                    "Stauraum. Zwei Tiefgaragenstellplätze gehören zur Wohnung."
                ),
                "Ausstattung": (
                    "Einbauküche (in der Miete enthalten), einzelraumgeregelte "
                    "Fußbodenheizung, Echtholzparkett in den Zimmern, "
                    "großformatige Fliesen in Wohn-/Kochbereich und Bädern, "
                    "elektrische Rollläden, Videogegensprechanlage mit "
                    "Farbdisplay. Die Wohnung ist barrierearm angelegt. "
                    "Geheizt wird über eine zentrale Holzpelletanlage "
                    "(Effizienzhaus 55)."
                ),
                "Sonstiges": (
                    "Die Nebenkosten sind eine monatliche Vorauszahlung "
                    "inklusive Heizung und Warmwasser und werden jährlich "
                    "abgerechnet. Die beiden Tiefgaragenstellplätze kosten "
                    "je 60 € im Monat. Haustiere nach Absprache."
                ),
            },
            "lage": LAGE_GECHINGEN,
            "specs": {
                "Objektdaten": {
                    "Objekt ID": "20261105",
                    "Kaltmiete": "1.677 €",
                    "Nebenkosten": "320 €",
                    "Heizkosten": "in Nebenkosten enthalten",
                    "Warmmiete": "1.997 €",
                    "Kaution": "3.354 € (2 Nettokaltmieten)",
                    "Preis/m²": "15,50 €/m²",
                    "Wohnfläche": "108,17 m²",
                    "Zimmer": "4",
                    "Badezimmer": "2",
                    "Etage": "2. Obergeschoss (oberste Etage)",
                    "Baujahr": "2026",
                    "Zustand": "Erstbezug",
                    "Ausstattung": "Gehobene Qualität",
                    "Verfügbar ab": "Sofort",
                    "Haustiere": "Nach Vereinbarung",
                    "Garage/Stellplatz": "2 Tiefgaragenstellplätze",
                    "Miete Stellplatz": "je 60 €",
                },
                "Ausstattung / Merkmale": [
                    "Balkon mit Blick ins Grüne",
                    "Einbauküche inklusive",
                    "Zwei Bäder mit bodengleichen Duschen",
                    "Personenaufzug",
                    "Barrierearm",
                    "Einzelraumgeregelte Fußbodenheizung",
                    "Echtholzparkett",
                    "Elektrische Rollläden",
                    "Videogegensprechanlage",
                    "Abstellraum in der Wohnung",
                    "Kellerabteil",
                    "Zwei Tiefgaragenstellplätze",
                ],
                "Energieausweis": ENERGIE_TALAUE_7,
            },
        },
    },
    {
        "slug": "wohnung-etagenwohnung-in-gechingen-mieten-20261104",
        "source": "talaue_gechingen/media/talaue_miete_171305473",
        "images": [
            "bild_10_kueche_essbereich.jpg", "bild_09_blick_zur_kueche.jpg",
            "bild_08_wohnbereich.jpg", "bild_07_wohnbereich_2.jpg",
            "bild_11_schicke_einbaukueche.jpg", "bild_12_kochfeld_mit_bora_abzug.jpg",
            "bild_04_grosser_balkon_in_sw_ausrichtung.jpg", "bild_05_unverbaubarer_weitblick.jpg",
            "bild_15_schlafzimmer_mit_zugang_zu_ensuite_bad.jpg", "bild_22_schlafzimmer_ii.jpg",
            "bild_21_schlafzimmer_ii_buero.jpg", "bild_17_badezimmer.jpg",
            "bild_18_duschbereich.jpg", "bild_16_badezimmer_ii.jpg",
            "bild_20_gaeste_wc_duschbad.jpg", "bild_19_gaeste_wc_duschbad_2.jpg",
            "bild_14_flur.jpg", "bild_13_abstellraum.jpg",
            "bild_02_whng_1_og_links.jpg", "bild_01_aussenansicht.jpg",
            "bild_06_zugang_zum_haus.jpg", "bild_03_unverbaubarer_weitblick_2.jpg",
            "grundriss_01_grundriss.jpg",
        ],
        "data": {
            "title": "Erstbezug in Aussichtslage: 4-Zimmer-Wohnung mit Südwest-Balkon",
            "headline": "75391 Gechingen, Etagenwohnung",
            "sort_key": "20261104",
            "description": {
                "Objektbeschreibung": (
                    "Hochwertig ausgestattete 4-Zimmer-Wohnung im 1. Obergeschoss "
                    "eines Neubaus mit sieben Wohnungen, in naturnaher Ortsrandlage "
                    "mit unverbaubarem Blick über die Felder.\n"
                    "Der offene Wohn-, Koch- und Essbereich führt auf den großen "
                    "Balkon in Südwest-Ausrichtung. Das Schlafzimmer hat ein "
                    "eigenes Duschbad, dazu kommen zwei weitere Zimmer, etwa für "
                    "Kinder, Gäste oder das Homeoffice, sowie ein Gäste-WC mit "
                    "Dusche.\n"
                    "Ein Tiefgaragenstellplatz ist in der Miete enthalten. Im "
                    "Untergeschoss gibt es einen Kellerraum, einen großen "
                    "Fahrradraum und einen Stellplatz für Waschmaschine und "
                    "Trockner."
                ),
                "Ausstattung": (
                    "Heller Fliesenboden mit Fußbodenheizung in allen Räumen, "
                    "Wände in Glattputz, Deckeneinbaustrahler im Wohn-, Ess- und "
                    "Flurbereich. Hochwertige Einbauküche mit viel Stauraum, "
                    "Kühl-Gefrierkombination, Spülmaschine und Kochfeld mit "
                    "integriertem Dunstabzug. Duschbäder mit Regendusche, "
                    "Spiegelschrank und integrierter Beleuchtung. Aufzug im Haus."
                ),
                "Sonstiges": (
                    "Die Nebenkosten sind eine monatliche Vorauszahlung "
                    "inklusive Heizung und werden jährlich abgerechnet. "
                    "Haustiere sind nicht gestattet."
                ),
            },
            "lage": LAGE_GECHINGEN,
            "specs": {
                "Objektdaten": {
                    "Objekt ID": "20261104",
                    "Kaltmiete": "1.394 €",
                    "Nebenkosten": "300 €",
                    "Heizkosten": "in Nebenkosten enthalten",
                    "Warmmiete": "1.694 €",
                    "Kaution": "Nach Vereinbarung",
                    "Preis/m²": "15,50 €/m²",
                    "Wohnfläche": "89,91 m²",
                    "Zimmer": "4",
                    "Badezimmer": "2",
                    "Etage": "1. Obergeschoss",
                    "Baujahr": "2026",
                    "Zustand": "Erstbezug",
                    "Ausstattung": "Gehobene Qualität",
                    "Verfügbar ab": "Nach Vereinbarung",
                    "Haustiere": "Nein",
                    "Garage/Stellplatz": "1 Tiefgaragenstellplatz",
                    "Miete Stellplatz": "In der Miete enthalten",
                },
                "Ausstattung / Merkmale": [
                    "Großer Balkon in Südwest-Ausrichtung",
                    "Unverbaubarer Weitblick",
                    "Einbauküche mit Spülmaschine",
                    "Schlafzimmer mit eigenem Duschbad",
                    "Gäste-WC mit Dusche",
                    "Fußbodenheizung",
                    "Deckeneinbaustrahler",
                    "Personenaufzug",
                    "Abstellraum in der Wohnung",
                    "Kellerraum und Fahrradraum",
                    "Tiefgaragenstellplatz inklusive",
                ],
                "Energieausweis": ENERGIE_TALAUE_9,
            },
        },
    },
    {
        "slug": "wohnung-erdgeschosswohnung-in-gechingen-mieten-20261103",
        "source": "talaue_gechingen/media/talaue_miete_170773676",
        "images": [
            "bild_03_kueche.jpg", "bild_02_kueche.jpg", "bild_06_wohnzimmer.jpg",
            "bild_04_geplante_kueche.jpg", "bild_09_schlafzimmer.jpg",
            "bild_10_schlafzimmer.jpg", "bild_12_badezimmer.jpg",
            "bild_11_badezimmer.jpg", "bild_13_badezimmer.jpg", "bild_05_flur.jpg",
            "bild_08_flur.jpg", "bild_14_terrasse.jpg", "bild_15_terrasse.jpg",
            "bild_17_eingang.jpg", "bild_16_video_gegensprechanlage.jpg",
            "bild_01_ansicht.jpg",
            "grundriss_01_grundriss_dokument_2033_001_vermutlich_g.pdf",
        ],
        "data": {
            "title": "Neubau-Erstbezug: 2-Zimmer-Wohnung mit Terrasse und Garten",
            "headline": "75391 Gechingen, Erdgeschosswohnung",
            "sort_key": "20261103",
            "description": {
                "Objektbeschreibung": (
                    "Helle 2-Zimmer-Erdgeschosswohnung in einem Neubau im "
                    "Quartier Talaue, ideal für Singles oder Paare.\n"
                    "Der Wohn- und Essbereich mit neuer Einbauküche öffnet sich "
                    "zur sonnigen Terrasse mit Gartenanteil (ca. 37 m²). Auch "
                    "das Schlafzimmer hat einen Zugang zur Terrasse. Das Bad "
                    "hat eine bodengleiche Dusche und einen beleuchteten "
                    "Spiegelschrank.\n"
                    "Ein Tiefgaragenstellplatz und ein Kellerabteil gehören "
                    "dazu."
                ),
                "Ausstattung": (
                    "Moderne Einbauküche, hochwertiger Fliesenboden, "
                    "einzelraumgesteuerte Fußbodenheizung, Handtuchheizkörper, "
                    "Holz-Alu-Fenster, elektrische Rollläden, "
                    "Videogegensprechanlage mit Farbmonitor. Wohnanlage mit "
                    "Aufzug und Tiefgarage, ökologische Bauweise "
                    "(Effizienzhaus 55 EE)."
                ),
                "Sonstiges": (
                    "Die Nebenkosten sind eine monatliche Vorauszahlung "
                    "inklusive Heizung und werden jährlich abgerechnet. Der "
                    "Tiefgaragenstellplatz kostet 50 € im Monat. Haustiere "
                    "nach Absprache."
                ),
            },
            "lage": LAGE_GECHINGEN,
            "specs": {
                "Objektdaten": {
                    "Objekt ID": "20261103",
                    "Kaltmiete": "668 €",
                    "Nebenkosten": "240 €",
                    "Heizkosten": "in Nebenkosten enthalten",
                    "Warmmiete": "908 €",
                    "Kaution": "Nach Vereinbarung",
                    "Preis/m²": "17,75 €/m²",
                    "Wohnfläche": "37,64 m²",
                    "Zimmer": "2",
                    "Schlafzimmer": "1",
                    "Badezimmer": "1",
                    "Etage": "Erdgeschoss",
                    "Baujahr": "2026",
                    "Zustand": "Erstbezug",
                    "Ausstattung": "Gehobene Qualität",
                    "Verfügbar ab": "Nach Vereinbarung",
                    "Haustiere": "Nach Vereinbarung",
                    "Garage/Stellplatz": "1 Tiefgaragenstellplatz",
                    "Miete Stellplatz": "50 €",
                },
                "Ausstattung / Merkmale": [
                    "Terrasse mit Gartenanteil (ca. 37 m²)",
                    "Einbauküche",
                    "Bad mit bodengleicher Dusche",
                    "Einzelraumgesteuerte Fußbodenheizung",
                    "Holz-Alu-Fenster",
                    "Elektrische Rollläden",
                    "Videogegensprechanlage",
                    "Personenaufzug",
                    "Kellerabteil",
                    "Tiefgaragenstellplatz",
                ],
                "Energieausweis": ENERGIE_TALAUE_9,
            },
        },
    },
    {
        "slug": "wohnung-erdgeschosswohnung-in-calw-stammheim-mieten-20261102",
        "source": "waldhorn_calw_stammheim/media/waldhorn_whg01_miete",
        "images": [
            "bild_06_foto_2.jpg", "bild_05_foto_1.jpg", "bild_01_suedwest_ansicht.jpg",
            "bild_02_nordwest_ansicht.jpg", "bild_03_kueche_ansicht_oben_visualisierung.jpg",
            "bild_04_kueche_seite_visualisierung.jpg", "bild_07_foto_3.jpg",
            "bild_10_foto_6.jpg", "bild_11_foto_7.jpg", "bild_09_foto_5.jpg",
            "bild_12_foto_8.jpg",
            "grundriss_01_grundriss_wohnung_1_eg_deisling_expos_pd.pdf",
        ],
        "data": {
            "title": "Barrierefreie 3-Zimmer-Wohnung mit Terrasse und eigenem Garten",
            "headline": "75365 Calw-Stammheim, Erdgeschosswohnung",
            "sort_key": "20261102",
            "description": {
                "Objektbeschreibung": (
                    "Moderne, barrierefreie 3-Zimmer-Erdgeschosswohnung in einem "
                    "neuen Mehrfamilienhaus mit nur sechs Wohnungen im Ortskern "
                    "von Stammheim.\n"
                    "Der offene Wohn-, Ess- und Kochbereich (ca. 39 m²) führt "
                    "über eine große, bodentiefe Schiebetür auf die Terrasse und "
                    "in den eigenen Garten (Sondernutzungsrecht ca. 35 m²). Dazu "
                    "kommen ein Schlafzimmer, ein Kinder- oder Arbeitszimmer, "
                    "ein Bad mit Dusche und Badewanne, ein separates Gäste-WC "
                    "mit Waschmaschinenanschluss und ein Abstellraum.\n"
                    "Ein Kellerraum und ein Carport-Stellplatz direkt am Haus "
                    "gehören dazu."
                ),
                "Ausstattung": (
                    "Fußbodenheizung mit Wärmepumpe, hochwertiger Vinylboden "
                    "in Eiche hell, elektrische Rollläden, Videosprechanlage, "
                    "Handtuchheizkörper, Raumhöhe 2,60 m, keramische Platten "
                    "auf der Terrasse. Barrierefrei nach Landesbauordnung. "
                    "Eine Einbauküche mit Induktionskochfeld kann für 70 € im "
                    "Monat gemietet werden."
                ),
                "Sonstiges": (
                    "Die Nebenkosten sind eine monatliche Vorauszahlung "
                    "inklusive Heizung und werden jährlich abgerechnet. Der "
                    "Carport kostet 70 € im Monat. Haustiere sind nicht "
                    "gestattet. Die Küchenbilder sind Visualisierungen, die "
                    "Ansichten des Hauses unverbindliche Illustrationen."
                ),
            },
            "lage": LAGE_STAMMHEIM,
            "specs": {
                "Objektdaten": {
                    "Objekt ID": "20261102",
                    "Kaltmiete": "1.499 €",
                    "Nebenkosten": "200 €",
                    "Heizkosten": "in Nebenkosten enthalten",
                    "Warmmiete": "1.699 €",
                    "Kaution": "4.497 € (3 Nettokaltmieten)",
                    "Preis/m²": "16,20 €/m²",
                    "Wohnfläche": "92,50 m²",
                    "Zimmer": "3",
                    "Schlafzimmer": "2",
                    "Badezimmer": "1 + Gäste-WC",
                    "Etage": "Erdgeschoss",
                    "Baujahr": "2025",
                    "Zustand": "Neuwertig",
                    "Ausstattung": "Gehobene Qualität",
                    "Verfügbar ab": "Nach Vereinbarung",
                    "Haustiere": "Nein",
                    "Garage/Stellplatz": "1 Carport",
                    "Miete Stellplatz": "70 €",
                },
                "Ausstattung / Merkmale": [
                    "Terrasse mit eigenem Garten (ca. 35 m²)",
                    "Barrierefrei nach Landesbauordnung",
                    "Bad mit Dusche und Badewanne",
                    "Gäste-WC mit Waschmaschinenanschluss",
                    "Fußbodenheizung mit Wärmepumpe",
                    "Vinylboden Eiche hell",
                    "Elektrische Rollläden",
                    "Videosprechanlage",
                    "Abstellraum",
                    "Kellerraum",
                    "Carport",
                    "Einbauküche optional (70 €/Monat)",
                ],
                "Energieausweis": {
                    "Energieausweistyp": "Bedarfsausweis",
                    "Baujahr": "2025",
                    "Heizungsart": "Wärmepumpe, Fußbodenheizung",
                    "Wesentlicher Energieträger": "Strom",
                    "Endenergiebedarf": "14,9 kWh/(m²·a)",
                    "Energieeffizienzklasse": "A+",
                },
            },
        },
    },
    {
        "slug": "wohnung-etagenwohnung-in-gechingen-mieten-20261101",
        "source": "talaue_gechingen/media/talaue_miete_170192042",
        "images": [
            "bild_04_wohnzimmer.jpg", "bild_11_foto_img_8379.jpg",
            "bild_12_foto_img_8380.jpg", "bild_13_foto_img_8378.jpg",
            "bild_05_wohnzimmer.jpg", "bild_01_balkon.jpg", "bild_06_ausblick.jpg",
            "bild_07_schlafzimmer.jpg", "bild_08_kinderzimmer.jpg",
            "bild_03_badezimmer.jpg", "bild_09_gaeste_wc.jpg",
            "bild_10_foto_img_7990.jpg", "bild_02_talaue_visualisierung.jpg",
            "grundriss_01_hausansicht_als_grundriss_markiert.jpg",
        ],
        "data": {
            "title": "Erstbezug im 3. Obergeschoss: 3-Zimmer-Wohnung mit Kochinsel und Balkon",
            "headline": "75391 Gechingen, Etagenwohnung",
            "sort_key": "20261101",
            "description": {
                "Objektbeschreibung": (
                    "Moderne 3-Zimmer-Wohnung im 3. Obergeschoss eines Neubaus "
                    "im Quartier Talaue, mit Aufzug bequem erreichbar.\n"
                    "Auf 81 m² erwartet Sie ein offener Wohn- und Essbereich "
                    "mit hochwertiger Einbauküche und Kochinsel, ein großer "
                    "überdachter Balkon mit Weitblick, ein Schlafzimmer, ein "
                    "Kinder- oder Arbeitszimmer, ein Tageslichtbad mit "
                    "bodengleicher Dusche und ein separates Gäste-WC.\n"
                    "Ein Kellerabteil und ein Tiefgaragenstellplatz gehören "
                    "dazu."
                ),
                "Ausstattung": (
                    "Hochwertige Einbauküche mit Kochinsel, Echtholzparkett in "
                    "den Zimmern, großformatige Fliesen im Wohn- und "
                    "Kochbereich, Fußbodenheizung, bodentiefe Fenster, "
                    "Abstellraum. Die Wohnung ist barrierefrei erreichbar. "
                    "Geheizt wird über eine zentrale Holzpelletanlage."
                ),
                "Sonstiges": (
                    "Die Nebenkosten sind eine monatliche Vorauszahlung "
                    "inklusive Heizung und werden jährlich abgerechnet. Der "
                    "Tiefgaragenstellplatz kostet 50 € im Monat. Haustiere "
                    "sind nicht gestattet."
                ),
            },
            "lage": LAGE_GECHINGEN,
            "specs": {
                "Objektdaten": {
                    "Objekt ID": "20261101",
                    "Kaltmiete": "1.275 €",
                    "Nebenkosten": "270 €",
                    "Heizkosten": "in Nebenkosten enthalten",
                    "Warmmiete": "1.545 €",
                    "Kaution": "3.825 € (3 Nettokaltmieten)",
                    "Preis/m²": "15,74 €/m²",
                    "Wohnfläche": "81 m²",
                    "Zimmer": "3",
                    "Schlafzimmer": "2",
                    "Badezimmer": "1 + Gäste-WC",
                    "Etage": "3. Obergeschoss",
                    "Baujahr": "2026",
                    "Zustand": "Erstbezug",
                    "Ausstattung": "Gehobene Qualität",
                    "Verfügbar ab": "01.12.2026",
                    "Haustiere": "Nein",
                    "Garage/Stellplatz": "1 Tiefgaragenstellplatz",
                    "Miete Stellplatz": "50 €",
                },
                "Ausstattung / Merkmale": [
                    "Großer überdachter Balkon mit Weitblick",
                    "Einbauküche mit Kochinsel",
                    "Tageslichtbad mit bodengleicher Dusche",
                    "Separates Gäste-WC",
                    "Echtholzparkett",
                    "Fußbodenheizung",
                    "Personenaufzug",
                    "Barrierefrei erreichbar",
                    "Abstellraum",
                    "Kellerabteil",
                    "Tiefgaragenstellplatz",
                ],
                "Energieausweis": ENERGIE_TALAUE_7,
            },
        },
    },
]


# ---------- Helpers ----------

def load_image(src: Path) -> Image.Image:
    """Open a photo, or render page 1 of a PDF floor plan."""
    if src.suffix.lower() == ".pdf":
        doc = pymupdf.open(src)
        pix = doc[0].get_pixmap(dpi=150)
        return Image.open(io.BytesIO(pix.tobytes("png")))
    return Image.open(src)


def save_jpeg(img: Image.Image, dst: Path) -> None:
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, "white")
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    img.thumbnail((MAX_PX, MAX_PX))
    img.save(dst, "JPEG", quality=JPEG_QUALITY, optimize=True)


def write_listing(entry: dict) -> int:
    """Create listings/<slug>/ with data.json and a fresh images/ folder."""
    target_dir = LISTINGS_DIR / entry["slug"]
    images_dir = target_dir / "images"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Wipe existing images so re-runs don't accumulate duplicates.
    if images_dir.exists():
        shutil.rmtree(images_dir)
    images_dir.mkdir()

    src_dir = SOURCE_DIR / entry["source"]
    for i, name in enumerate(entry["images"], start=1):
        save_jpeg(load_image(src_dir / name), images_dir / f"{i:02d}.jpg")

    (target_dir / "data.json").write_text(
        json.dumps(entry["data"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(entry["images"])


def main() -> int:
    if not SOURCE_DIR.exists():
        print(f"! Source folder not found: {SOURCE_DIR}")
        return 1

    LISTINGS_DIR.mkdir(exist_ok=True)

    print(f"> Adding {len(LISTINGS)} Calw/Gechingen listings ...")
    for entry in LISTINGS:
        n = write_listing(entry)
        print(f"  [OK] {entry['slug']}  ({n} images)")

    print("\n> Done. Next step:  python build_site.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
