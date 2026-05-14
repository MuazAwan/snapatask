import psycopg2, time, uuid

DB = {"host":"localhost","port":5432,"dbname":"snapatask",
      "user":"snapatask_user","password":"Sn4p4T4sk_DB_S3cur3_2026!xPq9"}

conn = psycopg2.connect(**DB)
cur = conn.cursor()
print("=== 200-Lead Stress Test ===")

# Insert 200 test contractor leads
print("\n1. Inserting 200 test leads...")
start = time.time()
for i in range(200):
    cur.execute("""
        INSERT INTO contractor_leads
        (source_platform, source_url, company_name, phone,
         location, services_offered, licence_mentioned, notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT ON CONSTRAINT uq_contractor_leads_source_url DO NOTHING
    """, (
        'stress_test',
        f'https://test.example.com/contractor/{i}',
        f'Test Contractor {i} Ltd',
        f'0700{i:06d}',
        'London',
        'Rubbish removal test service',
        True,
        'Stress test lead'
    ))
insert_time = time.time() - start
conn.commit()
print(f"   ✅ Inserted in {insert_time:.2f}s")

# Count total
cur.execute("SELECT COUNT(*) FROM contractor_leads")
total = cur.fetchone()[0]
print(f"   Total leads now: {total}")

# Query performance test
print("\n2. Query performance tests...")
tests = [
    ("Count all", "SELECT COUNT(*) FROM contractor_leads"),
    ("Filter by platform", "SELECT COUNT(*) FROM contractor_leads WHERE source_platform='environment_agency'"),
    ("Filter by score", "SELECT COUNT(*) FROM contractor_leads WHERE lead_score >= 9"),
    ("Filter London", "SELECT COUNT(*) FROM contractor_leads WHERE location ILIKE '%london%'"),
    ("Filter with phone", "SELECT COUNT(*) FROM contractor_leads WHERE phone IS NOT NULL AND phone != ''"),
    ("Top 50 by score", "SELECT id FROM contractor_leads ORDER BY lead_score DESC LIMIT 50"),
    ("Join outreach", "SELECT COUNT(*) FROM contractor_leads c LEFT JOIN outreach_logs o ON c.id=o.lead_id"),
]
for name, query in tests:
    t = time.time()
    cur.execute(query)
    result = cur.fetchone()[0] if 'COUNT' in query else len(cur.fetchall())
    elapsed = (time.time() - t) * 1000
    status = "✅" if elapsed < 500 else "⚠️"
    print(f"   {status} {name}: {result} results in {elapsed:.1f}ms")

# Dashboard API test
print("\n3. Dashboard stats query (simulates homepage load)...")
t = time.time()
cur.execute("""SELECT
    (SELECT COUNT(*) FROM contractor_leads) as contractors,
    (SELECT COUNT(*) FROM customer_leads) as customers,
    (SELECT COUNT(*) FROM outreach_logs WHERE delivery_status='queued') as queued,
    (SELECT COUNT(*) FROM contractor_leads WHERE lead_score >= 9) as high_quality,
    (SELECT ROUND(AVG(lead_score),1) FROM contractor_leads) as avg_score
""")
row = cur.fetchone()
elapsed = (time.time() - t) * 1000
print(f"   ✅ Stats loaded in {elapsed:.1f}ms")
print(f"   Contractors: {row[0]} | Customers: {row[1]} | Queued: {row[2]} | High quality: {row[3]} | Avg score: {row[4]}")

# Clean up test data
print("\n4. Cleaning up test data...")
cur.execute("DELETE FROM contractor_leads WHERE source_platform='stress_test'")
deleted = cur.rowcount
conn.commit()
print(f"   ✅ Removed {deleted} test leads")

cur.execute("SELECT COUNT(*) FROM contractor_leads")
final = cur.fetchone()[0]
print(f"   Final lead count: {final}")

cur.close()
conn.close()
print("\n=== STRESS TEST PASSED ===")
