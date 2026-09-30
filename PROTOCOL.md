# Urja Meter Ops — Reverse-Engineered Protocol

## Scope

The portal was investigated through normal browser usage and Chrome DevTools Network inspection. It was treated as read-only.

## Authentication

The logged-in browser uses an `auth.session_token` session cookie. The implementation does not hard-code credentials or cookies. A fresh session token is supplied through the `URJA_SESSION_TOKEN` environment variable.

The session token must never be committed to GitHub or included in logs.

## Confirmed upstream requests

### Meter search

```http
GET /portal/meters/search?q={query}&page={page}
```

Example:

```http
GET /portal/meters/search?q=J100001&page=1
```

Observed response shape:

```json
{
  "data": [
    {
      "meterId": "J100001",
      "serialNo": "GE84132",
      "make": "L&T",
      "phaseType": "single",
      "installStatus": "Installed",
      "dtCode": "DT-002"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 20
}
```

### Energy

```http
GET /portal/meters/{meter_id}/energy
```

Example:

```http
GET /portal/meters/J100001/energy
```

The response contains consumption readings with:

- `timestamp`
- `kwh`
- `kvah`
- `voltR`

Observed readings were at 30-minute intervals. The portal represents numeric measurements as strings; the clean API converts them to JSON numbers.

### Geo

```http
GET /portal/meters/{meter_id}/geo
```

Example:

```http
GET /portal/meters/J100001/geo
```

Observed response:

```json
{
  "data": {
    "latitude": "26.822136543835608",
    "longitude": "75.90718190602279"
  }
}
```

## Browser page

The meter detail page is:

```text
/meters/{meter_id}
```

The page displays nameplate information, location, network hierarchy, and consumption. The nameplate/network data did not appear as a separate Fetch/XHR request in the observed Network view; the page is a SvelteKit application and some page data is delivered through its SvelteKit data loading.

## Network hierarchy observed for J100001

```text
Jaipur Zone 2 (Z-02)
  -> Circle 2 (C-02)
  -> Division 2 (D-02)
  -> Subdivision 2 (SD-02)
  -> Substation 2 (SS-02)
  -> Feeder 2 (F-002)
  -> Mansarovar DT 2 (DT-002)
  -> Meter J100001
```

## Quirks and decisions

1. Portal field names are abbreviated/camelCase (`meterId`, `serialNo`, `phaseType`).
2. The public API normalizes these to clearer snake_case names.
3. Energy numeric values are converted from strings to numbers.
4. The upstream session is treated as an external dependency and is not persisted.
5. A 10-second upstream timeout is used to avoid hanging API requests.
6. Upstream authentication failures are translated into a stable API error rather than exposing portal internals.
