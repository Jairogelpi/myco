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
