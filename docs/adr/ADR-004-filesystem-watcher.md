# ADR-004: Filesystem watcher

## Status

Accepted

## Decision

Use the `watchdog` library to observe the ShareBox shared folder recursively and publish `fs_changed` events on the in-process event bus for SSE clients.

## Consequences

- Native OS watchers where available; polling fallback on some network mounts.
- Debouncing is minimal in V1; clients refresh listing on each event.
