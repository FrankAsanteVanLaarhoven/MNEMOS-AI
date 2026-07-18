# Mnemos

Sovereign, local-first memory + concierge orchestrator. The single source of truth is a
human-readable Markdown vault. A thin runner primes on that vault before acting, and logs
every action with evidence citations.

**Owner:** Frank Asante Van Laarhoven — frankleroyvan@gmail.com

## Provenance

Mnemos is a clean-room implementation. The "Markdown notes as external memory, read an
index before answering" method is a common practitioner pattern and is not owned by anyone;
the *idea* is free to reimplement. **No third-party source file was copied into this project,
and nothing here is derived from any CC-licensed repository.** Every file was written from a
blank page.

## Layout

- `core/`    boot config + memory pointer — read at startup, never edited by tasks
- `vault/`   the memory — INDEX, projects, jobs, daily logs, resources, archive
- `runner/`  orchestrator + specialists + integration adapters   *(P2+)*
- `voice/`   speech-to-text, text-to-speech, reactive visualizer  *(P3+)*
- `audit/`   append-only JSONL action log                         *(P2+)*

## Status

P1 (memory core) scaffolded. Full plan and phasing are kept in the local project spec.

Note: this repo is the **framework** (boot/priming convention, templates, runner scaffold).
Real memory — the actual project notes and daily logs — stays local and is gitignored, by
design. See `vault/02-projects/EXAMPLE.md` for the note template.
