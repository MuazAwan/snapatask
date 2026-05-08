# Snapatask — Rubbish Removal Marketplace Automation

A full AI agent system for finding and contacting rubbish removal contractors in the UK.

## What It Does
- Scrapes contractor leads from Environment Agency, Checkatrade, Gumtree, Yell
- Scores and deduplicates leads automatically
- 9 AI agents (via Paperclip + Hermes) manage the full pipeline
- CRM dashboard for manual outreach review

## Stack
- Node.js + Express (CRM dashboard)
- Python (scrapers)
- PostgreSQL (database)
- Docker Compose (all services)
- Paperclip AI (agent orchestration)
- Hermes Agent (AI execution via Claude)

## Services
| Service | Port | Purpose |
|---------|------|---------|
| dashboard | 3200 | CRM frontend |
| paperclip | 3100 | Agent manager |
| postgres | 5432 | Database |
| hermes | - | AI executor |
| openclaw | 18789 | Agent tools |
| traefik | 80/443 | Reverse proxy |

## Setup
1. Copy .env.example to .env and fill in credentials
2. docker compose up -d
3. Run scrapers: python3 env-agency-scraper.py
4. Open CRM: http://your-ip:3200

## Agents
- CEO — delegates tasks to subagents
- Reporting Agent — queries DB and generates reports
- Lead Scorer — scores unscored leads
- Contractor Finder — finds contractor leads
- Customer Lead Finder — finds customer leads
- Data Extractor — cleans and normalises data
- Deduplication Agent — finds and marks duplicates
- Outreach Agent — prepares outreach messages
- Reply Monitor — tracks replies and conversion
