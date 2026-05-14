import json, time, re
from scrapling.fetchers import StealthyFetcher
import psycopg2

DB = {
    "host": "localhost", "port": 5432,
    "dbname": "snapatask", "user": "snapatask_user",
    "password": "Sn4p4T4sk_DB_S3cur3_2026!xPq9"
}

def fetch(url, wait=3):
    time.sleep(wait)
    return StealthyFetcher.fetch(
        url, headless=True, block_webrtc=True,
        hide_canvas=True, network_idle=True, google_search=True
    )

def extract_postcode(text):
    m = re.search(r'\b([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})\b', text, re.I)
    return m.group(1).upper() if m else ""

leads = []

# ── SOURCE 1: Gumtree "for-sale/stuff-wanted" section ──────────
print("\n[1/3] Scraping Gumtree wanted ads...")
wanted_urls = [
    "https://www.gumtree.com/for-sale/stuff-wanted/london?q=rubbish+removal",
    "https://www.gumtree.com/for-sale/stuff-wanted/london?q=house+clearance",
    "https://www.gumtree.com/for-sale/stuff-wanted/london?q=garden+clearance",
]
for url in wanted_urls:
    try:
        page = fetch(url)
        html = page.body.decode('utf-8', errors='ignore')
        # Save for inspection
        with open('/tmp/wanted_debug.html', 'w') as f:
            f.write(html)
        listing_urls = re.findall(r'href="(/p/[^"]+/\d+)"', html)
        print(f"  Found {len(listing_urls)} listings at {url[:60]}")
        for lu in listing_urls[:10]:
            full = "https://www.gumtree.com" + lu
            if full not in [l['source_url'] for l in leads]:
                try:
                    lp = fetch(full)
                    lhtml = lp.body.decode('utf-8', errors='ignore')
                    title = re.search(r'<h1[^>]*>\s*([^<]+)\s*</h1>', lhtml)
                    desc = re.search(r'"description"\s*:\s*"([^"]{20,})"', lhtml)
                    loc = re.search(r'"location"\s*:\s*"([^"]+)"', lhtml)
                    # Skip if it looks like a contractor offering service
                    title_text = title.group(1) if title else ""
                    if any(w in title_text.lower() for w in
                           ['we offer', 'we provide', 'call us', 'our service',
                            'fully licensed', 'professional service', '£20ph', 'from £']):
                        print(f"    ✗ Skipped (contractor): {title_text[:50]}")
                        continue
                    leads.append({
                        "source_platform": "gumtree_wanted",
                        "source_url": full,
                        "customer_name": "",
                        "phone": "",
                        "email": "",
                        "location": loc.group(1)[:255] if loc else "London",
                        "postcode": extract_postcode(lhtml),
                        "post_title": title_text.strip()[:500],
                        "post_description": desc.group(1)[:1000] if desc else "",
                        "job_type": "rubbish_removal",
                        "urgency": "normal",
                        "date_posted": None,
                        "notes": "Gumtree wanted section"
                    })
                    print(f"    ✓ {title_text[:60]}")
                except Exception as e:
                    print(f"    ✗ {e}")
    except Exception as e:
        print(f"  Error: {e}")

# ── SOURCE 2: Freeads.co.uk ─────────────────────────────────────
print("\n[2/3] Scraping Freeads.co.uk...")
freeads_urls = [
    "https://www.freeads.co.uk/uk/search/services/tradesmen-construction/find?q=rubbish+removal+needed&location=London",
    "https://www.freeads.co.uk/uk/search/services/tradesmen-construction/find?q=house+clearance+wanted&location=London",
]
for url in freeads_urls:
    try:
        page = fetch(url)
        html = page.body.decode('utf-8', errors='ignore')
        listing_urls = re.findall(r'href="(https://www\.freeads\.co\.uk/[^"]+/\d+[^"]*)"', html)
        print(f"  Found {len(listing_urls)} listings")
        for lu in listing_urls[:10]:
            try:
                lp = fetch(lu)
                lhtml = lp.body.decode('utf-8', errors='ignore')
                title = re.search(r'<h1[^>]*>\s*([^<]+)\s*</h1>', lhtml)
                desc = re.search(r'class="[^"]*description[^"]*"[^>]*>\s*([^<]{20,})', lhtml)
                phone = re.search(r'(07[\d\s]{9,}|0[\d\s]{10,})', lhtml)
                title_text = title.group(1).strip() if title else ""
                leads.append({
                    "source_platform": "freeads",
                    "source_url": lu,
                    "customer_name": "",
                    "phone": phone.group(0)[:20] if phone else "",
                    "email": "",
                    "location": "London",
                    "postcode": extract_postcode(lhtml),
                    "post_title": title_text,
                    "post_description": desc.group(1)[:1000] if desc else "",
                    "job_type": "rubbish_removal",
                    "urgency": "normal",
                    "date_posted": None,
                    "notes": "Freeads.co.uk"
                })
                print(f"    ✓ {title_text[:60]}")
            except Exception as e:
                print(f"    ✗ {e}")
    except Exception as e:
        print(f"  Freeads error: {e}")

# ── SOURCE 3: Friday-Ad.co.uk ───────────────────────────────────
print("\n[3/3] Scraping Friday-ad.co.uk...")
try:
    page = fetch("https://www.friday-ad.co.uk/london/for-sale/?q=rubbish+removal+wanted")
    html = page.body.decode('utf-8', errors='ignore')
    listing_urls = re.findall(r'href="(https://www\.friday-ad\.co\.uk/[^"]+)"', html)
    print(f"  Found {len(listing_urls)} listings")
    for lu in listing_urls[:10]:
        try:
            lp = fetch(lu)
            lhtml = lp.body.decode('utf-8', errors='ignore')
            title = re.search(r'<h1[^>]*>\s*([^<]+)\s*</h1>', lhtml)
            desc = re.search(r'class="[^"]*desc[^"]*"[^>]*>\s*([^<]{20,})', lhtml)
            phone = re.search(r'(07[\d\s]{9,})', lhtml)
            title_text = title.group(1).strip() if title else ""
            leads.append({
                "source_platform": "friday-ad",
                "source_url": lu,
                "customer_name": "",
                "phone": phone.group(0)[:20] if phone else "",
                "email": "",
                "location": "London",
                "postcode": extract_postcode(lhtml),
                "post_title": title_text,
                "post_description": desc.group(1)[:1000] if desc else "",
                "job_type": "rubbish_removal",
                "urgency": "normal",
                "date_posted": None,
                "notes": "Friday-ad.co.uk"
            })
            print(f"    ✓ {title_text[:60]}")
        except Exception as e:
            print(f"    ✗ {e}")
except Exception as e:
    print(f"  Friday-ad error: {e}")

# ── SAVE ────────────────────────────────────────────────────────
print(f"\nTotal leads found: {len(leads)}")
with open('/tmp/customer_leads.json', 'w') as f:
    json.dump(leads, f, indent=2)
print("Saved to /tmp/customer_leads.json")

if leads:
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    saved = 0
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
            if cur.rowcount > 0:
                saved += 1
        except Exception as e:
            print(f"DB error: {e}")
            conn.rollback()
    conn.commit()
    cur.close()
    conn.close()
    print(f"✓ Saved {saved} customer leads to PostgreSQL")

print("=== DONE ===")
