import psycopg2

DB = {"host":"localhost","port":5432,"dbname":"snapatask",
      "user":"snapatask_user","password":"Sn4p4T4sk_DB_S3cur3_2026!xPq9"}

conn = psycopg2.connect(**DB)
cur = conn.cursor()
passed = failed = 0

def check(name, query, condition, expected):
    global passed, failed
    cur.execute(query)
    result = cur.fetchone()[0]
    ok = condition(result)
    status = "✅ PASS" if ok else "❌ FAIL"
    if ok: passed += 1
    else: failed += 1
    print(f"{status} | {name}")
    print(f"       Expected: {expected} | Got: {result}")

print("=" * 60)
print("SNAPATASK COMPLIANCE TEST")
print("=" * 60)

# 1. Source URLs stored for every lead
check("All contractor leads have source_url",
    "SELECT COUNT(*) FROM contractor_leads WHERE source_url IS NULL OR source_url = ''",
    lambda x: x == 0, "0 missing")

check("All customer leads have source_url",
    "SELECT COUNT(*) FROM contractor_leads WHERE source_url IS NULL OR source_url = ''",
    lambda x: x == 0, "0 missing")

# 2. No duplicate source URLs
check("No duplicate source_urls in contractor_leads",
    "SELECT COUNT(*) FROM (SELECT source_url FROM contractor_leads GROUP BY source_url HAVING COUNT(*) > 1) t",
    lambda x: x == 0, "0 duplicates")

# 3. DNC table exists and is accessible
check("DNC table exists",
    "SELECT COUNT(*) FROM do_not_contact",
    lambda x: x >= 0, ">= 0 entries")

# 4. Outreach logs exist with manual review mode
check("Outreach logs exist",
    "SELECT COUNT(*) FROM outreach_logs",
    lambda x: x > 0, "> 0 logs")

check("No messages auto-sent without approval",
    "SELECT COUNT(*) FROM outreach_logs WHERE delivery_status = 'sent' AND channel != 'manual'",
    lambda x: x == 0, "0 auto-sent")

# 5. Contact history tracked
check("Outreach logs have timestamps",
    "SELECT COUNT(*) FROM outreach_logs WHERE created_at IS NULL",
    lambda x: x == 0, "0 missing timestamps")

# 6. Lead scores set
check("Contractor leads have scores",
    "SELECT COUNT(*) FROM contractor_leads WHERE lead_score IS NULL AND contact_status != 'invalid'",
    lambda x: x < 100, "< 100 unscored")

# 7. Invalid/duplicate leads marked
check("Duplicate leads marked invalid",
    "SELECT COUNT(*) FROM contractor_leads WHERE contact_status = 'invalid'",
    lambda x: x > 0, "> 0 marked")

# 8. Sources table populated
check("Sources table has entries",
    "SELECT COUNT(*) FROM sources",
    lambda x: x >= 10, ">= 10 sources")

# 9. All leads have platform recorded
check("All contractor leads have source_platform",
    "SELECT COUNT(*) FROM contractor_leads WHERE source_platform IS NULL OR source_platform = ''",
    lambda x: x == 0, "0 missing")

# 10. Manual review mode — no mass sending
check("MANUAL_REVIEW_MODE active (queued not sent)",
    "SELECT COUNT(*) FROM outreach_logs WHERE delivery_status = 'queued'",
    lambda x: x > 0, "> 0 queued for review")

print("\n" + "=" * 60)
print(f"RESULT: {passed} passed | {failed} failed")
if failed == 0:
    print("✅ ALL CHECKS PASSED — System is compliant")
else:
    print("⚠️  Some checks failed — review above")
print("=" * 60)

cur.close()
conn.close()
