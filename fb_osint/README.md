# FB Public OSINT

Tool CLI + web që mbledh **informata publike** nga faqet e Facebook-ut përmes **Meta Graph API** dhe i filtrin sipas temës që jep useri.

## Çfarë bën

- Lexon metadata publike të faqeve (emër, kategori, fans, about, link)
- Merr postime publike të faqeve (mesazh, engagement, permalink)
- Filtron / skoron postimet sipas temës ose fjalëkyçeve
- Nxjerr statistika: hits, reactions, comments, shares, top posts, top terms

## Çfarë NUK bën

- Nuk bën scraping të `facebook.com`
- Nuk lexon DM, profile private, apo përmbajtje jo-publike
- Nuk anashkalon login / rate limits / mbrojtje të platformës

Për akses real duhet app Meta + access token me lejet e duhura (p.sh. për faqe që menaxhon, ose Page Public Content Access kur Meta e ka aprovuar).

## Setup

```bash
cd fb_osint
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# vendos FACEBOOK_ACCESS_TOKEN në .env
```

## CLI

```bash
# me faqe eksplicite (rekomanduar)
python run_cli.py scan "energi e rinovueshme" --pages "Meta,bbcnews" --out report.json

# info për një faqe
python run_cli.py page Meta
```

Nëse nuk jep `--pages`, tool-i provon `pages/search` (shpesh i kufizuar nga lejet e app-it). Më e besueshme është lista e faqeve publike që i njeh ti.

## Web UI

```bash
python run_web.py
# hap http://127.0.0.1:8000
```

API JSON:

```bash
curl -X POST http://127.0.0.1:8000/api/scan \
  -H 'Content-Type: application/json' \
  -d '{"theme":"solar energy","pages":["Meta"],"posts_per_page":20}'
```

## Teste (offline, pa token)

```bash
pytest -q
```

## Si të marrësh token

1. Hap [Meta for Developers](https://developers.facebook.com/)
2. Krijo një app
3. Gjenero User/Page Access Token
4. Vendose në `.env` si `FACEBOOK_ACCESS_TOKEN`

Shënim: Meta ka kufizuar shumë search-in publik. Për OSINT tematik të qëndrueshëm, jep faqe publike relevante me `--pages` dhe lëri analyzer-in të filtrojë sipas temës.
