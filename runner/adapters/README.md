# Mnemos channel adapters

A governed way for Mnemos to **deliver** something to a channel. Every delivery goes
through the same **risk/authority gate** as a specialist (0–6), plus two hard rules for
channels that reach other people.

## The two rules for third-party channels

1. **Disclosure is mandatory.** A `third_party` adapter must carry an AI-disclosure line,
   prepended to the payload. Mnemos never reaches out while pretending to be a person; an
   adapter marked third-party with no disclosure is refused.
2. **Never autonomous.** A third-party delivery needs approval (`--yes`), and a
   professional sign-off (`--signoff`) at risk 5. Risk 6 is prohibited.

## Shipped adapters (local only)

| Adapter | Risk | Third-party | What it does |
|---|---|---|---|
| `note`   | 2 | no  | appends a line to `outbox/notes.md` (local) |
| `email`  | 3 | yes | writes a **draft** to `outbox/email-*.md`, disclosure prepended, for you to review and send yourself — **it does not send** |
| `notion` | 2 | no  | drafts a page body to `outbox/notion-*.md`, targeting `MNEMOS_NOTION_ACCOUNT` — **does not post** |
| `slack`  | 3 | yes | drafts a message to `outbox/slack-*.md`, targeting `MNEMOS_SLACK_ACCOUNT`, disclosure prepended — **does not post** |
| `gmail`  | 3 | yes | drafts an email to `outbox/gmail-*.md`, targeting `MNEMOS_GMAIL_ACCOUNT`, disclosure prepended — **does not send** |

The `notion`/`slack`/`gmail` adapters are **draft-only**: they prepare content addressed to
the account named in `MNEMOS_<CHANNEL>_ACCOUNT` (set locally, never committed) and never
call an external API. **Live delivery needs that channel's API token** (Notion integration
secret, a Slack access token, a Gmail credential) and is built once a real token is available
against. Account identifiers and tokens live only in your gitignored `.env`.

## Deliberately NOT here

No telephony, SMS, WhatsApp, or social adapter. Automated calling/texting of third parties
is regulated (TCPA / GDPR / PECR), and an AI answering or placing calls without disclosure
is deceptive. This framework is the **guardrail** — disclosure + approval + audit — not a
dialer. If you add a channel that contacts real people, you own the carrier agreements,
per-recipient consent, and regional legality; the framework will still force disclosure and
approval on it.

## Use

    python -m runner.cli --list-adapters
    python -m runner.cli --send note  "a local reminder"
    python -m runner.cli --send email "Dear client, ..." --yes   # writes a disclosed draft
