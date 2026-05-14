import time, re, json
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

def clean(text):
    return re.sub(r'<[^>]+>', ' ', text).strip()

leads = []
seen = set()

def add_lead(lead):
    if lead['source_url'] not in seen and lead['post_title']:
        seen.add(lead['source_url'])
        leads.append(lead)
        print(f"  ✓ {lead['post_title'][:65]}")
        print(f"    {lead['location']} | {lead['source_platform']}")

# ── SOURCE 1: LoveJunk London ─────────────────────────────────
print('\n[1/4] LoveJunk — rubbish collection requests...')
lovejunk_urls = [
    'https://www.lovejunk.com/london/',
    'https://www.lovejunk.com/london/furniture/',
    'https://www.lovejunk.com/london/garden-waste/',
    'https://www.lovejunk.com/london/household-waste/',
]
for url in lovejunk_urls:
    try:
        page = fetch(url)
        html = page.body.decode('utf-8', errors='ignore')
        with open('/tmp/lovejunk_debug.html','w') as f: f.write(html)
        # Extract listing links
        links = re.findall(r'href="(https://www\.lovejunk\.com/[^"]+/item/[^"]+)"', html)
        links += re.findall(r'href="(/[^"]+/item/[^"]+)"', html)
        print(f"  Found {len(links)} listings at {url[-40:]}")
        for link in links[:8]:
            full = link if link.startswith('http') else 'https://www.lovejunk.com' + link
            if full in seen: continue
            try:
                lp = fetch(full, wait=3)
                lhtml = lp.body.decode('utf-8', errors='ignore')
                title_m = re.search(r'<h1[^>]*>([^<]+)</h1>', lhtml)
                desc_m = re.search(r'"description"\s*:\s*"([^"]{20,})"', lhtml)
                loc_m = re.search(r'(?:London|[A-Z]{1,2}\d{1,2})', lhtml)
                phone_m = re.search(r'(07[\d\s]{9,})', lhtml)
                title = clean(title_m.group(1)) if title_m else ''
                text = (title + ' ' + (desc_m.group(1) if desc_m else '')).lower()
                urgency = 'high' if any(w in text for w in ['urgent','asap','today','quickly']) else 'normal'
                add_lead({
                    'source_platform': 'lovejunk',
                    'source_url': full,
                    'customer_name': '',
                    'phone': phone_m.group(0)[:20] if phone_m else '',
                    'email': '',
                    'location': 'London',
                    'postcode': postcode(lhtml),
                    'post_title': title[:500],
                    'post_description': clean(desc_m.group(1))[:1000] if desc_m else '',
                    'job_type': 'rubbish_removal',
                    'urgency': urgency,
                    'date_posted': None,
                    'notes': 'LoveJunk London listing'
                })
            except Exception as e:
                print(f"    ✗ {e}")
    except Exception as e:
        print(f"  Error: {e}")

# ── SOURCE 2: TrashNothing London groups ──────────────────────
print('\n[2/4] TrashNothing — London Freegle/Freecycle wanted posts...')
trash_urls = [
    'https://trashnothing.com/beta/browse?search=rubbish+removal&lat=51.5074&lng=-0.1278&radius=30',
    'https://trashnothing.com/beta/browse?search=clearance+needed&lat=51.5074&lng=-0.1278&radius=30',
    'https://trashnothing.com/beta/browse?search=collect+furniture&lat=51.5074&lng=-0.1278&radius=30',
    'https://trashnothing.com/beta/browse?search=take+away+rubbish&lat=51.5074&lng=-0.1278&radius=30',
]
for url in trash_urls:
    try:
        page = fetch(url)
        html = page.body.decode('utf-8', errors='ignore')
        with open('/tmp/trash_debug.html','w') as f: f.write(html)
        links = re.findall(r'href="(https://trashnothing\.com/[^"]+/post/[^"]+)"', html)
        links += re.findall(r'href="(/[a-z/]+/post/[^"]+)"', html)
        print(f"  Found {len(links)} posts")
        for link in links[:8]:
            full = link if link.startswith('http') else 'https://trashnothing.com' + link
            if full in seen: continue
            try:
                lp = fetch(full, wait=3)
                lhtml = lp.body.decode('utf-8', errors='ignore')
                title_m = re.search(r'<h1[^>]*>([^<]+)</h1>', lhtml)
                desc_m = re.search(r'class="[^"]*post[^"]*body[^"]*"[^>]*>([\s\S]{20,200}?)</div>', lhtml)
                if not desc_m:
                    desc_m = re.search(r'"description"\s*:\s*"([^"]{20,})"', lhtml)
                title = clean(title_m.group(1)) if title_m else ''
                if not title: continue
                add_lead({
                    'source_platform': 'trashnothing',
                    'source_url': full,
                    'customer_name': '',
                    'phone': '',
                    'email': '',
                    'location': 'London',
                    'postcode': postcode(lhtml),
                    'post_title': title[:500],
                    'post_description': clean(desc_m.group(1))[:1000] if desc_m else '',
                    'job_type': 'rubbish_removal',
                    'urgency': 'normal',
                    'date_posted': None,
                    'notes': 'TrashNothing London group post'
                })
            except Exception as e:
                print(f"    ✗ {e}")
    except Exception as e:
        print(f"  Error: {e}")

# ── SOURCE 3: Gumtree for-sale/stuff-wanted ───────────────────
print('\n[3/4] Gumtree — for-sale/stuff-wanted section...')
gumtree_urls = [
    'https://www.gumtree.com/for-sale/stuff-wanted/london?q=rubbish+removal',
    'https://www.gumtree.com/for-sale/stuff-wanted/london?q=clearance',
    'https://www.gumtree.com/for-sale/stuff-wanted/london?q=furniture+collection',
    'https://www.gumtree.com/free-stuff/london?q=rubbish',
    'https://www.gumtree.com/free-stuff/london?q=collect',
]
for url in gumtree_urls:
    try:
        page = fetch(url)
        html = page.body.decode('utf-8', errors='ignore')
        links = re.findall(r'href="(/p/[^"]+/\d+)"', html)
        print(f"  Found {len(links)} listings")
        for link in links[:8]:
            full = 'https://www.gumtree.com' + link
            if full in seen: continue
            try:
                lp = fetch(full, wait=3)
                lhtml = lp.body.decode('utf-8', errors='ignore')
                title_m = re.search(r'<h1[^>]*>\s*([^<]+)\s*</h1>', lhtml)
                desc_m = re.search(r'"description"\s*:\s*"([^"]{20,})"', lhtml)
                loc_m = re.search(r'"location"\s*:\s*"([^"]+)"', lhtml)
                phone_m = re.search(r'(07\d[\d\s]{8,})', lhtml)
                title = title_m.group(1).strip() if title_m else ''
                desc = desc_m.group(1).strip() if desc_m else ''
                # Filter out contractor service ads
                text = (title+' '+desc).lower()
                if any(w in text for w in ['we offer','call now','from £','licensed waste',
                    'professional service','we provide','our team','we cover']):
                    print(f"    ✗ Contractor skipped: {title[:50]}")
                    continue
                urgency = 'high' if any(w in text for w in ['urgent','asap','today']) else 'normal'
                add_lead({
                    'source_platform': 'gumtree',
                    'source_url': full,
                    'customer_name': '',
                    'phone': phone_m.group(0)[:20] if phone_m else '',
                    'email': '',
                    'location': loc_m.group(1)[:255] if loc_m else 'London',
                    'postcode': postcode(lhtml),
                    'post_title': title[:500],
                    'post_description': desc[:1000],
                    'job_type': 'rubbish_removal',
                    'urgency': urgency,
                    'date_posted': None,
                    'notes': 'Gumtree for-sale/wanted'
                })
            except Exception as e:
                print(f"    ✗ {e}")
    except Exception as e:
        print(f"  Error: {e}")

# ── SOURCE 4: Freeads.co.uk ───────────────────────────────────
print('\n[4/4] Freeads.co.uk — wanted section...')
freeads_urls = [
    'https://www.freeads.co.uk/uk/search/for-sale/wanted/find?q=rubbish+removal&location=London',
    'https://www.freeads.co.uk/uk/search/for-sale/wanted/find?q=clearance&location=London',
    'https://www.freeads.co.uk/uk/search/for-sale/wanted/find?q=furniture+collection&location=London',
]
for url in freeads_urls:
    try:
        page = fetch(url)
        html = page.body.decode('utf-8', errors='ignore')
        links = re.findall(r'href="(https://www\.freeads\.co\.uk/[^"]+\d+[^"]*)"', html)
        print(f"  Found {len(links)} listings")
        for link in links[:8]:
            if link in seen: continue
            try:
                lp = fetch(link, wait=3)
                lhtml = lp.body.decode('utf-8', errors='ignore')
                title_m = re.search(r'<h1[^>]*>([^<]+)</h1>', lhtml)
                phone_m = re.search(r'(07[\d\s]{9,})', lhtml)
                title = clean(title_m.group(1)) if title_m else ''
                if not title: continue
                add_lead({
                    'source_platform': 'freeads',
                    'source_url': link,
                    'customer_name': '',
                    'phone': phone_m.group(0)[:20] if phone_m else '',
                    'email': '',
                    'location': 'London',
                    'postcode': postcode(lhtml),
                    'post_title': title[:500],
                    'post_description': '',
                    'job_type': 'rubbish_removal',
                    'urgency': 'normal',
                    'date_posted': None,
                    'notes': 'Freeads.co.uk wanted'
                })
            except Exception as e:
                print(f"    ✗ {e}")
    except Exception as e:
        print(f"  Error: {e}")

# ── SAVE ──────────────────────────────────────────────────────
print(f'\n{"="*55}')
print(f'Total customer leads found: {len(leads)}')
with open('/tmp/customer_leads_v4.json','w') as f:
    json.dump(leads, f, indent=2)
print('Backup: /tmp/customer_leads_v4.json')

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
            """, (lead['source_platform'], lead['source_url'],
                  lead['customer_name'], lead['phone'], lead['email'],
                  lead['location'], lead['postcode'], lead['post_title'],
                  lead['post_description'], lead['job_type'],
                  lead['urgency'], lead['date_posted'], lead['notes']))
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
    print('No leads found — check debug HTML files in /tmp/')

print('=== DONE ===')
