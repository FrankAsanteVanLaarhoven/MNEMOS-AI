# Mnemos security

## Threat model (be honest about what this is)

Mnemos is a **single-user, local-first tool**. It runs on Frank's own machine, under
Frank's own account, and listens on **nothing public** — the only server, the visualizer,
binds `127.0.0.1`. The real security perimeter is therefore the operating system and disk:
full-disk encryption, account login, and not pasting secrets where they don't belong. This
module covers the few things Mnemos itself can meaningfully own.

## In scope (built + tested)

- **Secret hygiene** (`secrets.py`) — secrets come from the environment or the OS keyring,
  never from tracked files (`.env` is gitignored). `redact()` scrubs secret-looking values
  and bearer tokens out of anything written to the audit log.
- **No secrets in logs** — the audit trail runs `output_preview` through `redact()`.
- **Input validation** (`validate.py`) — size cap + control-character stripping, so junk
  can't be injected into the audit trail.
- **Local budget guard** (`limits.py`) — a sliding-window request cap and a cumulative
  token budget with a warn threshold and a hard stop, so a runaway loop can't blow your
  token/cost budget. Configured by `MNEMOS_MAX_PER_MIN` and `MNEMOS_TOKEN_BUDGET`.
- **Localhost-only binding** — the visualizer server binds `127.0.0.1`; audit logs and real
  notes are gitignored.

## Deliberately out of scope (and why)

The following were proposed but are **controls for a multi-tenant, public, internet-facing
service** — not a single-user local tool. Adding them here would increase attack surface and
maintenance for **no benefit**, and would contradict Mnemos being sovereign and local-first:

- Kubernetes / Docker Swarm autoscaling, load balancers, "10× load", circuit breakers
- Redis / Postgres / Supabase / PGVector as required infrastructure
- WAF, fail2ban, DDoS mitigation, per-IP internet rate limiting
- mTLS between services, VPC-style network isolation
- Prometheus / Grafana threat dashboards
- MFA / biometric auth, HashiCorp Vault
- "military-grade" / formal-certification claims

**Revisit only if Mnemos ever becomes a hosted, multi-user, network-exposed service.** Until
then, the OS is the perimeter and the list above is net-negative.
