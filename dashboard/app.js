const express = require('express');
const { Pool } = require('pg');
const path = require('path');

const app = express();
const PORT = 3200;

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'postgres',
  port: 5432,
  database: 'snapatask',
  user: 'snapatask_user',
  password: 'Sn4p4T4sk_DB_S3cur3_2026!xPq9'
});

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', async (req, res) => {
  try {
    const stats = await pool.query(`SELECT
      (SELECT COUNT(*) FROM contractor_leads) as contractors,
      (SELECT COUNT(*) FROM customer_leads) as customers,
      (SELECT COUNT(*) FROM outreach_logs WHERE delivery_status='queued') as queued,
      (SELECT COUNT(*) FROM outreach_logs WHERE delivery_status='sent') as sent,
      (SELECT COUNT(*) FROM contractor_leads WHERE lead_score >= 7) as high_quality,
      (SELECT COUNT(*) FROM contractor_leads WHERE reply_status='replied') as replied,
      (SELECT COUNT(*) FROM contractor_leads WHERE contact_status='new') as new_contractors,
      (SELECT COUNT(*) FROM customer_leads WHERE contact_status='new') as new_customers,
      (SELECT COUNT(*) FROM sources WHERE status='active') as active_sources,
      (SELECT ROUND(AVG(lead_score),1) FROM contractor_leads) as avg_score`);
    const recent_contractors = await pool.query(`SELECT company_name, location, lead_score, contact_status, created_at FROM contractor_leads ORDER BY created_at DESC LIMIT 5`);
    const recent_customers = await pool.query(`SELECT post_title, location, urgency, contact_status, created_at FROM customer_leads ORDER BY created_at DESC LIMIT 5`);
    const score_dist = await pool.query(`SELECT lead_score, COUNT(*) as count FROM contractor_leads GROUP BY lead_score ORDER BY lead_score DESC`);
    res.render('home', { stats: stats.rows[0], recent_contractors: recent_contractors.rows, recent_customers: recent_customers.rows, score_dist: score_dist.rows, page: 'home' });
  } catch (e) { res.status(500).send('DB Error: ' + e.message); }
});

app.get('/contractors', async (req, res) => {
  try {
    const { status, min_score, location, reply, sort, search } = req.query;
    let where = ['1=1']; let params = []; let i = 1;
    if (status)    { where.push(`contact_status=$${i++}`); params.push(status); }
    if (min_score) { where.push(`lead_score>=$${i++}`); params.push(parseInt(min_score)); }
    if (location)  { where.push(`location ILIKE $${i++}`); params.push(`%${location}%`); }
    if (reply)     { where.push(`reply_status=$${i++}`); params.push(reply); }
    if (search)    { where.push(`(company_name ILIKE $${i++} OR services_offered ILIKE $${i-1})`); params.push(`%${search}%`); }
    const order = sort === 'date' ? 'created_at DESC' : sort === 'name' ? 'company_name ASC' : 'lead_score DESC, created_at DESC';
    const result = await pool.query(`SELECT id, company_name, location, phone, email, lead_score, contact_status, reply_status, registration_status, licence_mentioned, source_platform, source_url, LEFT(services_offered, 120) as services_short, created_at FROM contractor_leads WHERE ${where.join(' AND ')} ORDER BY ${order} LIMIT 100`, params);
    res.render('contractors', { leads: result.rows, filters: req.query, count: result.rows.length, page: 'contractors' });
  } catch (e) { res.status(500).send('DB Error: ' + e.message); }
});

app.post('/contractors/:id/update', async (req, res) => {
  try {
    const { reply_status, contact_status, registration_status } = req.body;
    await pool.query(`UPDATE contractor_leads SET reply_status=$1, contact_status=$2, registration_status=$3, updated_at=NOW() WHERE id=$4`, [reply_status, contact_status, registration_status, req.params.id]);
    res.json({ success: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});


app.get('/contractors/:id', async (req, res) => {
  try {
    const result = await pool.query(`SELECT * FROM contractor_leads WHERE id=$1`, [req.params.id]);
    if (result.rows.length === 0) return res.status(404).send('Lead not found');
    const outreach = await pool.query(`SELECT * FROM outreach_logs WHERE lead_id=$1 AND lead_type='contractor' ORDER BY created_at DESC`, [req.params.id]);
    res.render('contractor-detail', { lead: result.rows[0], outreach: outreach.rows, page: 'contractors' });
  } catch (e) { res.status(500).send('DB Error: ' + e.message); }
});

app.get('/customers', async (req, res) => {
  try {
    const { status, urgency, location, sort, search } = req.query;
    let where = ['1=1']; let params = []; let i = 1;
    if (status)  { where.push(`contact_status=$${i++}`); params.push(status); }
    if (urgency) { where.push(`urgency=$${i++}`); params.push(urgency); }
    if (location){ where.push(`location ILIKE $${i++}`); params.push(`%${location}%`); }
    if (search)  { where.push(`(post_title ILIKE $${i++} OR post_description ILIKE $${i-1})`); params.push(`%${search}%`); }
    const order = sort === 'score' ? 'lead_score DESC NULLS LAST' : 'created_at DESC';
    const result = await pool.query(`SELECT id, post_title, location, postcode, phone, email, urgency, lead_score, contact_status, reply_status, source_platform, source_url, job_type, LEFT(post_description, 150) as desc_short, created_at FROM customer_leads WHERE ${where.join(' AND ')} ORDER BY ${order} LIMIT 100`, params);
    res.render('customers', { leads: result.rows, filters: req.query, count: result.rows.length, page: 'customers' });
  } catch (e) { res.status(500).send('DB Error: ' + e.message); }
});

app.get('/outreach', async (req, res) => {
  try {
    const { status, lead_type } = req.query;
    let where = ['1=1']; let params = []; let i = 1;
    if (status)    { where.push(`o.delivery_status=$${i++}`); params.push(status); }
    if (lead_type) { where.push(`o.lead_type=$${i++}`); params.push(lead_type); }
    const result = await pool.query(`SELECT o.id, o.lead_id, o.lead_type, o.channel, o.delivery_status, o.message_body, o.message_template, o.sent_at, o.reply_received, o.created_at, COALESCE(c.company_name, cu.post_title) as lead_name, COALESCE(c.location, cu.location) as lead_location, COALESCE(c.phone, cu.phone) as lead_phone, COALESCE(c.lead_score::text, cu.lead_score::text) as lead_score, COALESCE(c.source_url, cu.source_url) as lead_url FROM outreach_logs o LEFT JOIN contractor_leads c ON o.lead_type='contractor' AND o.lead_id=c.id LEFT JOIN customer_leads cu ON o.lead_type='customer' AND o.lead_id=cu.id WHERE ${where.join(' AND ')} ORDER BY o.created_at DESC LIMIT 100`, params);
    const counts = await pool.query(`SELECT delivery_status, COUNT(*) as count FROM outreach_logs GROUP BY delivery_status`);
    res.render('outreach', { logs: result.rows, counts: counts.rows, filters: req.query, count: result.rows.length, page: 'outreach' });
  } catch (e) { res.status(500).send('DB Error: ' + e.message); }
});

app.post('/outreach/:id/sent', async (req, res) => {
  try {
    // Get message and phone number
    const msgResult = await pool.query(`
      SELECT ol.message_body, ol.lead_type, ol.lead_id,
        COALESCE(cl.phone, cu.phone) as phone,
        COALESCE(cl.company_name, cu.customer_name) as name
      FROM outreach_logs ol
      LEFT JOIN contractor_leads cl ON ol.lead_type='contractor' AND ol.lead_id=cl.id
      LEFT JOIN customer_leads cu ON ol.lead_type='customer' AND ol.lead_id=cu.id
      WHERE ol.id=$1
    `, [req.params.id]);

    const msg = msgResult.rows[0];

    if (msg && msg.phone) {
      // Format UK phone to E.164
      let phone = msg.phone.replace(/\s+/g, '').replace(/[^0-9+]/g, '');
      if (phone.startsWith('0')) phone = '+44' + phone.slice(1);
      if (!phone.startsWith('+')) phone = '+44' + phone;

      // Send via Twilio
      const accountSid = process.env.TWILIO_ACCOUNT_SID;
      const authToken = process.env.TWILIO_AUTH_TOKEN;
      const fromNumber = process.env.TWILIO_FROM_NUMBER;

      const twilio = require('node:https');
      const params = new URLSearchParams({
        To: phone,
        From: fromNumber,
        Body: msg.message_body
      });

      const options = {
        hostname: 'api.twilio.com',
        path: `/2010-04-01/Accounts/${accountSid}/Messages.json`,
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': 'Basic ' + Buffer.from(`${accountSid}:${authToken}`).toString('base64')
        }
      };

      await new Promise((resolve, reject) => {
        const request = twilio.request(options, (response) => {
          let data = '';
          response.on('data', chunk => data += chunk);
          response.on('end', () => {
            const result = JSON.parse(data);
            if (result.sid) {
              console.log(`SMS sent to ${msg.name} (${phone}) - SID: ${result.sid}`);
              resolve(result);
            } else {
              console.error(`SMS failed: ${JSON.stringify(result)}`);
              reject(new Error(result.message || 'SMS failed'));
            }
          });
        });
        request.on('error', reject);
        request.write(params.toString());
        request.end();
      });

      // Update lead contact status
      const table = msg.lead_type === 'contractor' ? 'contractor_leads' : 'customer_leads';
      await pool.query(`UPDATE ${table} SET contact_status='contacted', last_contacted_at=NOW() WHERE id=$1`, [msg.lead_id]);
    }

    // Mark as sent
    await pool.query(`UPDATE outreach_logs SET delivery_status='sent', sent_at=NOW() WHERE id=$1`, [req.params.id]);
    res.json({ success: true });
  } catch (e) {
    console.error('Send error:', e.message);
    // Mark as failed if SMS failed
    await pool.query(`UPDATE outreach_logs SET delivery_status='failed' WHERE id=$1`, [req.params.id]);
    res.status(500).json({ error: e.message });
  }
});

app.post('/outreach/:id/failed', async (req, res) => {
  try {
    await pool.query(`UPDATE outreach_logs SET delivery_status='failed' WHERE id=$1`, [req.params.id]);
    res.json({ success: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.get('/report', async (req, res) => {
  try {
    const [summary, by_score, by_location, by_status, by_platform, by_reply] = await Promise.all([
      pool.query(`SELECT (SELECT COUNT(*) FROM contractor_leads) as total_contractors, (SELECT COUNT(*) FROM customer_leads) as total_customers, (SELECT COUNT(*) FROM outreach_logs WHERE delivery_status='queued') as queued, (SELECT COUNT(*) FROM outreach_logs WHERE delivery_status='sent') as sent, (SELECT COUNT(*) FROM outreach_logs WHERE delivery_status='failed') as failed, (SELECT COUNT(*) FROM contractor_leads WHERE reply_status='replied') as replied, (SELECT COUNT(*) FROM contractor_leads WHERE reply_status='interested') as interested, (SELECT COUNT(*) FROM contractor_leads WHERE registration_status='registered') as registered, (SELECT ROUND(AVG(lead_score),1) FROM contractor_leads) as avg_score, (SELECT COUNT(*) FROM contractor_leads WHERE licence_mentioned=true) as licensed`),
      pool.query(`SELECT lead_score, COUNT(*) as count FROM contractor_leads GROUP BY lead_score ORDER BY lead_score DESC`),
      pool.query(`SELECT location, COUNT(*) as count FROM contractor_leads GROUP BY location ORDER BY count DESC LIMIT 10`),
      pool.query(`SELECT contact_status, COUNT(*) as count FROM contractor_leads GROUP BY contact_status ORDER BY count DESC`),
      pool.query(`SELECT source_platform, COUNT(*) as count FROM contractor_leads GROUP BY source_platform`),
      pool.query(`SELECT reply_status, COUNT(*) as count FROM contractor_leads GROUP BY reply_status`)
    ]);
    res.render('report', { summary: summary.rows[0], by_score: by_score.rows, by_location: by_location.rows, by_status: by_status.rows, by_platform: by_platform.rows, by_reply: by_reply.rows, generated_at: new Date().toISOString(), page: 'report' });
  } catch (e) { res.status(500).send('DB Error: ' + e.message); }
});

app.get('/dnc', async (req, res) => {
  try {
    const result = await pool.query(`SELECT * FROM do_not_contact ORDER BY date_added DESC LIMIT 100`);
    res.render('dnc', { entries: result.rows, page: 'dnc' });
  } catch (e) { res.status(500).send('DB Error: ' + e.message); }
});

app.post('/dnc/add', async (req, res) => {
  try {
    const { phone, email, name, reason } = req.body;
    await pool.query(`INSERT INTO do_not_contact (phone, email, name, reason, date_added, source) VALUES ($1,$2,$3,$4,NOW(),'manual')`, [phone||null, email||null, name||null, reason||'Manual add']);
    res.redirect('/dnc');
  } catch (e) { res.status(500).send('DB Error: ' + e.message); }
});

app.get('/api/stats', async (req, res) => {
  try {
    const result = await pool.query(`SELECT (SELECT COUNT(*) FROM contractor_leads) as contractors, (SELECT COUNT(*) FROM customer_leads) as customers, (SELECT COUNT(*) FROM outreach_logs WHERE delivery_status='queued') as queued, (SELECT COUNT(*) FROM outreach_logs WHERE delivery_status='sent') as sent`);
    res.json(result.rows[0]);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log('Snapatask Dashboard running on port ' + PORT);
});
