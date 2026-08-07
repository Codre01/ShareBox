# ADR-003: Local transport security

## Status

Accepted (V1)

## Context

Spec §93 allows HTTP on the LAN for V1 while requiring accurate documentation of the limitation. Browsers must not be instructed to bypass certificate warnings.

## Decision

V1 ships **HTTP** bound to local network interfaces with:

- pairing tokens that expire and are single-use;
- high-entropy trusted-device credentials;
- server-side authorization on every file API;
- strict filesystem root boundary checks.

Local HTTPS (private CA / trust-on-first-use) is deferred to a post-V1 investigation.

## Consequences

- LAN observers can see traffic content.
- Product docs and README must state this clearly.
- Architecture keeps TLS termination pluggable for a later ADR.
