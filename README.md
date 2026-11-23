# MarketMapper

Upload a list of businesses. MarketMapper reads each company's public website, works out what it does, finds gaps, and recommends the best-fitting **TxLabz** offers, along with a ready-to-use outreach angle.

- **Team workspace:** email and password login. Everyone on the team sees all uploads.
- **Upload:** CSV or Excel (.xlsx). Only business columns are used (`business_name`, `website`, `city`, `country`, `notes`). Other columns are ignored, and the app tells you which ones.
- **Live progress:** a background worker researches each business while the page updates automatically.
- **Results:** industry, summary, gaps, top 3 offers with reasons, priority and outreach text. You can export everything to CSV.
- **AI or rules:** with an Anthropic or OpenAI API key you get AI analysis. Without one, a fast rule-based engine is used.

---

## Architecture

```
            ┌──────────────┐       ┌─────────────────┐
 Browser ──▶│ web (nginx)  │──/api▶│ api (FastAPI)   │──┐
            │ React SPA    │       │ auth, uploads   │  │
            └──────────────┘       └────────┬────────┘  │
                                            │ enqueue   │ read/write
                                   ┌────────▼────────┐  │
                                   │ redis (queue)   │  │
                                   └────────┬────────┘  │
                                   ┌────────▼────────┐  ▼
                                   │ worker × N (RQ) │──▶ postgres
                                   │ fetch site → AI │
                                   └─────────────────┘
```

Each business is its own queue task, so research scales horizontally. Run more workers to process more websites in parallel (`--scale worker=4`). Job counters use atomic SQL updates, so any number of workers is safe.

| Layer | Tech |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router |
| API | FastAPI, Pydantic, SQLAlchemy 2, Alembic, JWT auth (bcrypt) |
| Jobs | Redis + RQ workers |
| Database | PostgreSQL 16 |
| Research | requests + BeautifulSoup (robots.txt-aware), Anthropic or OpenAI API |
| Deploy | Docker Compose |

## Project structure

```
marketmapper/
├── backend/
│   ├── app/
│   │   ├── api/            # HTTP layer: routes + dependencies (auth)
│   │   ├── core/           # settings, database, security
│   │   ├── models/         # SQLAlchemy tables: users, jobs, businesses
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── ingest.py   # CSV/XLSX parsing + column mapping
│   │   │   └── research/   # fetcher, signals, rules, AI, pipeline
│   │   ├── worker/         # queue + background task
│   │   ├── cli.py          # command-line mode (no web app)
│   │   └── main.py         # FastAPI app
│   ├── migrations/         # Alembic
│   ├── tests/              # pytest (runs on SQLite, no services needed)
│   └── offers.yaml         # TxLabz offer catalog ← edit this
├── frontend/
│   └── src/
│       ├── components/     # ui/ (Button, Card, Badge…) + layout/
│       ├── features/       # auth/ and jobs/ (pages, hooks, components)
│       └── lib/            # api client, auth, types, formatting
├── samples/businesses.csv
├── docker-compose.yml
└── .env.example
```

---

## Quick start (Docker, recommended, works on Windows/Mac/Linux)

1. Install **Docker Desktop** and start it.
2. Create your env file:
   ```bash
   cp .env.example .env          # Windows PowerShell: copy .env.example .env
   ```
   Set `SECRET_KEY` to a long random string:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
   Optionally add `ANTHROPIC_API_KEY` (starts with `sk-ant-`) **or** `OPENAI_API_KEY` (starts with `sk-proj-`) for AI analysis.
3. Start everything:
   ```bash
   docker compose up --build
   ```
4. Open **http://localhost:8080**, create your account and upload `samples/businesses.csv`.

To use more workers for faster research:
```bash
docker compose up --build --scale worker=4
```

When your team has signed up, set `ALLOW_SIGNUP=false` in `.env` and restart.

---

## Local development (without Docker for the app code)

You need PostgreSQL and Redis running. The easiest way is to start only those two from Compose:
```bash
docker compose up db redis
```
Then expose their ports, or install them natively. **Windows note:** RQ workers need Linux or macOS, so on Windows run the worker in Docker or WSL.

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload                          # API on :8000, docs at /docs
rq worker research                                     # in a second terminal
```

**Frontend**
```bash
cd frontend
npm install
npm run dev                                            # http://localhost:5173 (proxies /api → :8000)
```

**Checks** (the same ones CI runs on every push):
```bash
cd backend && ruff check . && pytest -q
cd frontend && npm run lint && npm run build
```

---

## Configuration

All settings are environment variables (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | — | Signs login tokens. **Must** be long and random in production |
| `ANTHROPIC_API_KEY` | empty | Enables AI analysis with Claude |
| `AGENT_MODEL` | `claude-sonnet-5-5` | Claude model |
| `OPENAI_API_KEY` | empty | Enables AI analysis with OpenAI |
| `OPENAI_MODEL` | `gpt-6.2-sol` | OpenAI model |
| `AI_PROVIDER` | `auto` | `auto` (whichever key is set, Anthropic first), `anthropic` or `openai`. With no key, rules are used |
| `ALLOW_SIGNUP` | `true` | Turn off after the team has registered |
| `MAX_UPLOAD_MB` | `10` | Upload size limit |
| `MAX_ROWS_PER_UPLOAD` | `2000` | Rows per file |
| `MAX_PAGES_PER_SITE` | `4` | Pages read per website |

## Editing the offers

`backend/offers.yaml` holds the TxLabz catalog. Each offer has:
- `fits`: the description the AI reads when matching
- `signals`: what the rule engine looks for
- `weight`: how strongly it ranks

The `seller` text tells the AI who is making the offer. Restart the API and workers after editing.

## API

Interactive docs are at **/docs** on the API (e.g. http://localhost:8000/docs in local dev).

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get token (form: `username`, `password`) |
| GET | `/api/auth/me` | Current user |
| POST | `/api/jobs` | Upload CSV/XLSX (multipart `file`) |
| GET | `/api/jobs` | List uploads |
| GET | `/api/jobs/{id}` | Upload status and progress |
| GET | `/api/jobs/{id}/businesses` | Results (`offset`, `limit`) |
| GET | `/api/jobs/{id}/export.csv` | Download results |
| DELETE | `/api/jobs/{id}` | Delete upload and results |

## Responsible use

- MarketMapper researches **businesses** from their public websites only. It does not look up private individuals, and it discards personal columns from uploads.
- It respects `robots.txt`, waits between page requests, and blocks internal or private network addresses.
- Contact businesses through their published business channels, and follow CAN-SPAM, TCPA, GDPR or other local rules for outreach.
