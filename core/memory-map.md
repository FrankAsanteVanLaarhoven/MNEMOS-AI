# Memory map

The single source of truth is the vault. Start here:

    vault/INDEX.md

Everything Mnemos knows is a Markdown file under `vault/`. Nothing is remembered that is
not written there. `core/` (this pointer and `boot.md`) is read at startup and is never
edited by a task.
