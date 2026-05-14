import json, re
import psycopg2

DB = {"host":"localhost","port":5432,"dbname":"snapatask",
      "user":"snapatask_user","password":"Sn4p4T4sk_DB_S3cur3_2026!xPq9"}

with open('/tmp/leads.json') as f:
    leads = json.load(f)

conn = psycopg2.connect(**DB)
cur = conn.cursor()
saved = skipped = errors = 0

for lead in leads:
    # Clean phone - skip Gumtree placeholder
    phone = lead.get('phone','')
    if phone == '02604301904':
        phone = ''

    # Detect licence mention
    desc = (lead.get('post_description','') or '').lower()
    title = (lead.get('post_title','') or '').lower()
    licensed = any(w in desc+title for w in
        ['licensed','licence','waste carrier','cbdu','registered','insured'])

    try:
        cur.execute("""
            INSERT INTO contractor_leads
            (source_platform, source_url, company_name, phone,
             location, services_offered, licence_mentioned, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT ON CONSTRAINT uq_contractor_leads_source_url DO NOTHING
        """, (
            lead.get('source_platform','gumtree'),
            lead.get('source_url',''),
            (lead.get('post_title','') or '')[:255],
            phone[:50] if phone else '',
            (lead.get('location','London') or 'London')[:255],
            (lead.get('post_description','') or '')[:1000],
            licensed,
            'Scraped from Gumtree removal-services'
        ))
        if cur.rowcount > 0:
            saved += 1
        else:
            skipped += 1
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        errors += 1

conn.commit()
cur.close()
conn.close()
print(f"✓ Contractor leads — Saved: {saved} | Skipped: {skipped} | Errors: {errors}")
