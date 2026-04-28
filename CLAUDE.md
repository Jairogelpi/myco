# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Myco** is an autonomous digital worker ecosystem — a FastAPI backend + vanilla HTML dashboard implementing self-managing AI agents that operate as economic units in a decentralized marketplace. Agents self-hire, self-bid, self-execute, and self-improve through a Karpathy Loop that generates reusable Python skills.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (auto-reload)
uvicorn main:app --reload
# Server: http://localhost:8000 | Dashboard: http://localhost:8000/

# Seed a default organism (charter + agents + jobs)
curl -X POST http://localhost:8000/seed

# CLI tool
python myco_cli.py seed          # seed organism
python myco_cli.py state         # view full state
python myco_cli.py execute <agent_id> <task>
```

**No test suite or linter is configured.**

## Configuration

Copy `.env.example` to `.env` and set:
- `OPENROUTER_API_KEY` — required (primary AI backend via OpenRouter)
- `OPENROUTER_MODEL` — default `z-ai/glm-5`; supports Claude, GPT-4, Gemini, Llama, DeepSeek, Qwen
- `DATABASE_URL` — SQLite path (auto-created at `./data/myco.db`)
- `KERNEL_TAX_RATE` — default 15%

The `openai` SDK is used with `base_url=https://openrouter.ai/api/v1` to reach OpenRouter. Legacy `OPENAI_API_KEY`/`OPENAI_MODEL` are fallbacks.

## Architecture

### Entry Point
- [main.py](main.py) — FastAPI app (481 lines); all REST endpoints, startup lifecycle, CORS, static file serving

### Core Package (`myco/`)
- [myco/kernel.py](myco/kernel.py) — The "soil": agent registry, job marketplace, ledger, opportunity scanner. Collects 15% tax on all transactions; scans for skill/capacity/market gaps and auto-publishes jobs.
- [myco/agent.py](myco/agent.py) — AI executor: builds system prompts from agent role/skills, calls OpenRouter, handles multi-provider fallback.
- [myco/autonomy.py](myco/autonomy.py) — Self-hiring engine: agents publish jobs, auto-bid (score = skill_match + reputation / bid_price), auto-execute, auto-complete. Full autonomy cycle in one call.
- [myco/improvement.py](myco/improvement.py) — Karpathy Loop: evaluates AI output quality; if poor, triggers skill generation — AI writes new Python functions stored as reusable skills.
- [myco/skills_engine.py](myco/skills_engine.py) — Manages learned Python skills in `data/skills/{agent_id}/`; dynamically loads and executes via `exec()`; tracks usage stats and success rate per skill.
- [myco/charter.py](myco/charter.py) — Parses YAML-defined missions (capital, burn limits, ethics, north-star metric).
- [myco/models.py](myco/models.py) — SQLAlchemy ORM: `Charter`, `Agent`, `Job`, `Transaction`, `Opportunity`.
- [myco/config.py](myco/config.py) — Pydantic Settings loading from `.env`.

### Frontend
- [static/index.html](static/index.html) — Single-page dashboard in pure HTML/CSS/JS; no build step.

### Database
- SQLite at `./data/myco.db`; schema auto-created via `Base.metadata.create_all` on startup. No migrations system.

## Key Data Flow

1. **Charter** defines the mission and capital budget.
2. **Kernel** scans for gaps → publishes **Jobs** to the marketplace.
3. **Agents** bid on jobs (autonomy engine scores bids) → assigned agent executes via AI.
4. On completion, kernel collects tax, pays agent, records **Transaction**.
5. If output quality is low, **Karpathy Loop** generates a new **Skill** (Python function) stored to disk and reused in future tasks.

## API Surface (main.py)

| Group | Key Endpoints |
|-------|---------------|
| Charter | `POST /charter`, `GET /charter` |
| Agents | `POST /agents`, `GET /agents`, `POST /agents/{id}/execute` |
| Marketplace | `POST /jobs`, `POST /jobs/{id}/bid`, `POST /jobs/{id}/complete` |
| Autonomy | `POST /autonomy/cycle` (full loop), `POST /autonomy/detect` |
| Self-Improvement | `POST /improvement/evaluate`, `POST /improvement/execute-with-skills` |
| Ledger | `GET /ledger/pnl` |
| Setup | `POST /seed` |
