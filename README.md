# Snapatask — AI-Powered Lead Generation & Outreach Platform

> A fully automated multi-agent AI system for finding, scoring, and managing contractor leads in the UK waste removal marketplace.

---

## Overview

Snapatask is a production-grade AI automation platform built on top of **Paperclip** and **Hermes (Claude Sonnet)** that autonomously scrapes contractor leads from multiple UK platforms, scores them by quality, deduplicates the database, and prepares personalised outreach — all running on a self-hosted VPS with zero manual intervention.

The system currently manages **2,300+ verified contractor leads** with daily automated collection from 4 data sources.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        PAPERCLIP                            │
│              Agent Orchestration Layer                      │
│                                                             │
│  ┌──────────┐   delegates   ┌──────────────────────────┐   │
│  │   CEO    │ ────────────► │   Specialist Agents      │   │
│  │  Agent   │               │  • Contractor Finder     │   │
│  └──────────┘               │  • Customer Lead Finder  │   │
│                             │  • Lead Scorer           │   │
│                             │  • Deduplication Agent   │   │
│                             │  • Outreach Agent        │   │
│                             │  • Reply Monitor         │   │
│                             │  • Data Extractor        │   │
│                             │  • Reporting Agent       │   │
│                             └──────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Hermes Agent v0.12  │
                    │   (Claude Sonnet)     │
                    └───────────┬───────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │          PostgreSQL DB             │
              │  contractor_leads | customer_leads │
              │  outreach_logs   | sources        │
              └───────────────────────────────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │        Python Scrapers             │
              │  Checkatrade | Env Agency          │
              │  Gumtree     | Yell.com            │
              └───────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | Paperclip AI |
| AI Execution | Hermes Agent v0.12 (Claude Sonnet 4.6) |
| Database | PostgreSQL 15 |
| CRM Dashboard | Node.js + Express + EJS |
| Scrapers | Python 3.12 + BeautifulSoup + Requests |
| Infrastructure | Docker Compose on Ubuntu 24.04 VPS |
| Reverse Proxy | Traefik |
| Agent Monitoring | OpenClaw v2026.5.7 |

---

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Dashboard (CRM) | 3200 | Lead management UI |
| Paperclip | 3100 | Agent orchestration UI |
| PostgreSQL | 5432 | Main database |
| OpenClaw | 18789 | Agent monitoring |
| Traefik | 80/443 | Reverse proxy |

---

## AI Agents

| Agent | Role |
|-------|------|
| **CEO** | Orchestrates all agents, interprets tasks, delegates work |
| Contractor Finder | Discovers new contractor leads from web sources |
| Customer Lead Finder | Finds businesses needing waste removal services |
| Lead Scorer | Scores leads 1–10 based on quality signals |
| Deduplication Agent | Identifies and removes duplicate leads |
| Outreach Agent | Prepares personalised outreach messages |
| Reply Monitor | Classifies and tracks lead responses |
| Data Extractor | Generates structured reports from raw data |
| Reporting Agent | Produces daily/weekly business intelligence reports |

---

## Lead Scoring Criteria

| Signal | Points |
|--------|--------|
| Verified / Licensed status | 40 |
| Reviews & ratings | 20 |
| Service breadth | 10 |
| Named business | 5 |
| Pricing clarity | 5 |
| Same-day availability | 5 |
| Card payments accepted | 3 |

---

## Data Sources

| Source | Leads | Avg Score | Notes |
|--------|-------|-----------|-------|
| Environment Agency | 2,034 | 9.1/10 | Licensed carriers, high quality |
| Checkatrade | 132 | 10.0/10 | Verified, reviewed, phones |
| Gumtree | 30 | 5.6/10 | Mixed quality |
| Yell.com | 13 | 5.0/10 | Directory listings |

---

## Automated Schedule

```
06:00 AM daily
├── env-agency-scraper.py     → Environment Agency licensed carriers
├── checkatrade-scraper.py    → Verified contractor profiles
├── lead-scraper.py           → Gumtree listings
└── yell-scraper.py           → Yell.com directory
         │
         ▼
    PostgreSQL DB
         │
         ▼
    Agents score, deduplicate, and report on new leads
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Anthropic API key
- Ubuntu 20.04+ VPS

### Setup

```bash
# Clone the repo
git clone https://github.com/MuazAwan/snapatask.git
cd snapatask

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker compose up -d

# Run initial database setup
docker exec postgres psql -U snapatask_user -d snapatask -f /docker-entrypoint-initdb.d/init.sql

# Onboard Paperclip
docker exec -it paperclip pnpm paperclipai onboard

# Run scrapers manually (first time)
bash run-daily-scrapers.sh
```

### Access

| URL | Service |
|-----|---------|
| `http://YOUR_IP:3200` | CRM Dashboard |
| `http://YOUR_IP:3100` | Paperclip Agent Manager (Chrome only) |

---

## Environment Variables

```bash
# Copy the example file
cp .env.example .env
```

Required variables:

```env
ANTHROPIC_API_KEY=           # Claude API key
PAPERCLIP_DB_PASSWORD=       # Paperclip PostgreSQL password
SNAPATASK_DB_PASSWORD=       # Snapatask PostgreSQL password
BETTER_AUTH_SECRET=          # Paperclip auth secret
PAPERCLIP_PUBLIC_URL=        # Your server URL e.g. http://YOUR_IP:3100
```

---

## Using the Agents

Once Paperclip is running, assign tasks to the CEO agent in plain English:

```
"Give me a full status report of all leads"
"Score the top 20 unscored contractor leads"
"Find any duplicate contractor leads and report them"
"Prepare outreach messages for the top 10 Checkatrade leads"
"Generate a weekly business intelligence report"
```

The CEO delegates automatically to the right specialist agent.

---

## Project Structure

```
snapatask/
├── dashboard/              # CRM frontend (Node.js + EJS)
│   ├── app.js
│   └── views/
├── database/
│   └── init.sql            # Database schema
├── agents/                 # Agent configurations
├── scripts/                # Utility scripts
├── shared/                 # Shared modules (DB, Claude, logger)
├── checkatrade-scraper.py  # Checkatrade scraper
├── env-agency-scraper.py   # Environment Agency scraper
├── lead-scraper.py         # Gumtree scraper
├── yell-scraper.py         # Yell.com scraper
├── run-daily-scrapers.sh   # Cron entry point
├── restore-hermes.sh       # Hermes recovery script
└── docker-compose.yml      # Full stack definition
```

---

## Recovery

If Hermes stops working after a container restart:

```bash
bash /opt/snapatask/restore-hermes.sh
```

Or manually:

```bash
docker cp /usr/local/bin/hermes-paperclip paperclip:/usr/bin/hermes
docker exec paperclip chmod +x /usr/bin/hermes
docker exec paperclip /usr/bin/hermes --version
```

---

## Database Schema

```sql
contractor_leads     -- 2,200+ contractor businesses
customer_leads       -- Businesses needing waste removal
outreach_logs        -- Message queue and history
sources              -- Scraping source registry
do_not_contact       -- Opt-out list
```

---

## License

MIT — built by [Muaz Saad ur Rehman](https://github.com/MuazAwan)
