CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name VARCHAR(255) NOT NULL,
  source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('gumtree', 'facebook_marketplace', 'facebook_group', 'directory', 'other')),
  source_url TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused')),
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customer_leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_platform VARCHAR(100) NOT NULL,
  source_url TEXT NOT NULL,
  customer_name VARCHAR(255),
  phone VARCHAR(50),
  email VARCHAR(255),
  location VARCHAR(255),
  postcode VARCHAR(20),
  post_title TEXT,
  post_description TEXT,
  job_type VARCHAR(100),
  urgency VARCHAR(50),
  date_posted TIMESTAMP,
  date_found TIMESTAMP NOT NULL DEFAULT NOW(),
  lead_score INTEGER CHECK (lead_score >= 1 AND lead_score <= 10),
  contact_status VARCHAR(50) NOT NULL DEFAULT 'new' CHECK (contact_status IN ('new', 'contacted', 'interested', 'not_interested', 'job_posted', 'do_not_contact', 'invalid')),
  message_sent TEXT,
  message_channel VARCHAR(50),
  last_contacted_at TIMESTAMP,
  reply_status VARCHAR(50) DEFAULT 'no_reply' CHECK (reply_status IN ('no_reply', 'replied', 'interested', 'not_interested', 'do_not_contact')),
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contractor_leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_platform VARCHAR(100) NOT NULL,
  source_url TEXT NOT NULL,
  company_name VARCHAR(255),
  contact_name VARCHAR(255),
  phone VARCHAR(50),
  email VARCHAR(255),
  website VARCHAR(500),
  profile_url TEXT,
  location VARCHAR(255),
  area_covered TEXT,
  services_offered TEXT,
  licence_mentioned BOOLEAN DEFAULT FALSE,
  date_found TIMESTAMP NOT NULL DEFAULT NOW(),
  lead_score INTEGER CHECK (lead_score >= 1 AND lead_score <= 10),
  contact_status VARCHAR(50) NOT NULL DEFAULT 'new' CHECK (contact_status IN ('new', 'contacted', 'interested', 'not_interested', 'registered', 'do_not_contact', 'invalid')),
  message_sent TEXT,
  message_channel VARCHAR(50),
  last_contacted_at TIMESTAMP,
  reply_status VARCHAR(50) DEFAULT 'no_reply' CHECK (reply_status IN ('no_reply', 'replied', 'interested', 'not_interested', 'do_not_contact')),
  registration_status VARCHAR(50) DEFAULT 'not_registered' CHECK (registration_status IN ('not_registered', 'invited', 'registered', 'active')),
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS outreach_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_type VARCHAR(20) NOT NULL CHECK (lead_type IN ('customer', 'contractor')),
  lead_id UUID NOT NULL,
  channel VARCHAR(50) NOT NULL CHECK (channel IN ('email', 'sms', 'platform_message', 'manual')),
  message_template VARCHAR(100),
  message_body TEXT NOT NULL,
  sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
  delivery_status VARCHAR(50) DEFAULT 'sent' CHECK (delivery_status IN ('queued', 'sent', 'delivered', 'failed', 'bounced')),
  reply_received BOOLEAN DEFAULT FALSE,
  reply_text TEXT,
  next_follow_up_date DATE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS do_not_contact (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone VARCHAR(50),
  email VARCHAR(255),
  name VARCHAR(255),
  reason TEXT NOT NULL,
  date_added TIMESTAMP NOT NULL DEFAULT NOW(),
  source VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_customer_leads_phone ON customer_leads(phone);
CREATE INDEX IF NOT EXISTS idx_customer_leads_email ON customer_leads(email);
CREATE INDEX IF NOT EXISTS idx_customer_leads_source_url ON customer_leads(source_url);
CREATE INDEX IF NOT EXISTS idx_customer_leads_contact_status ON customer_leads(contact_status);
CREATE INDEX IF NOT EXISTS idx_customer_leads_lead_score ON customer_leads(lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_contractor_leads_phone ON contractor_leads(phone);
CREATE INDEX IF NOT EXISTS idx_contractor_leads_email ON contractor_leads(email);
CREATE INDEX IF NOT EXISTS idx_contractor_leads_source_url ON contractor_leads(source_url);
CREATE INDEX IF NOT EXISTS idx_outreach_logs_lead_id ON outreach_logs(lead_id);
CREATE INDEX IF NOT EXISTS idx_dnc_phone ON do_not_contact(phone);
CREATE INDEX IF NOT EXISTS idx_dnc_email ON do_not_contact(email);

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER customer_leads_updated_at
  BEFORE UPDATE ON customer_leads
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER contractor_leads_updated_at
  BEFORE UPDATE ON contractor_leads
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

INSERT INTO sources (source_name, source_type, source_url, status, notes) VALUES
  ('Gumtree Rubbish Removal UK', 'gumtree', 'https://www.gumtree.com/search?search_category=services&q=rubbish+removal', 'active', 'National rubbish removal services'),
  ('Gumtree House Clearance UK', 'gumtree', 'https://www.gumtree.com/search?search_category=services&q=house+clearance', 'active', 'House clearance services'),
  ('Gumtree Waste Clearance UK', 'gumtree', 'https://www.gumtree.com/search?search_category=services&q=waste+clearance', 'active', 'Waste clearance services'),
  ('Gumtree Junk Removal UK', 'gumtree', 'https://www.gumtree.com/search?search_category=services&q=junk+removal', 'active', 'Junk removal services'),
  ('Gumtree Garden Waste UK', 'gumtree', 'https://www.gumtree.com/search?search_category=services&q=g
