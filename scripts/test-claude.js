require('dotenv').config({ path: '/opt/snapatask/.env' });
const { askHaiku } = require('/opt/snapatask/shared/claude');

askHaiku('You are a helpful assistant.', 'Reply with the single word OK and nothing else.')
  .then(response => {
    console.log('Claude response:', response);
    if (response.trim().includes('OK')) {
      console.log('SUCCESS — Claude API working');
      process.exit(0);
    } else {
      console.log('UNEXPECTED response — check API key');
      process.exit(1);
    }
  })
  .catch(err => {
    console.error('FAILED — Claude API error:', err.message);
    process.exit(1);
  });
