require('dotenv').config({ path: '/opt/snapatask/.env' });
const { testConnection } = require('/opt/snapatask/shared/db');

testConnection().then(ok => {
  if (ok) {
    console.log('SUCCESS — database connection working');
    process.exit(0);
  } else {
    console.log('FAILED — database connection failed');
    process.exit(1);
  }
});
