# Job: governance-scan

**Purpose:** run a standing review over a governed project and report its status honestly.

**Prime on:** this note + the target's `vault/02-projects/` note.

## Steps

1. Read the target project note; record its stated state and its "next".
2. Check the actual repo against the note — tests, last commit, open blockers.
3. Report three things: what is true, what has drifted from the note, and the next decision.
4. Persist: update the project note's **State**; append one `01-daily/` action citing sources.

## Output contract

- No "superior" / "certifiable" / "surpasses" language.
- Every status line cites a file or a command's output.
- If a check was skipped, say so — do not imply full coverage.

## Approval

Read-only by default. Any fix, commit, or publish is a **high-stakes action**: confirm first,
then write an `audit/` entry (boot rules 5–6).
