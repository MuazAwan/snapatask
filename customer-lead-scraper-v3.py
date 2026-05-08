import json, time, re
import psycopg2
from scrapling.fetchers import StealthyFetcher

DB = {"host":"localhost","port":5432,"dbname":"snapatask",
      "user":"snapatask_user","password":"Sn4p4T4sk_DB_S3cur3_2026!xPq9"}

def fetch(url, wait=4):
    time.sleep(wait)
    return StealthyFetcher.fetch(
        url, headless=True, block_webrtc=True,
        hide_canvas=True, network_idle=True, google_search=True
    )

def postcode(text):
    m = re.search(r'\b([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})\b', text, re.I)
    return m.group(1).upper() if m else ''

CUSTOMER_KEYWORDS = [
    'needed','wanted','looking for','need someone','anyone recommend',
    'can someone','help needed','require a','seeking','asap','urgently need',
    'need a quote','get quotes','collection needed','clearance needed',
    'removal needed','someone to take','who can','does anyone know'
]

CONTRACTOR_KEYWORDS = [
    'we offer','we provide','call us','our service','fully licensed',
    'professional service','from £','£20ph','£30ph','we are a',
    'licensed waste','waste carrier','established','years experience',
    'same day service','free quotes','insured','licensed company',
    'call now','contact us','we cover','we operate'
]

def is_customer_post(title, desc):
    text = (title + ' ' + desc).lower()
    has_customer = any(w in text for w in CUSTOMER_KEYWORDS)
    has_contractor = any(w in text for w in CONTRACTOR_KEYWORDS)
    return has_customer and not has_contractor

leads = []
seen_urls = set()

# Client spec search terms
search_queries = [
    'rubbish+removal+needed',
    'waste+clearance+needed',
    'house+clearance+needed',
    'garden+waste+removal+needed',
    'rubbish+removal+wanted',
    'junk+removal+needed',
    'furniture+disposal+needed',
    'garage+clearance+needed',
    'someone+to+take+rubbish',
    'sofa+removal+needed',
    'man+with+van+wanted+rubbish',
    'office+clearance+needed',
]

print('=== Snapatask Customer Lead Scraper ===')
all_listing_urls = []

for query in search_queries:
    url = f"https://www.gumtree.com/search?q={query}&search_location=London"
    print(f"\nSearching: {query.replace('+', ' ')}")
    try:
        page = fetch(url)
        html = page.body.decode('utf-8', errors='ignore')
        found = re.findall(r'href="(/p/[^"]+/\d+)"', html)
        new = 0
        for f in found:
            full = "https://www.gumtree.com" + f
            if full not in seen_urls:
                seen_urls.add(full)
                all_listing_urls.append(full)
                new += 1
        print(f"  Found {len(found)} listings ({new} new unique)")
    except Exception as e:
        print(f"  Error: {e}")

print(f"\nTotal unique listings to check: {len(all_listing_urls)}")
print("Visiting each to filter customer posts...\n")

for i, url in enumerate(all_listing_urls[:50]):
    print(f"[{i+1}/{min(len(all_listing_urls),50)}] {url[:70]}")
    try:
        page = fetch(url)
        html = page.body.decode('utf-8', errors='ignore')

        title_m = re.search(r'<h1[^>]*>\s*([^<]+)\s*</h1>', html)
        title = title_m.group(1).strip() if title_m else ''

        desc_m = re.search(r'"description"\s*:\s*"([^"]{20,})"', html)
        if not desc_m:
            desc_m = re.search(r'itemprop="description"[^>]*>\s*([^<]{20,})', html)
        desc = desc_m.group(1).strip()[:1000] if desc_m else ''

        loc_m = re.search(r'"location"\s*:\s*"([^"]+)"', html)
        location = loc_m.group(1).strip() if loc_m else 'London'

        text = (title + ' ' + desc).lower()
        urgency = 'high' if any(w in text for w in
            ['urgent','asap','today','immediately','same day','quickly']) else 'normal'

        if is_customer_post(title, desc):
            phone_m = re.search(r'(07\d[\d\s]{8,})', html)
            phone = phone_m.group(0).replace(' ','')[:20] if phone_m else ''
            email_m = re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', html)
            email = email_m.group(0) if email_m else ''

            leads.append({
                'source_platform': 'gumtree',
                'source_url': url,
                'customer_name': '',
                'phone': phone,
                'email': email,
                'location': location[:255],
                'postcode': postcode(html),
                'post_title': title[:500],
                'post_description': desc,
                'job_type': 'rubbish_removal',
                'urgency': urgency,
                'date_posted': None,
                'notes': 'Gumtree customer wanted ad'
            })
            print(f"  ✓ CUSTOMER: {title[:60]}")
            print(f"    {location} | {urgency} urgency")
        else:
            print(f"  ✗ Contractor: {title[:55]}")

    except Exception as e:
        print(f"  ✗ Error: {e}")

# Save JSON backup
with open('/tmp/customer_leads_v3.json','w') as f:
    json.dump(leads, f, indent=2)

print(f'\n{"="*50}')
print(f'Customer leads found: {len(leads)}')
print(f'Backup: /tmp/customer_leads_v3.json')

# Save to DB
if leads:
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    saved = skipped = 0
    for lead in leads:
        try:
            cur.execute("""
                INSERT INTO customer_leads
                (source_platform, source_url, customer_name, phone, email,
                 location, postcode, post_title, post_description,
                 job_type, urgency, date_posted, notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT ON CONSTRAINT uq_customer_leads_source_url DO NOTHING
            """, (
                lead['source_platform'], lead['source_url'],
                lead['customer_name'], lead['phone'], lead['email'],
                lead['location'], lead['postcode'], lead['post_title'],
                lead['post_description'], lead['job_type'],
                lead['urgency'], lead['date_posted'], lead['notes']
            ))
            if cur.rowcount > 0: saved += 1
            else: skipped += 1
        except Exception as e:
            print(f"DB error: {e}")
            conn.rollback()
    conn.commit()
    cur.close()
    conn.close()
    print(f'✓ DB: Saved {saved} | Skipped {skipped}')
else:
    print('No customer posts found on Gumtree today.')
    print('Check /tmp/customer_leads_v3.json and page HTML for debugging.')

print('=== DONE ===')
