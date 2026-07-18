# Evidence-citation format

Every non-trivial Mnemos output cites what it used, by path, so any claim is checkable.

**Inline:**

> …the batch was rejected (see `vault/02-projects/example-project.md`, detectors section).

**List form, at the end of an output:**

    Evidence:
    - vault/02-projects/example-project.md — current release + test status
    - audit/2026-07-18.jsonl:42 — approval recorded for the send action

## Rules

- Cite the vault note or file, not memory.
- If a claim has no citable source, mark it **unverified** rather than asserting it.
- A high-stakes action must also have an `audit/` entry, and that entry is cited too.
