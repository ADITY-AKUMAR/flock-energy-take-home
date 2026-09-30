# Urja Meter API

A small FastAPI service that exposes a clean API over the legacy **Urja Meter Ops** portal.

The portal is treated as read-only. The service hides portal-specific URL and field naming from API consumers.

## Architecture

```text
Client
  |
  v
FastAPI
  |
  v
Portal adapter
  |
  v
Urja Meter Ops
```

The first version intentionally stays small: it provides meter search, energy readings, location, and health.

## API

### Search meters

```bash
curl "http://127.0.0.1:8000/api/v1/meters?q=J100001&page=1"
```

### Meter details

```bash
curl "http://127.0.0.1:8000/api/v1/meters/J100001"
```

### Energy

```bash
curl "http://127.0.0.1:8000/api/v1/meters/J100001/energy"
```

### Location

```bash
curl "http://127.0.0.1:8000/api/v1/meters/J100001/location"
```

### Health

```bash
curl "http://127.0.0.1:8000/health"
```

FastAPI also exposes interactive Swagger documentation at `/docs` and the generated OpenAPI document at `/openapi.json`. FastAPI generates these automatically from the application routes and models. 

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and provide a fresh `URJA_SESSION_TOKEN`.

Do not commit `.env`.

Run:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Design decisions and trade-offs

### FastAPI

FastAPI was chosen because it provides typed request/response validation and automatic OpenAPI/Swagger documentation with minimal code.

### No database

The assignment is an API facade over a legacy portal. A database would introduce another source of truth and is unnecessary for the core task.

### No aggressive caching

Freshness requirements were not specified, so the first version does not cache upstream data.

### Upstream timeout

Requests use a bounded timeout so a slow legacy portal cannot hold an API request indefinitely.

### Normalization

Legacy fields such as `meterId`, `serialNo`, `phaseType`, and `installStatus` are converted into clearer API fields such as `meter_id`, `serial_number`, `phase_type`, and `installation_status`.

## Intentionally skipped

- Full network hierarchy API
- Cross-meter local search/index
- Persistent cache
- Automated session refresh
- Modern frontend
- Bulk data ingestion

These are reasonable follow-up improvements but were intentionally left out to keep the core implementation focused.

## Assumptions

See `PROTOCOL.md` for the observed upstream behavior.

## Protocol

See `PROTOCOL.md`.

## OpenAPI

The application generates `/openapi.json`. A copy can be produced with:

```bash
curl http://127.0.0.1:8000/openapi.json > openapi.json
```

## Reflection

See `REFLECTION.md`.

## Tests

```bash
pytest
```
