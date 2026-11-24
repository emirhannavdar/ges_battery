# GES Battery

GES Battery combines photovoltaic plant simulation, weather data and electricity market prices. A FastAPI backend and a Next.js dashboard let operators run daily scenarios, review hourly results and compare grid energy across saved runs.

The project is an active prototype. Simulation results are calculated from model inputs and weather data. The application currently models PV production, inverter control and transformer losses. Battery dispatch and revenue optimization are planned.

## Features

- **PV simulation:** Inverter output, temperature effects, active and reactive power limits, transformer losses and curtailment.
- **Stateful sessions:** User-owned sessions with start, step, reset and inverter fault operations. Session state is stored in PostgreSQL.
- **Daily scenarios:** Run a 24-hour simulation, save hourly results and compare scenarios in the dashboard.
- **External data:** Retrieve EPİAŞ PTF and KPTF prices and Visual Crossing weather data. PTF and weather records can be stored in PostgreSQL.
- **Authentication:** JWT access and refresh tokens, Argon2 password hashing, Redis-backed login rate limiting and role-based authorization.
- **Database migrations:** Alembic initializes the PostgreSQL schema for users, weather, prices and simulation records.

## Technology stack

| Layer | Technologies |
| --- | --- |
| Backend | Python 3.12+, FastAPI, Pydantic |
| Database | PostgreSQL, SQLAlchemy, Psycopg 3, Alembic |
| Jobs and caching | Redis, Celery, Celery Beat |
| Frontend | Next.js, React, TypeScript, ECharts, Zod |
| Tooling | uv, pytest, GitHub Actions, npm |

The browser calls the Next.js server, which forwards API requests to FastAPI. FastAPI runs simulations and reads and writes PostgreSQL data. Redis supports login rate limiting, EPİAŞ token caching and the Celery broker.

## Local development

### 1. Install dependencies

Install Python 3.12+, [uv](https://docs.astral.sh/uv/), PostgreSQL, Redis and a Node.js version supported by the frontend.

```powershell
git clone https://github.com/emirhannavdar/ges_battery.git
cd ges_battery
uv sync --frozen
```

### 2. Configure the backend

Create a PostgreSQL database and add a `.env` file at the repository root. Replace the placeholders with your own settings. If your PostgreSQL instance listens on `5433`, use that port in `_DATABASE_URL`.

```dotenv
_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/DATABASE
_REDIS_URL=redis://localhost:6379/0

_VISUAL_CROSSING_API_KEY=YOUR_KEY
_VISUAL_CROSSING_BASE_URI=YOUR_VISUAL_CROSSING_BASE_URL

_EPIAS_BASE_URI=YOUR_EPIAS_BASE_URL
_TGT_URL=YOUR_EPIAS_TGT_URL
_PTF_ENDPOINT=YOUR_PTF_ENDPOINT_PATH
_KPTF_ENDPOINT=YOUR_KPTF_ENDPOINT_PATH
_EPIAS_USERNAME=YOUR_EPIAS_USERNAME
_EPIAS_PASSWORD=YOUR_EPIAS_PASSWORD

_HASH_PASSWORD=YOUR_PASSWORD_HASH_CONFIGURATION
_XSECRET_KEY_1=YOUR_PREVIOUS_JWT_SIGNING_SECRET
_XSECRET_KEY_2=YOUR_ACTIVE_JWT_SIGNING_SECRET
```

Start Redis before using the login endpoint. The login rate limiter currently connects to `localhost:6379`. EPİAŞ and Celery use `_REDIS_URL`. Keep `.env`, credentials and signing keys out of Git.

### 3. Apply database migrations

For a newly created, empty database, run this from the repository root:

```powershell
uv run alembic upgrade head
```

For a database created manually before Alembic was introduced, back it up and compare the existing schema with the initial migration before recording a baseline. The initial migration creates the application tables.

On a fresh database, provision the first admin through a trusted local terminal. The following PowerShell example prompts for the password without echoing it and uses the application's own password hashing and user creation functions:

```powershell
uv run python -c "from getpass import getpass; from database.database import SessionLocal, create_user_db; from hash.hash_pass import get_hashed_password; username=input('Username: '); full_name=input('Full name: '); email=input('Email: '); password=getpass('Password: '); assert password, 'Password is required'; db=SessionLocal(); create_user_db(db, username=username, full_name=full_name, email=email, hashed_password=get_hashed_password(password), role='admin'); db.close()"
```

After signing in as admin, use `POST /auth/sign` to create additional accounts.

### 4. Start FastAPI

```powershell
uv run uvicorn api.api:app --reload --host 127.0.0.1 --port 8071
```

Swagger UI is available at [http://127.0.0.1:8071/docs](http://127.0.0.1:8071/docs).

### 5. Start the dashboard

In a second terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The example `BACKEND_URL` points to `http://127.0.0.1:8071`. If you use a different port, update `frontend/.env.local` to match.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/auth/token` | Sign in and receive access and refresh tokens |
| `POST` | `/auth/refresh-access-token` | Renew the access token using `X-Refresh-Token` |
| `GET` | `/auth/users/me` | Read the current user's profile |
| `POST` | `/auth/sign` | Create a user as an admin |
| `POST` | `/api/v1/epias/PTF` | Retrieve and persist PTF prices |
| `POST` | `/api/v1/epias/KPTF` | Retrieve KPTF data |
| `GET` | `/api/v1/visual_crossing` | Retrieve and store weather data |
| `POST` | `/inverter/sessions` | Create a stateful simulation session |
| `POST` | `/inverter/sessions/{simulation_id}/start` | Start a simulation session |
| `POST` | `/inverter/sessions/{simulation_id}/step` | Advance a session using stored weather |
| `POST` | `/inverter/daily` | Run and save a daily scenario |
| `GET` | `/inverter/simulations` | List saved daily scenarios |
| `GET` | `/inverter/simulations/{simulation_id}` | Read a saved run and its hourly results |
| `GET` | `/inverter/simulations/compare` | Compare two saved runs |

Stateful sessions use UUIDs. Saved daily runs use integer IDs. Daily simulation requires a complete set of hourly weather records for the selected date.

Example body for `POST /inverter/daily`:

```json
{
  "simulation_date": "2026-11-23",
  "inverter_count": 3,
  "inverter_ac_rated_kw": 900,
  "inverter_dc_rated_kw": 1000,
  "ekk_active_power_limit_kw": 800
}
```

## Authentication and sessions

Access tokens expire after 15 minutes. Refresh tokens expire after 7 days and are checked against the current refresh `jti` stored for the user. A new login replaces that identifier. Users with refresh tokens issued before `jti` became mandatory should sign in again.

The dashboard keeps the access token in memory and the refresh token in an HTTP-only cookie. After a reload or an expired access token, the browser calls `/api/session/refresh` on Next.js. The server reads the cookie and forwards the refresh token to FastAPI.

Logout clears the browser session. Server-side refresh token revocation on logout and rotation on each refresh are planned.

## Background jobs

Celery uses Redis as its broker. Run the worker and scheduler from the repository root in separate terminals:

```powershell
uv run celery -A tasks.celery_app:celery_app worker --loglevel=info --pool=solo
```

```powershell
uv run celery -A tasks.celery_app:celery_app beat --loglevel=info
```

Beat schedules EPİAŞ collection daily at 14:10 Europe/Istanbul and weather collection every two weeks. The scheduled EPİAŞ task still needs its token manager wired into the client constructor.

## Tests

Run the Python tests from the repository root:

```powershell
uv run python -m pytest -v
```

Run the frontend checks from `frontend`:

```powershell
npm run typecheck
npm run lint
npm run build
```

GitHub Actions runs the Python suite with test configuration. Applying migrations and running an end-to-end smoke test against PostgreSQL and Redis remain separate verification steps.

## Roadmap

- Isolate weather records and simulation inputs by site.
- Verify fresh database setup and the login-to-simulation flow in CI.
- Expose transformer overload duration in daily scenario results.
- Match hourly grid energy with EPİAŞ PTF for revenue estimates.
- Compare scenarios with and without a battery.

## Author

[Emirhan Navdar](https://github.com/emirhannavdar)