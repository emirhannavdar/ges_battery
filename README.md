# GES Battery

**Solar energy data integration, inverter simulation and monitoring-oriented software**

GES Battery is an actively developed full-stack project that combines electricity market prices, meteorological data and a stateful photovoltaic (PV) simulation engine. Its backend is built with FastAPI and PostgreSQL; a Next.js interface provides workflows for running and comparing daily simulations.

> **Status:** Active development / prototype. The repository is not yet a production-ready SCADA or battery-management system. Calculated values are simulation outputs, not measurements from physical equipment. Some authentication, background-task and multi-site workflows still require hardening; see [Known limitations](#known-limitations-and-roadmap).

## Features

- **EPİAŞ integration:** TGT-based authentication and PTF/KPTF electricity market data retrieval; PTF data persistence.
- **Visual Crossing integration:** Weather data retrieval using latitude/longitude and database persistence.
- **PV inverter simulation:** Irradiance- and temperature-dependent output, AC/DC limits, inverter state and injected fault scenarios.
- **Power system components:** Energy analyzer, transformer and energy quality controller (EKK), including active-power limitation, reactive-power control and curtailment calculations.
- **Stateful simulation sessions:** UUID-based sessions associated with an authenticated user; state serialization to PostgreSQL and row-level locking during updates.
- **Daily simulation and comparison:** Run a 24-hour scenario, store hourly results, review previous runs and compare grid-energy outputs.
- **Authentication and authorization:** JWT access/refresh tokens, password hashing and role-based access (`admin`, `operator`, `viewer`).
- **Scheduled data collection:** Celery workers and Redis broker for EPİAŞ and weather ingestion tasks.
- **Web interface:** Next.js dashboard for daily simulation, history, comparison and results.

## Technology stack

| Layer | Technologies |
| --- | --- |
| Backend | Python 3.12+, FastAPI, Pydantic, Requests |
| Persistence | PostgreSQL, SQLAlchemy, SQL queries |
| Authentication | PyJWT (HS512), pwdlib/Argon2, role dependencies |
| Cache and jobs | Redis, Celery, Celery Beat |
| Simulation | Python-based inverter, analyzer, transformer and EKK models |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4, ECharts, Zod |
| Tooling | uv, pytest, GitHub Actions, npm |

## Architecture

```text
                    +-----------------------+
                    | Next.js web dashboard |
                    +-----------+-----------+
                                |
                                | HTTP / cookie-based session proxy
                                v
                    +-----------------------+
                    | FastAPI REST backend  |
                    +-----------+-----------+
                                |
             +------------------+------------------+
             |                  |                  |
             v                  v                  v
       Auth / RBAC        External APIs      Simulation API
       JWT tokens         EPİAŞ / Weather    UUID sessions
             |                  |                  |
             +------------------+------------------+
                                |
                                v
                          PostgreSQL
                    users / weather / prices
                    simulation state / results

        Celery Beat --> Redis broker --> Celery workers
                                         |          |
                                         v          v
                                       EPİAŞ     Weather
```

The simulation engine is implemented separately from the HTTP layer. The API loads session state, runs the appropriate simulation operation and persists the updated state.

## Repository layout

```text
.
├── .github/workflows/       # GitHub Actions
├── api/
│   ├── api.py               # FastAPI application and router registration
│   ├── config/              # Configuration and logging
│   ├── endpoints/           # EPİAŞ, weather and simulation routes
│   ├── errors/              # Application errors and handlers
│   ├── response/            # API response models
│   └── services/            # External API clients and token management
├── auth/                    # JWT, authentication endpoints and RBAC
├── database/                # SQLAlchemy connection and repositories
├── frontend/                # Next.js application
├── hash/                    # Password hashing
├── simulation/              # Inverter, analyzer, transformer, EKK, clock
├── tasks/                   # Celery application and collection tasks
├── tests/                   # API and simulation tests
├── pyproject.toml
├── uv.lock
└── README.md
```

## API overview

All routes below are relative to the FastAPI server. Authentication is required for protected endpoints; access also depends on the user's role.

### Authentication

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/auth/token` | Log in and receive access/refresh tokens |
| `POST` | `/auth/refresh-access-token` | Obtain a new access token from a refresh token |
| `POST` | `/auth/sign` | Register a user (admin role required) |
| `GET` | `/auth/users/me` | Read the authenticated user's profile |

### External data

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/epias/token` | Request EPİAŞ TGT (currently returns raw token; see limitations) |
| `POST` | `/api/v1/epias/PTF` | Retrieve and persist PTF data |
| `POST` | `/api/v1/epias/KPTF` | Retrieve KPTF data |
| `GET` | `/api/v1/visual_crossing` | Retrieve and store weather data |
| `GET` | `/api/v1/visual_crossing/weather/full` | Retrieve detailed weather data |

### Stateful inverter sessions

These endpoints use a **UUID** `simulation_id`, and session operations are restricted to the owning user.

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/inverter/sessions` | Create a session |
| `GET` | `/inverter/sessions/{simulation_id}` | Read session metadata |
| `POST` | `/inverter/sessions/{simulation_id}/start` | Start a created session |
| `POST` | `/inverter/sessions/{simulation_id}/step` | Advance the simulation using stored weather data |
| `POST` | `/inverter/sessions/{simulation_id}/reset` | Reset the session |
| `POST` | `/inverter/sessions/{simulation_id}/fault` | Inject an inverter fault |
| `POST` | `/inverter/sessions/{simulation_id}/fault/reset/{inverter_id}` | Clear an inverter fault |
| `GET` | `/inverter/sessions/{simulation_id}/data` | Retrieve inverter data |

Create a session with:

```http
POST /inverter/sessions
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json

{"inverter_count": 3}
```

A successful creation returns `201 Created` and a `simulation_id`. Use that UUID in subsequent session requests. For a step request, the body includes `hangi_gun`, `saat_kac` and `dt_seconds`:

```json
{
  "hangi_gun": "2026-11-23",
  "saat_kac": "11:00:00",
  "dt_seconds": 3600
}
```

The requested weather record must exist in the database. The session must be started before it can be stepped forward.

### Daily simulations and saved history

The **daily history ID is an integer**, distinct from the UUID used for stateful sessions.

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/inverter/daily` | Run and persist a daily scenario |
| `GET` | `/inverter/simulations` | List the current user's saved daily runs |
| `GET` | `/inverter/simulations/{simulation_id}` | Get a saved daily run by integer ID |
| `GET` | `/inverter/simulations/compare` | Compare two saved daily runs |

Example daily request:

```json
{
  "simulation_date": "2026-11-23",
  "inverter_count": 3,
  "inverter_ac_rated_kw": 900,
  "inverter_dc_rated_kw": 1000,
  "ekk_active_power_limit_kw": 800
}
```

A daily simulation requires a complete set of 24 hourly weather records for the requested date. To compare two saved runs, call:

```http
GET /inverter/simulations/compare?simulation_id_1=1&simulation_id_2=2
Authorization: Bearer <ACCESS_TOKEN>
```

## Local development

### Requirements

- Python 3.12 or newer and [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- Redis (for token caching and Celery)
- Node.js and npm (for the frontend)
- EPİAŞ and Visual Crossing credentials for real external API calls

### 1. Clone and install backend dependencies

```powershell
git clone https://github.com/emirhannavdar/ges_battery.git
cd ges_battery
uv sync --frozen
```

### 2. Configure environment variables

Create a `.env` file in the project root. Use your own credentials and connection details:

```dotenv
_DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@127.0.0.1:5432/DATABASE
_REDIS_URL=redis://127.0.0.1:6379/0

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

**Important:** The database URL is an example, not a provisioned database. The repository does not currently provide a complete schema migration/bootstrap process. Create the required PostgreSQL tables (`users`, `weather_data`, `simulation_sessions`, daily simulation tables and EPİAŞ price tables) according to the application SQL before using database-backed endpoints. Ensure the appropriate PostgreSQL driver is installed for your chosen URL; add it to project dependencies if needed.

Do not commit `.env`, credentials, signing secrets or actual tokens to Git.

### 3. Start the backend

```powershell
uv run uvicorn api.api:app --reload --host 127.0.0.1 --port 8000
```

API documentation: `http://127.0.0.1:8000/docs`

### 4. Start the frontend

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

The frontend's default `BACKEND_URL` is `http://127.0.0.1:8000`. The local web app is available at `http://localhost:3000`.

Optional frontend checks:

```powershell
npm run typecheck
npm run lint
npm run build
```

### 5. Run background workers (optional)

Start Redis and run Celery worker and scheduler in separate terminals:

```powershell
uv run celery -A tasks.celery_app:celery_app worker --loglevel=info --pool=solo
```

```powershell
uv run celery -A tasks.celery_app:celery_app beat --loglevel=info
```

The current Beat configuration schedules EPİAŞ collection daily at **14:10 Europe/Istanbul** and weather collection every **two weeks**. The EPİAŞ task currently needs its `OOP_Epias` token-manager dependency fixed before it can run successfully.

## Testing and CI

Run the Python test suite:

```powershell
uv run python -m pytest -v
```

Run only the inverter-related tests:

```powershell
uv run python -m pytest tests/inverter -v
```

GitHub Actions executes pytest on pushes and pull requests targeting `main`. Its current test environment uses mock credentials and a placeholder Redis URL; it does **not** provision a real PostgreSQL/Redis integration environment. Passing unit tests should not be treated as proof that the production database and background workers are configured correctly.

## Security model

- Protected API routes use bearer-token authentication and role dependencies.
- Access tokens expire after **15 minutes**; refresh tokens after **7 days**.
- JWT verification checks signature, issuer, audience, expiration, required claims and token type.
- Passwords are verified through the project's password hashing layer.
- The Next.js server stores the access token in an HTTP-only session cookie.

**Current limitations:** Token `jti` values are generated but are not yet enforced as a revocation/rotation mechanism. The frontend logout clears the cookie without server-side token revocation. Refresh-token replay protection and login rate limiting should be implemented before production use. The frontend cookie lifetime is currently 30 minutes, longer than the 15-minute access-token lifetime.

## Known limitations and roadmap

The following are known development items, not completed capabilities:

1. **Celery EPİAŞ collection:** Pass a valid token manager to `OOP_Epias` and align the scheduled task with the API token flow.
2. **Token lifecycle:** Add refresh-token rotation, `jti` verification, revocation, account-disabled checks and a server-side logout mechanism.
3. **Multi-site weather data:** Bind coordinates to actual locations and filter simulation weather queries by `location_id`; the current weather ingestion uses `location_id=1`.
4. **Database migrations:** Add Alembic and documented schema creation/update steps.
5. **EPİAŞ token exposure:** Stop returning the raw TGT value from the public API response.
6. **Frontend session integration:** Extend the frontend API proxy and UI to use the new UUID-based session routes if interactive session management is required.
7. **Infrastructure checks:** Add realistic PostgreSQL/Redis integration checks, deployment configuration and monitoring.
8. **Configuration validation:** Fail clearly on missing or invalid environment settings; remove obsolete token helper methods.
9. **Simulation validation:** Calibrate physical models and controller behavior against measured field data before making operational decisions from simulation outputs.

## Project scope

GES Battery is a software and simulation project for learning, experimentation and future energy-monitoring integrations. It does not currently claim to be a certified inverter controller, production SCADA system or battery digital twin. Integrating real field telemetry and equipment-specific protocols requires additional validation and engineering.

## Author

Developed by [Emirhan Navdar](https://github.com/emirhannavdar).

Repository: [github.com/emirhannavdar/ges_battery](https://github.com/emirhannavdar/ges_battery)
