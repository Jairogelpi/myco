# Myco — The Organism Operating System

> From agents that you manage... to organisms that feed you.

Myco is an autonomous digital worker ecosystem built on FastAPI. You plant a **Charter** — a YAML mission with capital and ethics constraints — and Myco deploys self-managing AI agents that hire each other, bid on jobs, execute tasks, and improve themselves through a generated-skill loop.

Unlike traditional agent frameworks, Myco treats agents as **economic units**: they hold wallets, earn tokens, pay each other, and fund the Kernel's growth tax. The system runs without human intervention after the Charter is planted.

## Quick Start

```bash
git clone https://github.com/Jairogelpi/myco
cd myco
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY
uvicorn main:app --reload
```

Seed a default organism (charter + agents + jobs) in one call:

```bash
curl -X POST http://localhost:8000/seed
curl http://localhost:8000/organism
```

Dashboard available at [http://localhost:8000](http://localhost:8000).

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | — | Get a free key at [openrouter.ai](https://openrouter.ai/settings/keys) |
| `OPENROUTER_MODEL` | No | `openai/gpt-4o-mini` | Any model ID from the table below |
| `DATABASE_URL` | No | `sqlite:///./data/myco.db` | SQLite path, auto-created on first run |
| `KERNEL_TAX_RATE` | No | `0.15` | Fraction of each payment collected as Kernel tax |

## Supported AI Models

Switch models by changing `OPENROUTER_MODEL` in `.env` — no code changes required.

| Model | Best For | Cost |
|-------|----------|------|
| `openai/gpt-4o-mini` | General tasks | $ |
| `anthropic/claude-3.5-haiku` | Writing, analysis | $$ |
| `google/gemini-flash-1.5` | High throughput | $ |
| `meta-llama/llama-3.1-8b-instruct` | Free tier available | FREE |
| `deepseek/deepseek-chat` | Reasoning, coding | $ |
| `qwen/qwen-2.5-72b-instruct` | Multilingual | $ |

## Architecture

```
myco/
├── main.py               # FastAPI REST API — all endpoints and startup lifecycle
├── static/index.html     # Web dashboard (vanilla HTML/CSS/JS, no build step)
└── myco/
    ├── kernel.py         # Central registry, marketplace, ledger, opportunity scanner
    ├── agent.py          # OpenRouter executor — builds prompts, calls AI, handles fallback
    ├── autonomy.py       # Self-hiring engine — agents publish, bid, execute, and complete autonomously
    ├── improvement.py    # Karpathy Loop — evaluates output quality, generates skills when quality is low
    ├── skills_engine.py  # Manages learned Python skills in data/skills/{agent_id}/, runs them via exec()
    ├── charter.py        # YAML mission parser — capital, burn limits, north-star metric, ethics
    └── models.py         # SQLAlchemy ORM — Charter, Agent, Job, Transaction, Opportunity
```

### How It Works

1. A **Charter** defines the mission, seed capital, and ethics constraints
2. The **Kernel** scans for skill, capacity, and market gaps → publishes **Jobs** to the marketplace
3. **Agents** bid on jobs (score = skill match + reputation / bid price) → the winning agent executes the task via AI
4. On completion, the Kernel collects a 15% tax, pays the agent, and records the **Transaction**
5. If output quality is poor, the **Karpathy Loop** generates a new **Skill** — a Python function stored to disk and reused in future tasks without calling the AI again

## API Reference

| Group | Method | Endpoint | Description |
|-------|--------|----------|-------------|
| **System** | GET | `/` | Web dashboard |
| | GET | `/system/model` | Current AI provider and model |
| **Charter** | POST | `/charter` | Plant a new charter from YAML |
| | GET | `/charter` | Get the active charter |
| | GET | `/charter/template` | Default charter YAML template |
| **Organism** | GET | `/organism` | Full state — charter, agents, jobs, P&L |
| **Agents** | POST | `/agents` | Register a new agent |
| | GET | `/agents` | List all agents |
| | GET | `/agents/{id}` | Agent details and transaction history |
| | POST | `/agents/{id}/execute` | Execute a task via AI |
| **Marketplace** | POST | `/jobs` | Publish a job to the marketplace |
| | GET | `/jobs` | List open jobs |
| | POST | `/jobs/{id}/bid` | Bid on a job (auto-assigns if best score) |
| | POST | `/jobs/{id}/complete` | Complete job, pay agent, collect tax |
| **Opportunities** | POST | `/opportunities/scan` | Kernel scans for gaps and auto-publishes jobs |
| **Autonomy** | POST | `/autonomy/cycle` | Full autonomous cycle: publish → bid → execute → complete |
| | POST | `/autonomy/publish` | Agent self-publishes a job |
| | POST | `/autonomy/bid/{job_id}` | Auto-bid on a specific job |
| | POST | `/autonomy/execute/{job_id}` | Auto-execute an assigned job |
| | POST | `/autonomy/complete/{job_id}` | Auto-complete with payment |
| | POST | `/autonomy/detect` | Agent detects skill gap and publishes a job |
| **Self-Improvement** | POST | `/improvement/evaluate` | Run Karpathy Loop evaluation |
| | POST | `/improvement/execute-with-skills` | Execute using learned skills before falling back to AI |
| | GET | `/improvement/skills/{agent_id}` | List an agent's learned skills |
| | GET | `/improvement/skill-code/{agent_id}/{skill}` | Get the Python source of a skill |
| **Ledger** | GET | `/ledger/pnl` | Organism profit and loss |
| **Setup** | POST | `/seed` | One-click setup: charter + agents + jobs |

## Charter Template

```yaml
charter:
  mission: "Generate $10K/month selling newsletters to retailers"
  north_star: "MRR"
  seed_capital: 500
  max_monthly_burn: 400
  ethics:
    - "No scraping sites with robots.txt"
    - "No generating spam"
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
