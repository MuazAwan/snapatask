import requests, json, psycopg2

DB = {"host":"localhost","port":5432,"dbname":"snapatask",
      "user":"snapatask_user","password":"Sn4p4T4sk_DB_S3cur3_2026!xPq9"}

print("Fetching Environment Agency London waste carriers...")
url = "https://environment.data.gov.uk/public-register/waste-carriers-brokers/registration.json"
params = {"name-search":"","number-search":"","address-search":"London","__postcode":""}
r = requests.get(url, params=params, headers={"User-Agent":"Mozilla/5.0"}, timeout=60)
data = r.json()
items = data['items']
print(f"Total records: {len(items)}")

conn = psycopg2.connect(**DB)
cur = conn.cursor()
saved = skipped = errors = 0

for item in items:
    try:
        reg_num   = item.get('registrationNumber','')
        source_url = item.get('@id','')
        if not reg_num: continue

        # Company name
        company = ''
        holder = item.get('holder',{})
        if isinstance(holder, dict):
            company = holder.get('name','')
        if not company:
            site = item.get('site',{})
            if isinstance(site, dict):
                addr = site.get('siteAddress',{})
                company = addr.get('organization_name','') if isinstance(addr,dict) else ''

        # Address fields
        site = item.get('site',{})
        site_addr = {}
        if isinstance(site, dict):
            site_addr = site.get('siteAddress',{}) or {}
        address   = site_addr.get('address','') if isinstance(site_addr,dict) else ''
        locality  = site_addr.get('locality','London') if isinstance(site_addr,dict) else 'London'
        postcode  = site_addr.get('postcode','') if isinstance(site_addr,dict) else ''

        # Registration details
        tier      = item.get('tier',{}).get('label','') if isinstance(item.get('tier'),dict) else ''
        reg_type  = item.get('registrationType',{}).get('label','') if isinstance(item.get('registrationType'),dict) else ''
        app_type  = item.get('applicantType',{}).get('prefLabel','') if isinstance(item.get('applicantType'),dict) else ''
        reg_date  = item.get('registrationDate','')
        exp_date  = item.get('expiryDate','')
        upper     = 'upper' in tier.lower()

        services = f"{reg_type} - {tier} Tier. Reg: {reg_num}. Expires: {exp_date}. Type: {app_type}"
        notes    = f"EA Register. Postcode: {postcode}. Reg date: {reg_date}"

        cur.execute("""
            INSERT INTO contractor_leads
            (source_platform, source_url, company_name, location,
             services_offered, licence_mentioned, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT ON CONSTRAINT uq_contractor_leads_source_url DO NOTHING
        """, (
            'environment_agency',
            source_url,
            (company or f'Carrier {reg_num}')[:255],
            (locality or 'London')[:255],
            services[:1000],
            True,
            notes[:500]
        ))
        if cur.rowcount > 0: saved += 1
        else: skipped += 1

        if saved % 100 == 0 and saved > 0:
            conn.commit()
            print(f"  Progress: {saved} saved...")

    except Exception as e:
        errors += 1
        conn.rollback()

conn.commit()
cur.close()
conn.close()

print(f"\n{'='*50}")
print(f"✓ Saved: {saved} | Skipped: {skipped} | Errors: {errors}")

# Final DB count
conn = psycopg2.connect(**DB)
cur = conn.cursor()
cur.execute("""
    SELECT source_platform, COUNT(*) as cnt
    FROM contractor_leads
    GROUP BY source_platform ORDER BY cnt DESC
""")
print(f"\nContractor leads by source:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")
cur.execute("SELECT COUNT(*) FROM contractor_leads")
print(f"\nTotal contractor leads: {cur.fetchone()[0]}")
cur.close()
conn.close()
print("=== DONE ===")
