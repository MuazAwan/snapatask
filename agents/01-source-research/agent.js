require('dotenv').config({ path: '/opt/snapatask/.env' });
const { query } = require('/opt/snapatask/shared/db');
const { createLogger } = require('/opt/snapatask/shared/logger');

const log = createLogger('SourceResearchAgent');

const KNOWN_SOURCES = [
  { name: 'Gumtree Rubbish Removal UK', type: 'gumtree', url: 'https://www.gumtree.com/search?search_category=services&q=rubbish+removal', notes: 'National rubbish removal services' },
  { name: 'Gumtree House Clearance UK', type: 'gumtree', url: 'https://www.gumtree.com/search?search_category=services&q=house+clearance', notes: 'House clearance services' },
  { name: 'Gumtree Waste Clearance UK', type: 'gumtree', url: 'https://www.gumtree.com/search?search_category=services&q=waste+clearance', notes: 'Waste clearance services' },
  { name: 'Gumtree Junk Removal UK', type: 'gumtree', url: 'https://www.gumtree.com/search?search_category=services&q=junk+removal', notes: 'Junk removal services' },
  { name: 'Gumtree Garden Waste UK', type: 'gumtree', url: 'https://www.gumtree.com/search?search_category=services&q=garden+waste+removal', notes: 'Garden waste removal' },
  { name: 'Gumtree Office Clearance UK', type: 'gumtree', url: 'https://www.gumtree.com/search?search_category=services&q=office+clearance', notes: 'Office clearance' },
  { name: 'Gumtree Man and Van UK', type: 'gumtree', url: 'https://www.gumtree.com/search?search_category=services&q=man+with+van+rubbish', notes: 'Man and van for rubbish' },
  { name: 'Gumtree Garage Clearance UK', type: 'gumtree', url: 'https://www.gumtree.com/search?search_category=services&q=garage+clearance', notes: 'Garage clearance' },
  { name: 'Gumtree Furniture Removal UK', type: 'gumtree', url: 'https://www.gumtree.com/search?search_category=services&q=furniture+removal', notes: 'Furniture removal' },
  { name: 'Gumtree Builders Waste UK', type: 'gumtree', url: 'https://www.gumtree.com/search?search_category=services&q=builders+waste', notes: 'Builders waste collection' },
  { name: 'Facebook Marketplace Home Services', type: 'facebook_marketplace', url: 'https://www.facebook.com/marketplace/category/home-services', notes: 'FB Marketplace home services' },
  { name: 'Gumtree Rubbish Removal Wanted', type: 'gumtree', url: 'https://www.gumtree.com/search?search_category=for-sale&q=rubbish+removal+needed', notes: 'Customer wanted posts' },
];

async function run() {
  log.info('Starting source research agent');

  let added = 0;
  let skipped = 0;

  for (const source of KNOWN_SOURCES) {
    try {
      const existing = await query(
        'SELECT id FROM sources WHERE source_url = $1',
        [source.url]
      );

      if (existing.rows.length > 0) {
        log.debug(`Source already exists: ${source.name}`);
        skipped++;
        continue;
      }

      await query(
        `INSERT INTO sources (source_name, source_type, source_url, status, notes)
         VALUES ($1, $2, $3, 'active', $4)`,
        [source.name, source.type, source.url, source.notes]
      );

      log.info(`Added source: ${source.name}`);
      added++;
    } catch (err) {
      log.error(`Failed to add source ${source.name}:`, { error: err.message });
    }
  }

  const total = await query("SELECT COUNT(*) FROM sources WHERE status = 'active'");
  log.info('Source research complete', {
    added,
    skipped,
    totalActive: total.rows[0].count
  });

  process.exit(0);
}

run().catch(err => {
  log.error('Agent crashed:', { error: err.message });
  process.exit(1);
});
