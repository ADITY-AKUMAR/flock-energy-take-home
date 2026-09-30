# Reflection

## What assumptions did you make?

I assumed the Urja portal is the source of truth and that the new service should remain read-only. I also assumed the browser session cookie is an acceptable short-lived authentication mechanism for this take-home, while keeping the token outside source control.

## Which part was most difficult, and how did you get unstuck?

The difficult part was understanding the portal without API documentation. I used Chrome DevTools Network inspection while performing normal user actions. That revealed the meter search, energy, and geo requests and their response shapes.

## If you had another day, what would you improve?

I would automate login/session bootstrap, add richer contract tests against recorded upstream responses, add retry/backoff for transient upstream failures, and investigate the SvelteKit page-data path for the full meter nameplate/network object.

## What mistake did you make?

I initially assumed the visible meter page would have one obvious REST endpoint containing all data. Network inspection showed that the page combines page data with separate `energy` and `geo` requests.

## If reviewing your own submission, what would you criticise?

The session-token bootstrap is intentionally simple and requires an externally obtained session token. For production, I would implement a proper login/session lifecycle and refresh strategy. I would also add more extensive tests around upstream failures and schema changes.
