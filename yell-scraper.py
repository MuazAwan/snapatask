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

print("=== Yell.com Contractor Scraper ===")

# Step 1 — collect all /biz/ URLs from search pages
biz_urls = set()
search_pages = [
    'https://www.yell.com/s/rubbish+removal-london.html',
    'https://www.yell.com/s/rubbish+removal-london.html?page=2',
    'https://www.yell.com/s/rubbish+removal-london.html?page=3',
    'https://www.yell.com/s/rubbish+removal-london.html?page=4',
    'https://www.yell.com/s/rubbish+removal-london.html?page=5',
    'https://www.yell.com/s/waste+clearance-london.html',
    'https://www.yell.com/s/waste+clearance-london.html?page=2',
    'https://www.yell.com/s/house+clearance-london.html',
    'https://www.yell.com/s/house+clearance-london.html?page=2',
    'https://www.yell.com/s/junk+removal-london.html',
]

for url in search_pages:
    try:
        print(f"\nSearching: {url[-50:]}")
        page = fetch(url, wait=4)
        html = page.body.decode('utf-8', errors='ignore')
        found = re.findall(r'href="(/biz/[^"#]+/)"', html)
        # Deduplicate keeping only main listing URL
        for f in found:
            # Skip review/photo sub-pages
            if f.count('/') <= 3:
                biz_urls.add('https://www.yell.com' + f)
        print(f"  Status: {page.status} | Found: {len(found)} | Total unique: {len(biz_urls)}")
    except Exception as e:
        print(f"  Error: {e}")

print(f"\nTotal unique business profiles: {len(biz_urls)}")

# Step 2 — scrape each business profile
conn = psycopg2.connect(**DB)
cur = conn.cursor()
saved = skipped = errors = 0

for i, url in enumerate(list(biz_urls)):
    print(f"\n[{i+1}/{len(biz_urls)}] {url[-50:]}")
    try:
        page = fetch(url, wait=3)
        html = page.body.decode('utf-8', errors='ignore')
        if page.status != 200:
            print(f"  ✗ Status {page.status}")
            continue

        # Company name
        name_m = re.search(r'<h1[^>]*>([^<]{3,100})</h1>', html)
        if not name_m:
            name_m = re.search(r'"name"\s*:\s*"([^"]{5,80})"', html)
        company = name_m.group(1).strip() if name_m else ''
        if not company:
            print(f"  ✗ No name found")
            continue

        # Phone — from tel: link
        phone_m = re.search(r'href="tel:([^"]+)"', html)
        if not phone_m:
            phone_m = re.search(r'tel:([0-9\s+]{10,15})', html)
        phone = phone_m.group(1).strip()[:20] if phone_m else ''

        # Website
        web_m = re.search(r'"url"\s*:\s*"(https?://(?!www\.yell)[^"]{5,100})"', html)
        website = web_m.group(1) if web_m else ''

        # Location/address
        addr_m = re.search(r'itemprop="address"[^>]*>([^<]{5,100})', html)
        if not addr_m:
            addr_m = re.search(r'"addressLocality"\s*:\s*"([^"]+)"', html)
        location = addr_m.group(1).strip() if addr_m else 'London'

        # Postcode
        pc_m = re.search(r'\b([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})\b', html)
        postcode = pc_m.group(1).upper() if pc_m else ''

        # Rating + reviews
        rating_m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
        reviews_m = re.search(r'"reviewCount"\s*:\s*(\d+)', html)
        rating = float(rating_m.group(1)) if rating_m else 0
        reviews = int(reviews_m.group(1)) if reviews_m else 0

        services = f"Rubbish/Waste Removal. Yell.com listed. Rating: {rating}. Reviews: {reviews}"
        notes = f"Yell.com. Postcode: {postcode}. Rating: {rating}/5 ({reviews} reviews)"

        print(f"  ✓ {company[:55]}")
        if phone: print(f"    Phone: {phone}")
        print(f"    {location} | Rating: {rating}")

        cur.execute("""
            INSERT INTO contractor_leads
            (source_platform, source_url, company_name, phone,
             website, location, services_offered, licence_mentioned, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT ON CONSTRAINT uq_contractor_leads_source_url DO NOTHING
        """, (
            'yell',
            url,
            company[:255],
            phone,
            website[:500] if website else None,
            location[:255],
            services[:1000],
            False,
            notes[:500]
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
cur.execute("""
    SELECT source_platform, COUNT(*) as leads,
           ROUND(AVG(lead_score),1) as avg_score,
           COUNT(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 END) as with_phone
    FROM contractor_leads
    GROUP BY source_platform ORDER BY leads DESC
""")
print(f"\nContractor leads by source:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} leads | score {row[2]} | {row[3]} with phone")
cur.execute("SELECT COUNT(*) FROM contractor_leads")
print(f"\nTotal contractor leads: {cur.fetchone()[0]}")
cur.close()
conn.close()
print("=== DONE ===")
