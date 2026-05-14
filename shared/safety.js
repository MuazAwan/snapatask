require('dotenv').config({ path: '/opt/snapatask/.env' });
const { query } = require('./db');

const OPT_OUT_KEYWORDS = [
  'stop', 'unsubscribe', 'remove me', 'remove my', 'not interested',
  'don\'t contact', 'do not contact', 'leave me alone', 'no thanks',
  'no thank you', 'please stop', 'opt out', 'opt-out'
];

async function isOnDNC(phone, email) {
  try {
    const conditions = [];
    const params = [];
    let idx = 1;

    if (phone) {
      conditions.push(`phone = $${idx++}`);
      params.push(phone.replace(/\s/g, ''));
    }
    if (email) {
      conditions.push(`LOWER(email) = LOWER($${idx++})`);
      params.push(email);
    }

    if (conditions.length === 0) return false;

    const result = await query(
      `SELECT id FROM do_not_contact WHERE ${conditions.join(' OR ')} LIMIT 1`,
      params
    );
    return result.rows.length > 0;
  } catch (err) {
    console.error('DNC check failed — blocking contact as safety measure:', err.message);
    return true;
  }
}

async function addToDNC(phone, email, name, reason, source = 'system') {
  await query(
    `INSERT INTO do_not_contact (phone, email, name, reason, source)
     VALUES ($1, $2, $3, $4, $5)`,
    [phone || null, email || null, name || null, reason, source]
  );
  console.log(`Added to DNC: ${email || phone} — reason: ${reason}`);
}

function containsOptOut(text) {
  if (!text) return false;
  const lower = text.toLowerCase();
  return OPT_OUT_KEYWORDS.some(kw => lower.includes(kw));
}

async function isDailyLimitReached() {
  const maxPerDay = parseInt(process.env.MAX_MESSAGES_PER_DAY) || 50;
  const result = await query(
    `SELECT COUNT(*) as count FROM outreach_logs
     WHERE sent_at >= NOW() - INTERVAL '24 hours'
     AND delivery_status != 'failed'`
  );
  const count = parseInt(result.rows[0].count);
  if (count >= maxPerDay) {
    console.warn(`Daily send limit reached: ${count}/${maxPerDay}`);
    return true;
  }
  return false;
}

function isManualReviewMode() {
  return process.env.MANUAL_REVIEW_MODE === 'true';
}

async function enforceDelay() {
  const minDelay = parseInt(process.env.MIN_DELAY_BETWEEN_MESSAGES_MS) || 60000;
  await new Promise(resolve => setTimeout(resolve, minDelay));
}

module.exports = {
  isOnDNC,
  addToDNC,
  containsOptOut,
  isDailyLimitReached,
  isManualReviewMode,
  enforceDelay,
  OPT_OUT_KEYWORDS
};
