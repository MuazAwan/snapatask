import json, time, re
from scrapling.fetchers import StealthyFetcher
import psycopg2

DB = {
    "host": "localhost", "port": 5432,
    "dbname": "snapatask", "user": "snapatask_user",
    "password": "Sn4p4T4sk_DB_S3cur3_2026!xPq9"
}

def fetch(url):
    time.sleep(3)
    return StealthyFetcher.fetch(
        url, headless=True, block_webrtc=True,
        hide_canvas=True, network_idle=True, google_search=True
    )

def get_listing_urls():
    print("Fetching search result pages...")
    urls = []
    search_queries = [
        "rubbish+removal+needed",
        "house+clearance+needed",
        "junk+removal+wanted"
    ]
    for query in search_queries:
        for page_num in range(1, 3):
            url = f"https://www.gumtree.com/search?q={query}&search_location=London&page={page_num}&search_category=for-sale&subcategory=wanted"
            print(f"  Searching: {url[:80]}")
            try:
                page = fetch(url)
                html = page.body.decode('utf-8', errors='ignore')
                found = re.findall(r'href="(/p/[^"]+/\d+)"', html)
                for f in found:
                    full = "https://www.gumtree.com" + f
                    if full not in urls:
                        urls.append(full)
                print(f"  → Found {len(found)} listings (total so far: {len(urls)})")
            except Exception as e:
                print(f"  ✗ Search error: {e}")
    print(f"\nTotal unique listing URLs: {len(urls)}")
    return urls

def extract_postcode(text):
    match = re.search(r'\b([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})\b', text, re.I)
    return match.group(1).upper() if match else ""

def scrape_listing(url):
    page = fetch(url)
    html = page.body.decode('utf-8', errors='ignore')

    # Title
    title = re.search(r'<h1[^>]*>\s*([^<]+)\s*</h1>', html)
    title = title.group(1).strip() if title else ""

    # Description - try multiple patterns
    desc = re.search(r'"description"\s*:\s*"([^"]{20,})"', html)
    if not desc:
        desc = re.search(r'class="[^"]*description[^"]*"[^>]*>\s*([^<]{20,})', html)
    desc = desc.group(1).strip()[:1000] if desc else ""

    # Location
    location = re.search(r'"location"\s*:\s*"([^"]+)"', html)
    if not location:
        location = re.search(r'class="[^"]*location[^"]*"[^>]*>\s*([^<]+)', html)
    location = location.group(1).strip() if location else "London"

    # Postcode
    postcode = extract_postcode(html)

    # Phone
    phone = re.search(r'(\+44[\d\s\-]{9,}|07[\d\s\-]{9,}|0[\d\s\-]{10,})', html)
    phone = re.sub(r'\s+', ' ', phone.group(0).strip())[:20] if phone else ""

    # Email
    email = re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', html)
    email = email.group(0) if email else ""

    # Customer name
    name = re.search(r'"seller_name"\s*:\s*"([^"]+)"', html)
    if not name:
        name = re.search(r'class="[^"]*seller[^"]*name[^"]*"[^>]*>\s*([^<]+)', html)
    name = name.group(1).strip() if name else ""

    # Date posted
    date = re.search(r'"date_posted"\s*:\s*"([^"]+)"', html)
    if not date:
        date = re.search(r'datetime="([^"]+)"', html)
    date = date.group(1) if date else None

    # Urgency keywords
    desc_lower = (title + " " + desc).lower()
    urgency = "high" if any(w in desc_lower for w in ["urgent", "asap", "immediately", "today"]) else "normal"

    return {
        "source_platform": "gumtree",
        "source_url": url,
        "customer_name": name,
        "phone": phone,
        "email": email,
        "location": location[:255],
        "postcode": postcode,
        "post_title": title,
        "post_description": desc,
        "job_type": "rubbish_removal",
        "urgency": urgency,
        "date_posted": date,
        "notes": f"Scraped by lead-scraper.py"
    }

def save_to_db(leads):
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    saved = 0
    skipped = 0
    for lead in leads:
        try:
            cur.execute("""
                INSERT INTO customer_leads
                (source_platform, source_url, customer_name, phone, email,
                 location, postcode, post_title, post_description,
                 job_type, urgency, date_posted, notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (source_url) DO NOTHING
            """, (
                lead['source_platform'], lead['source_url'],
                lead['customer_name'], lead['phone'], lead['email'],
                lead['location'], lead['postcode'], lead['post_title'],
                lead['post_description'], lead['job_type'],
                lead['urgency'], lead['date_posted'], lead['notes']
            ))
            if cur.rowcount > 0:
                saved += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  DB error for {lead['source_url'][:50]}: {e}")
    conn.commit()
    cur.close()
    conn.close()
    return saved, skipped

# ── MAIN ──────────────────────────────────────────────
print("=" * 50)
print("  SNAPATASK LEAD SCRAPER")
print("=" * 50)

urls = get_listing_urls()

if not urls:
    print("No URLs found. Check if Gumtree structure changed.")
    exit(1)

leads = []
for i, url in enumerate(urls[:30]):
    print(f"\n[{i+1}/{min(len(urls),30)}] {url[:70]}")
    try:
        lead = scrape_listing(url)
        leads.append(lead)
        print(f"  ✓ {lead['post_title'][:50] or 'No title'}")
        print(f"    Location: {lead['location']} | Urgency: {lead['urgency']}")
        if lead['phone']: print(f"    Phone: {lead['phone']}")
        if lead['email']: print(f"    Email: {lead['email']}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Save JSON backup always
with open('/tmp/leads.json', 'w') as f:
    json.dump(leads, f, indent=2)
print(f"\n✓ JSON backup saved: /tmp/leads.json ({len(leads)} leads)")

# Filter out service providers before saving
PROVIDER_SIGNALS = [
    'we offer', 'we provide', 'our services', 'call us', 'fully licensed',
    'man and van', 'man & van', 'removal company', 'removal service',
    'same day service', 'professional removal', 'house clearance service',
    'rubbish removal service', 'waste removal service', 'licensed waste',
    'book now', 'free quote', 'no job too small'
]

def is_provider(lead):
    text = ((lead.get('post_title') or '') + ' ' + (lead.get('post_description') or '')).lower()
    return any(signal in text for signal in PROVIDER_SIGNALS)

genuine_leads = [l for l in leads if not is_provider(l)]
provider_count = len(leads) - len(genuine_leads)
print(f"\n✓ Filtered out {provider_count} service provider ads")
leads = genuine_leads

# Save to PostgreSQL
print("\nSaving to PostgreSQL...")
try:
    saved, skipped = save_to_db(leads)
    print(f"✓ Saved: {saved} new leads | Skipped (duplicates): {skipped}")
except Exception as e:
    print(f"✗ DB error: {e}")

print("\n" + "=" * 50)
print(f"  DONE — {len(leads)} leads scraped")
print("=" * 50)
