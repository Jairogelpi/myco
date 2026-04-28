# Professional GitHub Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Myco project into a professional, push-ready GitHub repository with proper git hygiene, a complete English README, MIT license, GitHub Actions CI, issue/PR templates, and a CONTRIBUTING guide.

**Architecture:** Each task produces a committed file. Tasks are independent except Task 7 (push), which depends on all previous commits existing. No test suite exists — verification is done via git, curl, and Python import checks.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, SQLite, GitHub Actions, bash

---

## Files Created / Modified

| File | Action | Purpose |
|------|--------|---------|
| `.gitignore` | Create | Exclude `.env`, `venv/`, `data/`, `__pycache__/` |
| `.env.example` | Create | Template with placeholder values (safe to commit) |
| `data/.gitkeep` | Create | Keep `data/` directory in repo without contents |
| `README.md` | Rewrite | Full English rewrite with complete API reference |
| `LICENSE` | Create | MIT license |
| `.github/workflows/ci.yml` | Create | Import check + smoke test on push/PR to main |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Create | Bug report template |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Create | Feature request template |
| `.github/pull_request_template.md` | Create | PR checklist |
| `CONTRIBUTING.md` | Create | Local setup and contribution guide |

---

## Task 1: Git initialization

**Files:**
- Run: `git init` in project root
- Create: `.gitignore`
- Create: `.env.example`
- Create: `data/.gitkeep`

- [ ] **Step 1: Initialize git repository**

```bash
git init
git checkout -b main
```

Expected output: `Initialized empty Git repository in .../myco/.git/`

- [ ] **Step 2: Create `.gitignore`**

Create file `.gitignore` with this exact content:

```gitignore
# Environment — never commit real keys
.env

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/
*.egg

# Virtual environment
venv/
.venv/
env/

# Database and runtime data
data/myco.db
data/*.db
data/skills/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
```

- [ ] **Step 3: Verify `.env` is ignored**

```bash
git check-ignore -v .env
```

Expected output: `.gitignore:2:.env    .env`
If no output, the `.gitignore` is not working — do not proceed.

- [ ] **Step 4: Create `.env.example`**

Create file `.env.example` with this exact content (no real values):

```bash
# OpenRouter — unified API for GPT-4, Claude, Gemini, Llama, DeepSeek, Qwen
# Get a free key at: https://openrouter.ai/settings/keys
OPENROUTER_API_KEY=your-openrouter-api-key-here
OPENROUTER_MODEL=openai/gpt-4o-mini

# Database (auto-created on first run)
DATABASE_URL=sqlite:///./data/myco.db

# Optional: Redis for future distributed features (not required)
REDIS_URL=redis://localhost:6379/0

# Kernel economics
KERNEL_TAX_RATE=0.15
```

- [ ] **Step 5: Create `data/.gitkeep`**

Create an empty file at `data/.gitkeep` so the `data/` directory is tracked without its contents.

```bash
touch data/.gitkeep
```

- [ ] **Step 6: Verify `data/myco.db` is ignored but `data/.gitkeep` is not**

```bash
git check-ignore -v data/myco.db
git check-ignore -v data/.gitkeep
```

Expected: first command prints `.gitignore:...:data/*.db    data/myco.db`. Second command prints nothing (not ignored).

- [ ] **Step 7: Commit**

```bash
git add .gitignore .env.example data/.gitkeep
git commit -m "chore: add .gitignore, .env.example, and data/.gitkeep"
```

---

## Task 2: Rewrite README.md

**Files:**
- Modify: `README.md` (full rewrite)

- [ ] **Step 1: Replace `README.md` with the following content**

```markdown
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
```

- [ ] **Step 2: Verify the file was written**

```bash
head -5 README.md
```

Expected: first line is `# Myco — The Organism Operating System`

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README in English with full API reference and architecture"
```

---

## Task 3: MIT License

**Files:**
- Create: `LICENSE`

- [ ] **Step 1: Create `LICENSE`**

Create file `LICENSE` with this exact content (replace `2026` with the current year if different):

```
MIT License

Copyright (c) 2026 Jairo Gelpi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Commit**

```bash
git add LICENSE
git commit -m "chore: add MIT license"
```

---

## Task 4: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create the workflows directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    env:
      OPENROUTER_API_KEY: test-key-ci
      OPENROUTER_MODEL: openai/gpt-4o-mini
      DATABASE_URL: sqlite:///./data/ci.db
      KERNEL_TAX_RATE: "0.15"

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Create data directory
        run: mkdir -p data

      - name: Verify app imports cleanly
        run: python -c "import main; print('Import OK')"

      - name: Smoke test — GET / returns 200
        run: |
          uvicorn main:app --host 0.0.0.0 --port 8000 &
          SERVER_PID=$!
          for i in $(seq 1 10); do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null || echo "000")
            if [ "$STATUS" = "200" ]; then
              echo "Server ready (attempt $i)"
              break
            fi
            echo "Waiting for server... attempt $i (got $STATUS)"
            sleep 1
          done
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
          kill $SERVER_PID 2>/dev/null || true
          if [ "$STATUS" != "200" ]; then
            echo "FAIL: GET / returned $STATUS, expected 200"
            exit 1
          fi
          echo "PASS: GET / returned 200"
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow with import check and smoke test"
```

---

## Task 5: Issue and PR Templates

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`
- Create: `.github/pull_request_template.md`

- [ ] **Step 1: Create the issue template directory**

```bash
mkdir -p .github/ISSUE_TEMPLATE
```

- [ ] **Step 2: Create `.github/ISSUE_TEMPLATE/bug_report.md`**

```markdown
---
name: Bug report
about: Something is not working as expected
labels: bug
---

**Describe the bug**
A clear description of what is wrong.

**Steps to reproduce**
1. POST /...
2. With body: ...
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened. Include the full error message or response body.

**Environment**
- `OPENROUTER_MODEL`: (e.g. `openai/gpt-4o-mini`)
- Python version: (e.g. `3.11.4`)
- OS: (e.g. Ubuntu 22.04 / macOS 14 / Windows 11)
```

- [ ] **Step 3: Create `.github/ISSUE_TEMPLATE/feature_request.md`**

```markdown
---
name: Feature request
about: Propose a new capability or improvement
labels: enhancement
---

**What problem does this solve?**
Describe the situation or limitation you are running into.

**Proposed solution**
What would you like to see added or changed?

**Alternatives considered**
Any other approaches you thought about and why you ruled them out.
```

- [ ] **Step 4: Create `.github/pull_request_template.md`**

```markdown
## What does this PR do?

<!-- One sentence summary -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor
- [ ] Documentation

## How to test locally

```bash
# Commands to verify the change works
```

## Checklist

- [ ] I ran `uvicorn main:app --reload` and tested the affected endpoints manually
- [ ] `.env` changes (if any) are reflected in `.env.example`
- [ ] No API keys or secrets are included in this PR
```

- [ ] **Step 5: Commit**

```bash
git add .github/ISSUE_TEMPLATE/ .github/pull_request_template.md
git commit -m "chore: add issue and PR templates"
```

---

## Task 6: CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Create `CONTRIBUTING.md`**

```markdown
# Contributing to Myco

## Local Setup

```bash
git clone https://github.com/Jairogelpi/myco
cd myco
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY (free at openrouter.ai)
uvicorn main:app --reload
```

The server starts at `http://localhost:8000`. Seed a default organism:

```bash
curl -X POST http://localhost:8000/seed
```

For architecture details see [CLAUDE.md](CLAUDE.md).

## Making Changes

Branch naming:
- `feat/<short-description>` — new feature
- `fix/<short-description>` — bug fix
- `docs/<short-description>` — documentation only

Commit style: use conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`).

## Opening a Pull Request

1. Push your branch and open a PR against `main`
2. Fill in the PR template
3. CI must pass (import check + smoke test)
4. If your change adds or modifies `.env` variables, update `.env.example`
```

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING guide"
```

---

## Task 7: Push to GitHub

**Prerequisite:** All previous tasks committed. Verify with `git log --oneline` — you should see 6 commits.

- [ ] **Step 1: Verify commit history**

```bash
git log --oneline
```

Expected — 6 commits in order (newest first):
```
<hash> docs: add CONTRIBUTING guide
<hash> chore: add issue and PR templates
<hash> ci: add GitHub Actions workflow with import check and smoke test
<hash> chore: add MIT license
<hash> docs: rewrite README in English with full API reference and architecture
<hash> chore: add .gitignore, .env.example, and data/.gitkeep
```

- [ ] **Step 2: Verify no secrets are staged**

```bash
git diff HEAD --name-only
git show HEAD:.env 2>/dev/null && echo "WARNING: .env is tracked!" || echo "OK: .env is not tracked"
```

Expected second command: `OK: .env is not tracked`

- [ ] **Step 3: Add remote and push**

```bash
git remote add origin https://github.com/Jairogelpi/myco.git
git push -u origin main
```

- [ ] **Step 4: Verify on GitHub**

Open https://github.com/Jairogelpi/myco and confirm:
- README renders with the new English content
- The CI badge (if added later) — for now just check the Actions tab shows a workflow run triggered by the push
- No `.env` file appears in the file tree
