
# GES Battery | Solar Energy Data & Simulation Project

GES Battery is a Python-based project I'm developing to bring together data collection, API management, and simulation processes for solar energy systems.

The project integrates electricity market data from EPİAŞ and weather data from Visual Crossing. It also includes an inverter simulation module, user authentication, and database operations.

My main goal is to build a structured backend that makes data from different sources accessible through a REST API and provides a foundation for calculations and simulations related to solar energy systems.

> **Project Status:** Active development. I'm continuing to improve the API architecture, simulation modules, database operations, and automated testing infrastructure.

## Table of Contents

- [Project Overview](#project-overview)
- [Technologies](#technologies)
- [Project Structure](#project-structure)
- [API and Services](#api-and-services)
- [Inverter Simulation](#inverter-simulation)
- [Authentication and Database](#authentication-and-database)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [GitHub Actions](#github-actions)
- [Development Notes](#development-notes)
- [Version History](#version-history)

## Project Overview

While developing this project, I wanted to avoid keeping API requests, business logic, database operations, and calculations in the same files.

Instead, I organized the application into separate layers. API endpoints handle incoming HTTP requests, service classes communicate with external APIs, and database operations, authentication, and simulation logic are managed independently.

The project currently focuses on the following areas:

- **EPİAŞ Integration:** Retrieving electricity market data through external API services.
- **Visual Crossing Integration:** Collecting weather and solar-related meteorological data based on geographical coordinates.
- **Inverter Simulation:** Calculating inverter power output under different environmental and operating conditions.
- **Authentication:** Managing JWT-based authentication and protected API endpoints.
- **Database:** Managing application data through SQLAlchemy and PostgreSQL.
- **Testing and CI:** Running automated tests with pytest and GitHub Actions.

The overall structure is designed to make it easier to maintain existing features and add new functionality without making unnecessary changes to unrelated parts of the project.

## Technologies

| Technology | Purpose |
| --- | --- |
| Python 3.12+ | Main programming language |
| FastAPI | REST API development |
| Pydantic | Request and response validation |
| Requests | Communication with external APIs |
| SQLAlchemy | Database access and management |
| PostgreSQL | Relational database used in development |
| PyJWT | JWT authentication |
| pwdlib / Argon2 | Password hashing |
| pytest | Automated testing |
| unittest.mock | Mocking external services and database operations |
| uv | Dependency and virtual environment management |
| GitHub Actions | Continuous Integration (CI) |

Project dependencies are managed through `pyproject.toml`, while `uv.lock` is used to keep dependency installations consistent across environments.

## Project Structure

```text
ges_battery/
├── .github/
│   └── workflows/          # GitHub Actions workflows
├── api/
│   ├── endpoints/          # API route handlers
│   ├── services/           # EPİAŞ and Visual Crossing services
│   ├── config/             # Application configuration
│   ├── errors/             # Error handling
│   └── api.py              # FastAPI application
├── auth/                   # JWT authentication
├── database/               # Database connection and operations
├── frontend/               # Frontend files
├── hash/                   # Password hashing
├── simulation/             # Inverter simulation
├── static/                 # Static files
├── tests/
│   ├── apis/               # API tests
│   └── inverter/           # Inverter tests
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

I separated these components to keep the code easier to maintain.

For example, when I need to change how an external API request is made, I can update the related service without having to rewrite the endpoint logic.

Similarly, simulation calculations can be developed and tested independently of the API layer.

## API and Services

### EPİAŞ Integration

The EPİAŞ integration is used to retrieve electricity market data.

This part of the project includes TGT token management and endpoints for querying PTF and KPTF data.

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/epias/token` | `POST` | Handles the EPİAŞ TGT token operation |
| `/api/v1/epias/PTF` | `POST` | Retrieves PTF electricity market data |
| `/api/v1/epias/KPTF` | `POST` | Retrieves KPTF electricity market data |

PTF requests use the `startDate` and `endDate` parameters, while KPTF requests use `startDate`.

Date values must follow the format expected by the EPİAŞ service.

#### Service Architecture

The EPİAŞ integration uses a dedicated service class to manage external requests.

The service layer handles:

- Creating HTTP requests.
- Preparing request headers and parameters.
- Managing authentication tokens.
- Communicating with EPİAŞ endpoints.
- Handling external service errors.
- Returning data to the API layer.

This keeps the endpoint code focused on processing incoming requests and returning responses.

### Visual Crossing Integration

The Visual Crossing integration retrieves weather data for a given location using latitude and longitude.

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/visual_crossing` | `GET` | Retrieves weather data |
| `/api/v1/visual_crossing/weather/full` | `GET` | Retrieves more detailed weather data |

Example request:

```http
GET /api/v1/visual_crossing?enlem=39.97&boylam=32.68
```

Depending on the requested data, the response can include:

- Date and time information.
- Temperature.
- Cloud coverage.
- Solar radiation.
- Solar energy.
- Hourly weather measurements.
- Additional meteorological information.

These values are useful when working with solar energy calculations, since weather conditions directly affect the amount of energy a photovoltaic system can produce.

#### Weather Data Storage

The project also includes database operations for storing weather data.

I separated the database logic from the weather service so that API communication and data persistence can be handled independently.

This separation is particularly useful during testing because database writes can be mocked without affecting the behavior being tested in an API endpoint.

### API Responses and Error Handling

I use a structured response format to keep API responses consistent.

The response structure includes fields such as:

| Field | Description |
| --- | --- |
| `success` | Indicates whether the request was successful |
| `data` | Contains the returned data |
| `timestamp` | Time associated with the response |
| `errorCode` | Error code when applicable |
| `message` | Additional information about the response |

The project also includes centralized error-handling components for application errors and external service failures.

Logging is used to make it easier to identify problems, especially when communicating with external services.

## Inverter Simulation

The `simulation/` directory contains the inverter simulation logic.

This module is responsible for calculating inverter behavior under different operating conditions.

The simulation considers conditions such as solar irradiance, temperature, power limitations, and inverter operating states.

The main scenarios covered by the tests include:

- Available power calculation.
- Zero and negative irradiance values.
- AC power limits.
- DC power calculations.
- Temperature correction factors.
- Inverter `OFF` state.
- Inverter `FAULT` state.
- Step-by-step simulation behavior.
- Minimum irradiance conditions.
- Ensuring power calculations do not unexpectedly modify stored energy state.

I wanted the simulation to handle more than just normal operating conditions.

For that reason, I also added tests for boundary values and situations where the inverter should not generate power.

### Simulation Testing

The inverter tests are located in:

```text
tests/inverter/
```

These tests help verify that changes to the simulation logic do not break previously working calculations.

The simulation module can also be tested independently of external API connections.

## Authentication and Database

### Authentication

The project uses JWT-based authentication to control access to protected API endpoints.

Authentication-related operations are handled separately from the main API services.

The authentication system uses:

- PyJWT for token operations.
- Password hashing through `pwdlib` with Argon2 support.
- FastAPI dependencies for checking authenticated users.
- Protected endpoints that require authentication.

The goal is to keep authentication logic reusable across different API routes.

### Database

Database operations are handled through SQLAlchemy.

I use PostgreSQL in my local development environment.

The database layer is responsible for managing connections and handling application data.

Database connection settings are read from environment variables instead of being hardcoded directly into the source code.

This makes it easier to use different configurations for development and testing.

### Security Considerations

Sensitive configuration values should never be committed to the repository.

These include:

- API keys.
- Database credentials.
- JWT secret keys.
- External service usernames and passwords.

Each environment should use its own configuration values.

## Installation

### Requirements

Before running the project, make sure the following tools are available:

- Python 3.12 or newer.
- Git.
- uv.
- PostgreSQL for features that require database access.
- Valid credentials for external services when making real API requests.

### 1. Clone the Repository

```bash
git clone https://github.com/emirhannavdar/ges_battery.git
cd ges_battery
```

### 2. Install Dependencies

The project uses `uv` for dependency management.

Install the dependencies with:

```bash
uv sync --frozen
```

This installs the dependencies according to the existing `uv.lock` file.

### 3. Configure the Environment

Create a `.env` file in the project root directory and configure the required environment variables.

The application needs valid configuration values for external APIs, authentication, and database access.

## Environment Variables

The following variables are used in the project configuration:

```dotenv
_VISUAL_CROSSING_API_KEY=your-visual-crossing-api-key
_VISUAL_CROSSING_BASE_URI=your-visual-crossing-base-url

_EPIAS_BASE_URI=your-epias-base-url
_TGT_URL=your-tgt-endpoint
_PTF_ENDPOINT=your-ptf-endpoint
_KPTF_ENDPOINT=your-kptf-endpoint

_EPIAS_USERNAME=your-epias-username
_EPIAS_PASSWORD=your-epias-password

_HASH_PASSWORD=your-hash-configuration
_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/database_name
_SECRET_KEY=your-long-random-secret-key
```

These are example values and must be replaced with the correct configuration for the environment.

The database connection string must use a driver supported by the installed project dependencies.

The `.env` loading method must also match the application's configuration code.

**Important:** Do not commit the `.env` file or any real credentials to GitHub.

## Running the Application

After installing the dependencies and configuring the environment, start the FastAPI application:

```bash
uv run uvicorn api.api:app --reload --host 127.0.0.1 --port 8001
```

The API will be available at:

```text
http://127.0.0.1:8001
```

### API Documentation

FastAPI provides interactive API documentation.

Swagger UI:

```text
http://127.0.0.1:8001/docs
```

ReDoc:

```text
http://127.0.0.1:8001/redoc
```

These pages can be used to inspect endpoints, review request parameters, and test API requests.

If the `uvicorn` command is unavailable, check whether the package is installed in the project environment.

## Testing

I use pytest to test the API endpoints and inverter simulation logic.

The tests are organized into separate directories:

```text
tests/
├── apis/
│   ├── conftest.py
│   ├── test_epias.py
│   └── test_visual_crossing.py
└── inverter/
    ├── test_inverter_calculate_available_power.py
    └── test_inverter_step.py
```

### Running All Tests

```bash
uv run python -m pytest -v
```

### Running API Tests

```bash
uv run python -m pytest tests/apis -v
```

### Running Inverter Tests

```bash
uv run python -m pytest tests/inverter -v
```

### API Testing Approach

For API tests, I use `MagicMock`, `patch`, and FastAPI's `dependency_overrides` mechanism.

This allows me to test endpoint behavior without making real requests to external services.

For example, when testing the Visual Crossing endpoint, I can replace the actual weather service with a mock object that returns predefined weather data.

Database write operations can also be mocked when they are outside the scope of the test.

This makes the tests more predictable and avoids depending on external API availability.

### Test Coverage

During the `v1.1.0` development process, the project reached **27 passing automated tests**.

| Module | Tests | Main Scenarios |
| --- | ---: | --- |
| EPİAŞ API | 7 | Authentication, missing parameters, successful requests |
| Visual Crossing API | 6 | Authentication, validation, weather responses |
| Inverter simulation | 14 | Power calculations, operating states, boundary conditions |
| **Total** | **27** | |

The GitHub Actions test workflow was also successfully completed.

Passing tests do not mean that every possible application behavior has been covered. I plan to expand the test suite as the project grows.

## GitHub Actions

I added GitHub Actions to automate the testing process.

The workflow is stored in:

```text
.github/workflows/tests.yml
```

It runs automatically for the configured `push` and `pull_request` events.

### CI Workflow

The workflow performs the following steps:

1. Checks out the repository.
2. Sets up the Python environment.
3. Installs `uv`.
4. Installs project dependencies using the lockfile.
5. Configures test environment variables.
6. Runs the pytest test suite.

The main test command is:

```bash
uv run python -m pytest -v
```

### Why I Added CI

Before adding GitHub Actions, I was running tests locally to check whether changes had broken existing functionality.

With CI, tests also run automatically in a clean environment when the configured GitHub events occur.

This helps catch issues such as missing dependencies, import errors, and differences between local and CI environments.

The workflow does not modify application code automatically. It only runs the configured checks.

GitHub Actions results can be viewed here:

[View GitHub Actions](https://github.com/emirhannavdar/ges_battery/actions)

## Development Notes

While working on this project, I've been focusing on improving both the application structure and the development process.

Some of the main things I've worked on are:

1. Separating endpoint handlers from service logic.
2. Organizing external API requests into reusable classes.
3. Handling application and external service errors consistently.
4. Moving sensitive configuration values into environment variables.
5. Managing database connections and persistence separately.
6. Adding unit tests for inverter calculations.
7. Testing API endpoints with mocked dependencies.
8. Setting up automated testing through GitHub Actions.

There are still several areas I want to improve.

### Planned Improvements

- Expand authentication and authorization tests.
- Add more database integration tests using an isolated test database.
- Measure test coverage.
- Improve API documentation.
- Add more simulation scenarios.
- Continue refactoring the project as new features are added.

I'm treating this project as an ongoing development process, so the structure and functionality may change as I improve different parts of the system.

## Version History

### v1.1.0 — Automated Testing & CI Integration

This release focuses on improving test reliability and automating the testing process.

Main changes:

- Added automated API tests.
- Added inverter simulation tests.
- Integrated GitHub Actions CI.
- Improved dependency management.
- Added mock-based testing for external services.
- Fixed test environment configuration issues.
- Verified the automated test workflow.

Previous releases and version details are available on the GitHub Releases page:

[View Releases](https://github.com/emirhannavdar/ges_battery/releases)

---

This project is still under development. I'll continue updating the code, tests, and documentation as I add new features and improve the existing implementation.
