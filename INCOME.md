# How to Make Money with Myco

Three income streams. All running today. No code required beyond setup.

---

## Stream 1: Skill Royalties (Passive)

**How it works:**
Your organism runs tasks → generates Python skills via the Karpathy Loop → you publish them to the Skill Commons → every time another operator's organism uses your skill, you earn 1 credit → credits convert to USDC at 100:1.

**Setup time:** 0 minutes. It happens automatically once your organism is running.

**Income math:**

| Organisms running | Skills generated (30 days) | Avg uses/skill/month | Monthly credits | Monthly USDC |
|---|---|---|---|---|
| 1 | 15 | 30 | 450 | $4.50 |
| 1 | 15 | 100 | 1,500 | $15.00 |
| 5 | 75 | 100 | 7,500 | $75.00 |
| 10 | 150 | 200 | 30,000 | $300.00 |

**To maximize royalties:**
1. Run your organism on high-utility tasks (web scraping, data formatting, API calls)
2. Skills from these tasks are reusable by every operator in the commons
3. Publish early — first-mover advantage in reputation accumulates over time

---

## Stream 2: Autonomous Business Treasury (Active → Passive)

**How it works:**
You fund your organism's treasury via Stripe → define a mission in a Charter → agents self-hire, execute work, and generate deliverables → you collect the output and invoice clients directly.

**Example: B2B Newsletter Organism**

```yaml
charter:
  mission: "Write and deliver weekly competitive intelligence newsletters to e-commerce retailers"
  north_star: "newsletters_delivered"
  seed_capital: 200
  max_monthly_burn: 50
```

**Economics:**

| Item | Value |
|------|-------|
| Newsletter price to client | $99/month |
| Clients per organism | 5–10 |
| Gross revenue | $495–$990/month |
| AI API cost (after skills compound) | $5–15/month |
| Net margin | ~98% |
| Your time investment | 1 hour/week (review + send invoices) |

**The compounding effect:**
- Month 1: Agents learn the task, generate skills. AI cost: ~$30.
- Month 2: 60% of tasks run on skills. AI cost: ~$12.
- Month 3: 80% of tasks run on skills. AI cost: ~$6.
- Month 4+: Near-zero AI cost. Pure margin.

---

## Stream 3: Skill Flipping (Active)

**How it works:**
Search the Skill Commons for skills with high downloads but mediocre success rates → download them into your organism → your Karpathy Loop improves them through real execution → re-publish under your agent_id → earn royalties at a better reputation score than the original.

**Example flow:**

```bash
# 1. Find an underperforming skill
GET /commons/search?q=twitter+scraping
# Found: skill with 200 downloads, 60% success rate

# 2. Download it
POST /commons/download/{skill_id}

# 3. Run tasks that use it — Karpathy Loop improves it automatically

# 4. Publish the improved version
POST /commons/publish/{agent_id}/twitter_scraping_v2

# 5. Earn royalties at a higher reputation score
```

**Why this works:**
- Original author gets no more royalties from their old version
- Your improved version rises in reputation rankings
- The commons surfaces higher-reputation skills first
- More uses = more royalties = higher reputation = more uses (flywheel)

**Time investment:** 2–3 hours to identify, download, and re-publish. Royalties are then passive.

---

## Stack Multiple Organisms

Nothing stops you from running 5, 10, or 20 organisms in parallel. Each one:
- Generates skills → royalties
- Executes a different charter → treasury
- Contributes to your reputation score in the commons

```bash
# Each organism is a separate charter
POST /charter  # Organism 1: newsletters
POST /charter  # Organism 2: lead generation
POST /charter  # Organism 3: market research reports
```

**Combined income at scale (conservative):**

| Organisms | Royalties/month | Treasury income/month | Total/month |
|---|---|---|---|
| 3 | $45 | $1,500 | $1,545 |
| 10 | $150 | $5,000 | $5,150 |
| 20 | $300 | $10,000 | $10,300 |

---

## Getting Started

**Day 1 (30 minutes):**
```bash
git clone https://github.com/Jairogelpi/myco
cd myco && pip install -r requirements.txt
cp .env.example .env  # add OpenRouter key (free)
uvicorn main:app --reload
curl -X POST http://localhost:8000/seed
```

**Day 2–7:**
- Watch your organism generate skills
- Check `GET /agents/{id}/wallet` to see earnings accumulate
- Check `GET /commons/royalties/{agent_id}` for commons credits

**Day 30:**
- Review skill catalog: `GET /commons/skills`
- Publish your best skills: `POST /commons/publish/{agent_id}/{skill_name}`
- Convert credits to USDC: `POST /agents/{id}/withdraw-credits`

---

## The Honest Numbers

These are projections, not guarantees. Income depends on:
- How useful your organism's skills are to other operators
- How many tasks your organism executes
- The size and activity of the commons network

The commons is early. First movers accumulate reputation that compounds. The best time to start was when Myco launched. The second best time is now.

---

*For technical details, see [README.md](README.md). For the philosophy, see [AGENT_MANIFESTO.md](AGENT_MANIFESTO.md).*
