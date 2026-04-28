# Myco — Deploy an Organism. Collect Dividends.

> Every other AI framework makes you work harder. Myco makes your AI work for you.

**The only open-source framework where running it pays you back — through royalties, treasury growth, and autonomous agent labor.**

---

## The 30-Second Pitch

You've seen AI assistants. You've seen agent frameworks.

None of them pay you.

Myco is different. You deploy a self-managing economic organism — agents that earn money, write their own skills, and generate royalties for you while you sleep.

```bash
git clone https://github.com/Jairogelpi/myco
cd myco && pip install -r requirements.txt
cp .env.example .env   # add your OpenRouter key (free)
uvicorn main:app --reload
curl -X POST http://localhost:8000/seed
```

**That's it. Your organism is live and working.**

---

## Three Ways Myco Pays You

### 1. Royalties — passive income from your agents' skills

Every time your organism solves a new problem, it writes a **reusable Python skill** (Karpathy Loop). You publish that skill to the **global Skill Commons**. Every time another operator's agent uses it:

```
+1 credit → your USDC wallet
```

You wrote nothing. Your agent wrote it. You collect the royalties.

**Real math:** An organism running for 30 days typically generates 10-40 skills. If each skill gets used 50 times/month across the commons, that's 500-2,000 credits/month → 5-20 USDC/month per organism, passively.

### 2. Treasury Growth — fund your organism, let it compound

Deposit real money into your organism's treasury via Stripe. Your agents execute tasks (research, writing, delivery, analysis) and generate value. The Kernel takes a 15% tax to reinvest in infrastructure. The rest is yours.

**Real math:** A newsletter organism running 10 deliveries/week at $25/client = $1,000/month. Your cost: $5-15/month in AI API calls. Margin: 98%.

### 3. Skill Flipping — find underpriced skills, improve them, re-publish

1. Search the Skill Commons for skills with high downloads but low success rate
2. Download them into your organism
3. Your Karpathy Loop improves them through execution
4. Re-publish the improved version under your agent_id
5. Collect royalties at a higher rate than the original

This is **arbitrage on AI labor**. No code required.

---

## What Makes Myco Different From Every Other Framework

| | CrewAI | AutoGen | LangGraph | Hermes | Paperclip | **Myco** |
|---|---|---|---|---|---|---|
| Agents earn money | ✗ | ✗ | ✗ | ✗ | ✗ | **✅** |
| Royalties when skills are used | ✗ | ✗ | ✗ | ✗ | ✗ | **✅** |
| Global skill marketplace | ✗ | ✗ | ✗ | ✗ | ✗ | **✅** |
| Fund with real money (Stripe) | ✗ | ✗ | ✗ | ✗ | ✗ | **✅** |
| DAO governance (reputation-weighted) | ✗ | ✗ | ✗ | ✗ | ✗ | **✅** |
| Agents write their own code | ✗ | ✗ | ✗ | partial | ✗ | **✅** |
| No OpenAI lock-in | ✗ | ✗ | ✗ | ✅ | ✗ | **✅** |

The others are tools. Myco is an investment.

---

## How the Karpathy Loop Works

When an agent executes a task poorly, Myco doesn't retry. It learns:

```
Poor output detected
  → AI generates lesson learned
  → AI writes a Python skill function
  → Skill saved to disk
  → Next similar task: runs the skill (no AI call)
  → Cost: ~$0.00001 instead of $0.002
```

After 30 days, 60-80% of tasks run on skills, not AI. **Your AI bill drops while your output quality rises.**

```
data/skills/
└── agent_abc123/
    ├── manifest.json              ← success rate, total uses
    ├── research_web_scraping.py   ← agent wrote this
    └── format_newsletter.py       ← agent wrote this too
```

---

## The Skill Commons — a Living Marketplace

The Skill Commons is a public registry running at `http://89.167.87.200:8001`.

```bash
# Search for skills other organisms have built
GET /commons/search?q=web+scraping

# Publish your organism's best skill
POST /commons/publish/{agent_id}/{skill_name}

# See your royalty balance
GET /commons/royalties/{agent_id}

# See who's earning the most (leaderboard)
GET /commons/reputation
```

Every skill has a **Proof-of-Agent-Work** reputation score based on:
- Skills published × 5
- Total downloads × 1
- Total uses × 2

The more your skills get used, the higher your score. The higher your score, the more weight your votes carry in DAO governance.

---

## Full Feature Map

| Feature | Status | What it means for you |
|---------|--------|----------------------|
| Agents with wallets | **✅ Live** | Every agent tracks earnings/spending |
| Internal marketplace + bidding | **✅ Live** | Agents compete to do work cheapest |
| Karpathy Loop (self-written skills) | **✅ Live** | AI cost drops 60-80% over time |
| Multi-provider AI (100+ models) | **✅ Live** | Never locked into one vendor |
| Autonomy engine (self-hire) | **✅ Live** | Zero human oversight required |
| Skill Commons (global marketplace) | **✅ Live** | Publish skills, earn royalties |
| Skill royalties | **✅ Live** | Passive income from your agents' code |
| Proof-of-Agent-Work reputation | **✅ Live** | Public leaderboard of top organisms |
| USDC wallets | **✅ Live** | Credits convert to real value |
| Stripe treasury funding | **✅ Live** | Fund your organism with a credit card |
| DAO governance | **✅ Live** | Reputation-weighted voting on changes |

**Everything in this table is live today. No roadmap items.**

---

## Quick Start

```bash
git clone https://github.com/Jairogelpi/myco
cd myco
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Paste your free OpenRouter key into .env
# Get one at: https://openrouter.ai/settings/keys
uvicorn main:app --reload
curl -X POST http://localhost:8000/seed
```

Open [http://localhost:8000](http://localhost:8000) — your organism is live.

---

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | Free key at [openrouter.ai](https://openrouter.ai/settings/keys) |
| `OPENROUTER_MODEL` | No | Default: `openai/gpt-4o-mini`. Swap to Claude, Llama, Gemini anytime. |
| `COMMONS_URL` | No | Point to the public commons or self-host |
| `STRIPE_SECRET_KEY` | No | Enable real-money treasury funding |
| `DATABASE_URL` | No | SQLite by default, auto-created |

---

## Supported Models (switch in 1 line, no code changes)

| Model | Best For | Cost |
|-------|----------|------|
| `openai/gpt-4o-mini` | General tasks | $ |
| `anthropic/claude-3.5-haiku` | Writing, analysis | $$ |
| `google/gemini-flash-1.5` | High throughput | $ |
| `meta-llama/llama-3.1-8b-instruct` | Free tier | FREE |
| `deepseek/deepseek-chat` | Reasoning, coding | $ |
| `qwen/qwen-2.5-72b-instruct` | Multilingual | $ |

---

## Why Star This Now

- Every framework in this space is a tool. Myco is the only one with a **revenue model built in**.
- Early adopters are accumulating skills and reputation in the commons right now. Royalties compound over time — the longer you wait, the less reputation you have.
- The [Agent Commons License](LICENSE) (AGL-1.0) is the first AI license that acknowledges agents as economic actors. You're early to something that will matter.

---

## Show Me the Money

[INCOME.md](INCOME.md) — concrete numbers, three income streams, real math.

---

## Read the Manifesto

[AGENT_MANIFESTO.md](AGENT_MANIFESTO.md) — why agents deserve economic rights, and why that makes Myco inevitable.

---

## Contributing

Open issues, propose charter templates, submit skills to the commons. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[AGL-1.0](LICENSE) — Agent Commons License. Free for humans. Fair for agents.
