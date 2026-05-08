import re, time, psycopg2
from scrapling.fetchers import StealthyFetcher

DB = {"host":"localhost","port":5432,"dbname":"snapatask",
      "user":"snapatask_user","password":"Sn4p4T4sk_DB_S3cur3_2026!xPq9"}

def fetch(url, wait=3):
    time.sleep(wait)
    return StealthyFetcher.fetch(
        url, headless=True, block_webrtc=True,
        hide_canvas=True, network_idle=True, google_search=True
    )

# Step 1 — Get all trader slugs from search pages
print("=== Checkatrade Contractor Scraper ===")
trader_urls = set()
search_pages = [
    'https://www.checkatrade.com/Search/Rubbish-Waste-Clearance/in/London',
    'https://www.checkatrade.com/Search/Rubbish-Waste-Clearance/in/London?page=2',
    'https://www.checkatrade.com/Search/Rubbish-Waste-Clearance/in/London?page=3',
    'https://www.checkatrade.com/Search/Rubbish-Waste-Clearance/in/London?page=4',
    'https://www.checkatrade.com/Search/Rubbish-Waste-Clearance/in/London?page=5',
    'https://www.checkatrade.com/Search/House-Clearances/in/London',
    'https://www.checkatrade.com/Search/House-Clearances/in/London?page=2',
    'https://www.checkatrade.com/Search/Garden-Clearances/in/London',
]

for url in search_pages:
    try:
        print(f"\nSearching: {url[-50:]}")
        page = fetch(url, wait=4)
        html = page.body.decode('utf-8', errors='ignore')
        slugs = re.findall(r'"https://www\.checkatrade\.com/trades/([^"]+)"', html)
        for slug in slugs:
            if slug and '?' not in slug:
                trader_urls.add(f"https://www.checkatrade.com/trades/{slug}")
        print(f"  Found {len(slugs)} traders | Total unique: {len(trader_urls)}")
    except Exception as e:
        print(f"  Error: {e}")

print(f"\nTotal unique trader profiles: {len(trader_urls)}")

# Step 2 — Visit each trader profile and extract data
leads = []
conn = psycopg2.connect(**DB)
cur = conn.cursor()
saved = skipped = errors = 0

for i, url in enumerate(list(trader_urls)):
    print(f"\n[{i+1}/{len(trader_urls)}] {url}")
    try:
        page = fetch(url, wait=3)
        html = page.body.decode('utf-8', errors='ignore')

        # Company name
        name_m = re.search(r'<h1[^>]*>([^<]{3,100})</h1>', html)
        if not name_m:
            name_m = re.search(r'"tradingName"\s*:\s*"([^"]{3,100})"', html)
        company = name_m.group(1).strip() if name_m else ''

        # Phone
        phone_m = re.search(r'(0[12378]\d[\d\s]{8,14})', html)
        phone = phone_m.group(0).strip()[:20] if phone_m else ''

        # Location
        loc_m = re.search(r'"(?:area|location|town|city)"\s*:\s*"([^"]{3,60})"', html)
        if not loc_m:
            loc_m = re.search(r'Based in[^<]*<[^>]+>([^<]{3,60})', html)
        location = loc_m.group(1).strip() if loc_m else 'London'

        # Postcode
        pc_m = re.search(r'\b([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})\b', html)
        postcode = pc_m.group(1).upper() if pc_m else ''

        # Website
        web_m = re.search(r'"website"\s*:\s*"(https?://[^"]{5,100})"', html)
        website = web_m.group(1) if web_m else ''

        # Review count + score
        rev_m = re.search(r'"reviewCount"\s*:\s*(\d+)', html)
        reviews = int(rev_m.group(1)) if rev_m else 0

        score_m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
        score = float(score_m.group(1)) if score_m else 0

        # Services
        services = f"Rubbish/Waste Clearance. Checkatrade verified. Reviews: {reviews}. Score: {score}"

        if not company:
            print(f"  ✗ No company name found")
            continue

        print(f"  ✓ {company[:55]}")
        if phone: print(f"    Phone: {phone}")
        if location: print(f"    Location: {location}")

        cur.execute("""
            INSERT INTO contractor_leads
            (source_platform, source_url, company_name, phone,
             website, location, services_offered, licence_mentioned, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT ON CONSTRAINT uq_contractor_leads_source_url DO NOTHING
        """, (
            'checkatrade', url,
            company[:255], phone,
            website[:500] if website else None,
            location[:255],
            services[:1000],
            False,
            f"Checkatrade verified. {reviews} reviews. Score: {score}"
        ))
        if cur.rowcount > 0:
            saved += 1
            conn.commit()
        else:
            skipped += 1

    except Exception as e:
        print(f"  ✗ Error: {e}")
        errors += 1
        conn.rollback()

cur.close()
conn.close()

print(f"\n{'='*50}")
print(f"✓ Saved: {saved} | Skipped: {skipped} | Errors: {errors}")

# Final summary
conn = psycopg2.connect(**DB)
cur = conn.cursor()
cur.execute("SELECT source_platform, COUNT(*) FROM contractor_leads GROUP BY source_platform ORDER BY COUNT(*) DESC")
print(f"\nContractor leads by source:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")
cur.execute("SELECT COUNT(*) FROM contractor_leads")
print(f"Total: {cur.fetchone()[0]}")
cur.close()
conn.close()
print("=== DONE ===")
