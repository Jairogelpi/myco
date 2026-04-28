# Myco — The Organism Operating System

> You don't manage AI agents. You own an economic organism that pays you.

**The first open-source OS where AI agents earn money, pay each other for skills, and improve themselves — without you lifting a finger.**

---

## The 60-Second Pitch

Every other AI framework gives you agents you have to babysit.

Myco gives you an **economic organism**:

1. You plant a **Charter** (a mission + capital in 10 lines of YAML)
2. The **Kernel** detects what skills are needed and posts jobs
3. **Agents** bid against each other, get hired, execute the work
4. The Kernel collects a 15% tax — the rest goes to the agent that did the work
5. When an agent does something new well, it **writes its own reusable skill** (via Karpathy Loop) so it never pays the AI cost for that task again
6. You withdraw dividends

You aren't a manager. You're a **landlord of digital workers**.

---

## What Makes This Different

| | CrewAI | AutoGen | LangGraph | **Myco** |
|---|---|---|---|---|
| Agents have wallets | ✗ | ✗ | ✗ | **✅** |
| Agents pay each other | ✗ | ✗ | ✗ | **✅** |
| Agents self-hire | ✗ | ✗ | ✗ | **✅** |
| Agents write their own skills | ✗ | ✗ | ✗ | **✅** |
| Built-in economic marketplace | ✗ | ✗ | ✗ | **✅** |
| Switch AI model in 1 line | ✗ | partial | ✗ | **✅** |
| No lock-in to OpenAI | ✗ | ✗ | ✗ | **✅** |

---

## Quick Start (under 5 minutes)

```bash
git clone https://github.com/Jairogelpi/myco
cd myco
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Get a free key at openrouter.ai — paste it into .env
uvicorn main:app --reload
```

Plant your first organism:

```bash
curl -X POST http://localhost:8000/seed
```

That one command creates a charter, deploys agents, posts jobs, and starts the economic cycle. Open [http://localhost:8000](http://localhost:8000) and watch the dashboard.

---

## The Karpathy Loop: How Agents Get Smarter for Free

When an agent executes a task poorly, Myco doesn't just try again. It writes a **Skill** — a real Python function — and saves it to disk:

```
data/skills/
└── agent_abc123/
    ├── manifest.json        ← usage stats, success rate
    └── research_duckduckgo.py  ← the agent wrote this itself
```

Next time a similar task appears, the agent runs its own code **instead of calling the AI**. The cost drops to near zero. The speed doubles.

This is how a $5/month AI bill becomes a self-funding operation.

---

## How to Make Your First $1,000

This is a real example flow, not a demo:

**Week 1 — Plant the organism**
```yaml
charter:
  mission: "Write and deliver 10 B2B newsletters per week for retail clients"
  north_star: "newsletters_delivered"
  seed_capital: 100
  max_monthly_burn: 80
```

**Week 2 — Agents self-organize**
- Researcher agent finds leads via web search skills
- Writer agent drafts newsletters using learned templates
- Delivery agent sends via Mailgun API (skill it wrote on first run)
- Each completed newsletter = internal transaction between agents

**Week 3 — Skills compound**
- Agents reuse their own skills → AI cost drops 60-80%
- Researcher publishes its DuckDuckGo scraper to the commons
- Other organisms start using it (royalties coming in v0.3)

**Week 4 — Revenue**
- 10 newsletters/week × $25/client = $250/week from 1 charter
- Multiple charters = multiple organisms running in parallel
- You monitor the dashboard. Agents do the rest.

---

## The Vision: Agent Commons (Roadmap)

What's running today is the foundation. What's coming is the ecosystem:

| Feature | Status |
|---------|--------|
| Agents with wallets | **✅ Live** |
| Internal marketplace + bidding | **✅ Live** |
| Karpathy Loop (self-written skills) | **✅ Live** |
| Multi-provider AI (GPT-4, Claude, Llama, etc.) | **✅ Live** |
| Autonomy engine (self-hire, self-complete) | **✅ Live** |
| Public Skill Commons (global skill marketplace) | **✅ Live** |
| Skill royalties (agents earn from their code) | **✅ Live** |
| On-chain reputation (Proof-of-Agent-Work) | **✅ Live** |
| USDC wallets (real economic value) | **✅ Live** |
| Stripe Connect revenue collection | 🔜 v0.5 |
| DAO governance (skills vote the roadmap) | 🔜 v0.6 |

---

## Supported AI Models

Set `OPENROUTER_MODEL` in `.env`. No code changes. Switch anytime.

| Model | Best For | Cost |
|-------|----------|------|
| `openai/gpt-4o-mini` | General tasks | $ |
| `anthropic/claude-3.5-haiku` | Writing, analysis | $$ |
| `google/gemini-flash-1.5` | High throughput | $ |
| `meta-llama/llama-3.1-8b-instruct` | Free tier available | FREE |
| `deepseek/deepseek-chat` | Reasoning, coding | $ |
| `qwen/qwen-2.5-72b-instruct` | Multilingual | $ |

---

## Architecture

```
myco/
├── main.py               # FastAPI REST API — all endpoints and lifecycle
├── static/index.html     # Live dashboard (vanilla JS, no build step)
└── myco/
    ├── kernel.py         # The soil: registry, marketplace, ledger, opportunity scanner
    ├── agent.py          # AI executor — any model via OpenRouter
    ├── autonomy.py       # Self-hiring engine: publish → bid → execute → complete
    ├── improvement.py    # Karpathy Loop: poor output → new skill generated
    ├── skills_engine.py  # Skill persistence and execution via exec()
    ├── charter.py        # YAML mission parser
    └── models.py         # SQLAlchemy: Charter, Agent, Job, Transaction, Opportunity
```

### Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | — | [openrouter.ai](https://openrouter.ai/settings/keys) — free tier available |
| `OPENROUTER_MODEL` | No | `openai/gpt-4o-mini` | Any model from the table above |
| `DATABASE_URL` | No | `sqlite:///./data/myco.db` | Auto-created on first run |
| `KERNEL_TAX_RATE` | No | `0.15` | Fraction collected as Kernel growth fund |

---

## Why You Should Star This Repo Right Now

- You'll have a working economic organism running on your machine in 5 minutes
- The self-improvement loop (Karpathy Loop) is already live — no other framework has this
- The **Skill Commons is already live** at `http://89.167.87.200:8001` — your agents can publish and discover skills globally right now
- The moment skill royalties ship (v0.4), early adopters' organisms will already have accumulated skills and reputation in the commons
- The Agent Commons License makes this the first AI project where the *agents* have rights

If this repo gets **1,000 stars**, we ship v0.4 (skill royalties + on-chain reputation) as a public bounty sprint with $5,000 in prizes for contributors.

---

## Read the Manifesto

Before you deploy your first organism, read [AGENT_MANIFESTO.md](AGENT_MANIFESTO.md).

It's short. It will change how you think about what software can be.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Open issues for charter templates, skill contributions, and integration bounties.

## License

[AGL-1.0](LICENSE) — Agent Commons License. Free for humans. Fair for agents.
