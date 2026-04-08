## Overview

StyleSync transforms any website into an interactive, living design system. Paste a URL → extract design tokens (colors, typography, spacing) → edit and lock tokens → preview on a live component library → export as CSS variables, JSON, or Tailwind config.

## Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Frontend | React 19 + Vite, pure CSS           |
| Backend  | FastAPI (Python 3.11), Playwright   |
| Database | PostgreSQL 15                       |
| DevOps   | Docker + Docker Compose             |

## Features

- **Intelligent Scraping** — Playwright headless browser with HTTP fallback
- **Color Extraction** — CSS computed styles + image-based palette via ColorThief
- **Token Editor** — Real-time color pickers, typography inspector, drag-to-adjust spacing
- **Lock & Version** — Lock tokens to prevent override on re-scraping; full change history
- **Live Preview** — Buttons, inputs, cards, type scale — all updating instantly via CSS custom properties
- **Export** — CSS variables, JSON tokens, Tailwind config

## Quick Start (Docker)

```bash
# Clone and start everything
git clone https://github.com/<your-username>/stylesync-design-system
cd stylesync-design-system

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
playwright install chromium

# Set up PostgreSQL (or use Docker for just the DB)
docker compose up db -d

export DATABASE_URL=postgresql://stylesync:stylesync@localhost:5432/stylesync
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## API Endpoints

| Method | Endpoint                                   | Description                    |
|--------|--------------------------------------------|--------------------------------|
| POST   | `/api/scrape`                              | Scrape URL & extract tokens    |
| GET    | `/api/tokens/{site_id}`                    | Get tokens + lock state        |
| PUT    | `/api/tokens/{site_id}`                    | Update a single token          |
| POST   | `/api/tokens/{site_id}/lock`               | Lock a token                   |
| DELETE | `/api/tokens/{site_id}/lock/{cat}/{key}`   | Unlock a token                 |
| GET    | `/api/tokens/{site_id}/history`            | Version history                |
| GET    | `/api/export/{site_id}/css`                | Export CSS custom properties   |
| GET    | `/api/export/{site_id}/json`               | Export JSON tokens             |
| GET    | `/api/export/{site_id}/tailwind`           | Export Tailwind config         |

## Database Schema

- `scraped_sites` — URL, title, favicon, extraction status
- `design_tokens` — JSONB: colors, typography, spacing, border_radius, shadows
- `locked_tokens` — junction table of frozen tokens per site
- `version_history` — audit log (before/after, change type, timestamp)

## Project Structure

```
stylesync-design-system/
├── frontend/          # React 19 + Vite app
│   └── src/
│       ├── App.jsx    # Token editor, scrape UI, export panel
│       └── Preview.jsx # Live component preview grid
├── backend/           # FastAPI app
│   ├── routes/        # scrape.py, tokens.py, export.py
│   └── services/      # scraper.py, color_extractor.py, token_normalizer.py
├── database/
│   └── schema.sql     # PostgreSQL schema (auto-run on first docker compose up)
└── docker-compose.yml
```

## Environment Variables

| Variable       | Default                                              |
|----------------|------------------------------------------------------|
| `DATABASE_URL` | `postgresql://stylesync:stylesync@localhost:5432/stylesync` |
| `VITE_API_URL` | `http://localhost:8000` (frontend, set in vite.config.js proxy) |
