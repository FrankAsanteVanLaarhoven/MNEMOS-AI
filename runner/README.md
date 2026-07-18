# Mnemos runner (P2)

Thin master orchestrator: **prime → route → run specialist → audit**. Deterministic,
inspectable, model-agnostic.

## Flow

1. **Route** — `router.py` picks a specialist by whole-word trigger match (no model call).
   A tie or no match returns nothing, so the caller asks which specialist to use.
2. **Prime** — `orchestrator.py` reads `core/boot.md` + `vault/INDEX.md` + the specialist's
   job note (+ any `--note` project note), and records those paths as evidence.
3. **Run** — the primed context goes to a `ModelBackend`. High-stakes specialists are
   blocked until approved.
4. **Audit** — every action appends one JSONL line to `audit/` (gitignored, local only).

## Model backends (`model.py`)

Set `MNEMOS_MODEL_BACKEND`:

- `stub` (default) — offline, deterministic. Runs and tests with no model or network.
- `http` — any chat-completions HTTP endpoint (a `/chat/completions` route taking
  `{"messages": [...]}`). Point it at a local runtime on the RTX 4080, or a hosted gateway:

      MNEMOS_MODEL_BACKEND=http
      MNEMOS_MODEL_BASE_URL=http://localhost:11434/v1
      MNEMOS_MODEL_NAME=<model-id>
      MNEMOS_MODEL_API_KEY=<optional, hosted only>

## Use

    python -m runner.cli --list
    python -m runner.cli "scan the status of a project" --note vault/02-projects/EXAMPLE.md
    python -m runner.cli "write a checkpoint"            # prompts for approval (high-stakes)

## Specialists (`specialists/*.json`)

One JSON file per specialist: `name`, `job` (path to a priming note), `triggers`,
`high_stakes`, `description`. Add a specialist by dropping in a new file — no code change.

An optional `action` names a vault side-effect: after the model produces its text, the
action persists it. `write-checkpoint` appends the result to today's daily log (and leaves
a dated pointer in a `--note` project note). Actions are appends only, run **after** the
high-stakes approval gate, and their written paths are recorded in the audit trail.

## Test

    python -m pytest runner/tests -q      # or: python runner/tests/test_runner.py
