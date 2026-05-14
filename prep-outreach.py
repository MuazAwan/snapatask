import psycopg2

DB = {"host":"localhost","port":5432,"dbname":"snapatask",
      "user":"snapatask_user","password":"Sn4p4T4sk_DB_S3cur3_2026!xPq9"}

CONTRACTOR_MSG = """Hi, I saw you offer rubbish removal services. We are launching Snapatask, a platform where local rubbish removal contractors can register for free and receive job leads from customers. Registration is free. Would you like me to send you the link?"""

conn = psycopg2.connect(**DB)
cur = conn.cursor()

cur.execute("""
    SELECT id, company_name, location, source_url, lead_score
    FROM contractor_leads
    WHERE contact_status = 'new'
    ORDER BY lead_score DESC
""")
leads = cur.fetchall()
print(f"Contractors to queue: {len(leads)}")
print("="*60)

queued = errors = 0
for lead in leads:
    lid, name, loc, url, score = lead
    try:
        cur.execute("""
            INSERT INTO outreach_logs
            (lead_type, lead_id, channel, message_template,
             message_body, delivery_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            'contractor',
            str(lid),
            'manual',
            'contractor_invite_v1',
            CONTRACTOR_MSG,
            'queued'
        ))

        cur.execute("""
            UPDATE contractor_leads
            SET contact_status = 'contacted',
                message_sent = %s,
                message_channel = 'manual',
                notes = COALESCE(notes,'') || ' | Queued for manual review'
            WHERE id = %s
        """, (CONTRACTOR_MSG, lid))

        queued += 1
        print(f"✓ [{score}/10] {str(name)[:55]}")
        print(f"   {loc}")
    except Exception as e:
        print(f"✗ Error: {e}")
        conn.rollback()
        errors += 1

conn.commit()
cur.close()
conn.close()
print(f"\n{'='*60}")
print(f"✓ Queued: {queued} | Errors: {errors}")
print(f"MANUAL_REVIEW_MODE=true — nothing sent automatically")
