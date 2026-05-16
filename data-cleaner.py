import psycopg2
from datetime import datetime

DB = {
    "host": "localhost", "port": 5432,
    "dbname": "snapatask", "user": "snapatask_user",
    "password": "Sn4p4T4sk_DB_S3cur3_2026!xPq9"
}

PROVIDER_SIGNALS = [
    'we offer', 'we provide', 'fully licensed', 'man and van',
    'man & van', 'removal service', 'removal company', 'same day service',
    'professional removal', 'rubbish removal service', 'licensed waste',
    'book now', 'free quote', 'call us now', 'call now', 'no job too small'
]

print(f"=== DATA CLEANER {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")

try:
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    # 1. Delete fake phone records from contractor_leads
    cur.execute("DELETE FROM contractor_leads WHERE phone = '02604301904' AND company_name = ''")
    print(f"[1] Deleted {cur.rowcount} fake phone records from contractor_leads")

    # 2. Delete empty gumtree records from contractor_leads
    cur.execute("DELETE FROM contractor_leads WHERE company_name = '' AND lead_score IS NULL AND source_platform = 'gumtree'")
    print(f"[2] Deleted {cur.rowcount} empty gumtree records from contractor_leads")

    # 3. Delete irrelevant customer leads (wrong category)
    IRRELEVANT_SIGNALS = [
        'stress ball', 'iphone', 'apple', 'cassette', 'car jump',
        'selling', 'for sale', 'sports', 'job lot', 'accordion',
        'videograph', 'chinese restaurant', 'scrap metal'
    ]
    irr_sql = ' OR '.join([f"post_title ILIKE '%{s}%'" for s in IRRELEVANT_SIGNALS])
    cur.execute(f"DELETE FROM customer_leads WHERE {irr_sql}")
    print(f"[3a] Deleted {cur.rowcount} irrelevant customer leads")

    # 3b. Delete fake phone records from customer_leads
    cur.execute("DELETE FROM customer_leads WHERE phone IN ('02604301904', '073760481989')")
    print(f"[3] Deleted {cur.rowcount} fake phone records from customer_leads")

    # 4. Build provider signals SQL
    signals_sql = ' OR '.join([
        f"(post_title ILIKE '%{s}%' OR post_description ILIKE '%{s}%')"
        for s in PROVIDER_SIGNALS
    ])

    # 5. Move misclassified providers from customer_leads to contractor_leads
    cur.execute(f"""
        INSERT INTO contractor_leads (
            source_platform, source_url, company_name, contact_name,
            phone, email, location, services_offered, contact_status, created_at
        )
        SELECT 
            source_platform, source_url,
            COALESCE(NULLIF(customer_name,''), post_title),
            customer_name, phone, email, location,
            post_title, 'new', created_at
        FROM customer_leads
        WHERE {signals_sql}
        ON CONFLICT (source_url) DO NOTHING
    """)
    moved = cur.rowcount

    cur.execute(f"DELETE FROM customer_leads WHERE {signals_sql}")
    print(f"[4] Moved {moved} misclassified providers to contractor_leads")

    # 6. Final counts
    cur.execute("SELECT COUNT(*) FROM contractor_leads")
    contractors = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM customer_leads")
    customers = cur.fetchone()[0]
    print(f"[5] Final: {contractors} contractors | {customers} customers")

    conn.commit()
    cur.close()
    conn.close()
    print("=== CLEANUP COMPLETE ===")

except Exception as e:
    print(f"ERROR: {e}")
    raise
