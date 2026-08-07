# ADR-002: Browser credential persistence

## Status

Accepted

## Context

Trusted devices must reconnect without re-pairing (spec §33, §82). Credentials must survive browser restarts and must not depend on IP address.

## Decision

Issue each trusted device a high-entropy **device token** (opaque secret) stored:

- **Server**: hashed (SHA-256) in SQLite trusted-device records.
- **Browser**: `localStorage` key `sharebox.deviceToken` plus `sharebox.deviceId`.

Authenticate with `Authorization: Bearer <token>` (and a matching HttpOnly cookie set for same-origin convenience).

## Alternatives considered

- Cookies only: harder for SSE/download links on some mobile browsers.
- IndexedDB: unnecessary complexity for a single secret.

## Consequences

- Clearing site data requires re-pairing.
- Token theft on a compromised device equals device impersonation until revoked.
