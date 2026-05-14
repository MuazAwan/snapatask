require('dotenv').config({ path: '/opt/snapatask/.env' });
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT) || 5432,
  database: process.env.POSTGRES_DB,
  user: process.env.POSTGRES_USER,
  password: process.env.POSTGRES_PASSWORD,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

pool.on('error', (err) => {
  console.error('Unexpected DB pool error:', err);
});

async function query(text, params) {
  const start = Date.now();
  try {
    const result = await pool.query(text, params);
    const duration = Date.now() - start;
    if (duration > 1000) {
      console.warn(`Slow query (${duration}ms): ${text.substring(0, 100)}`);
    }
    return result;
  } catch (err) {
    console.error('DB query error:', { text: text.substring(0, 100), error: err.message });
    throw err;
  }
}

async function testConnection() {
  try {
    const result = await query('SELECT NOW() as time');
    console.log('DB connected at:', result.rows[0].time);
    return true;
  } catch (err) {
    console.error('DB connection failed:', err.message);
    return false;
  }
}

module.exports = { query, pool, testConnection };
