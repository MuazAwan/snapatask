import os
import psycopg2
import urllib.request
import urllib.parse
import base64
import json
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = "+447782223060"

DB = {
    "host": "localhost", "port": 5432,
    "dbname": "snapatask", "user": "snapatask_user",
    "password": "Sn4p4T4sk_DB_S3cur3_2026!xPq9"
}

# ── HELPERS ─────────────────────────────────────────
def get_phone_number():
    """Get actual phone number from Twilio using Phone Number SID"""
    phone_sid = "PN881c45af18a66e622879f342669f65fb"
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers/{phone_sid}.json"
    req = urllib.request.Request(url)
    credentials = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    req.add_header("Authorization", f"Basic {credentials}")
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            return data.get("phone_number")
    except Exception as e:
        print(f"Error fetching phone number: {e}")
        return None

def send_sms(to_number, message, from_number):
    """Send SMS via Twilio API"""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    data = urllib.parse.urlencode({
        "To": to_number,
        "From": from_number,
        "Body": message
    }).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    credentials = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    req.add_header("Authorization", f"Basic {credentials}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            return result.get("sid"), None
    except urllib.error.HTTPError as e:
        error = json.loads(e.read())
        return None, error.get("message", str(e))

def format_phone(phone):
    """Convert UK phone to E.164 format"""
    phone = ''.join(filter(str.isdigit, phone))
    if phone.startswith('0'):
        phone = '44' + phone[1:]
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone

# ── MAIN ────────────────────────────────────────────
print(f"=== SMS SENDER {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")

# Get sending number
from_number = get_phone_number()
if not from_number:
    print("ERROR: Could not fetch Twilio phone number. Exiting.")
    exit(1)
print(f"Sending from: {from_number}")

# Connect to DB
conn = psycopg2.connect(**DB)
cur = conn.cursor()

# Get queued SMS messages with phone numbers
cur.execute("""
    SELECT 
        ol.id,
        ol.lead_id,
        ol.lead_type,
        ol.message_body,
        CASE 
            WHEN ol.lead_type = 'contractor' THEN cl.phone
            WHEN ol.lead_type = 'customer' THEN cu.phone
        END as phone,
        CASE 
            WHEN ol.lead_type = 'contractor' THEN cl.company_name
            WHEN ol.lead_type = 'customer' THEN cu.customer_name
        END as name
    FROM outreach_logs ol
    LEFT JOIN contractor_leads cl ON ol.lead_type = 'contractor' AND ol.lead_id = cl.id
    LEFT JOIN customer_leads cu ON ol.lead_type = 'customer' AND ol.lead_id = cu.id
    WHERE ol.delivery_status = 'queued'
    AND ol.channel IN ('sms', 'manual')
    LIMIT 50
""")

messages = cur.fetchall()
print(f"Found {len(messages)} queued SMS messages")

if not messages:
    print("No SMS messages queued. Done.")
    cur.close()
    conn.close()
    exit(0)

sent = 0
failed = 0

for msg_id, lead_id, lead_type, message_body, phone, name in messages:
    if not phone:
        print(f"  SKIP {name or lead_id} — no phone number")
        cur.execute("UPDATE outreach_logs SET delivery_status='failed' WHERE id=%s", (msg_id,))
        failed += 1
        continue

    formatted_phone = format_phone(phone)
    print(f"  Sending to {name or 'Unknown'} ({formatted_phone})...")

    msg_sid, error = send_sms(formatted_phone, message_body, from_number)

    if msg_sid:
        cur.execute("""
            UPDATE outreach_logs 
            SET delivery_status='sent', sent_at=NOW()
            WHERE id=%s
        """, (msg_id,))
        # Update lead contact status
        table = 'contractor_leads' if lead_type == 'contractor' else 'customer_leads'
        cur.execute(f"""
            UPDATE {table} 
            SET contact_status='contacted', last_contacted_at=NOW()
            WHERE id=%s
        """, (lead_id,))
        print(f"  ✓ Sent — SID: {msg_sid}")
        sent += 1
    else:
        cur.execute("""
            UPDATE outreach_logs 
            SET delivery_status='failed'
            WHERE id=%s
        """, (msg_id,))
        print(f"  ✗ Failed — {error}")
        failed += 1

    conn.commit()

cur.close()
conn.close()

print(f"\n=== DONE — Sent: {sent} | Failed: {failed} ===")
