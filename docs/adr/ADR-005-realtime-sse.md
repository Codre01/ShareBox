# ADR-005: Real-time browser updates

## Status

Accepted

## Decision

Use Server-Sent Events (`GET /api/v1/events`) authenticated via Bearer token over a fetch stream (because EventSource cannot set Authorization headers).

## Consequences

- Works with existing HTTP stack; simpler than WebSockets for one-way notifications.
- Mobile browsers must keep the tab active for the stream; listing still refreshes on navigation.
