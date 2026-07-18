# Mnemos voice (P3)

A push-to-talk loop over the same runner as the text CLI: **listen → route → prime → run
→ speak**. Routing, priming, evidence citation, and the high-stakes approval gate all
carry over unchanged. Approval is spoken — a high-stakes action proceeds only on a "yes".

## Run

    python -m voice          # push-to-talk-by-typing (text backends, offline stub model)

Type a request; say `exit` (or type it) to end. With no model configured it uses the
offline stub, so the loop works with zero setup.

## Backends

All three layers are swappable and default to something that runs with no hardware:

- **Model** — `MNEMOS_MODEL_*` (default `stub`; set `http` for the local runtime on the 4080).
- **Speech-to-text** (`stt.py`) — `TextSTT` (default, typed input) or `CommandSTT`, which
  shells out to any local ASR CLI named in `MNEMOS_STT_CMD` (receives a wav path).
- **Text-to-speech** (`tts.py`) — `TextTTS` (default, prints) or `CommandTTS`, which pipes
  text to any local TTS CLI named in `MNEMOS_TTS_CMD`.

Mnemos declares no specific audio engine — you point the command backends at whatever
local ASR/TTS you run. The command backends are wiring only and are not covered by tests.

## Personas & voice

Each specialist can declare an assistant `persona` — a display name and a `voice`
(`male` / `female` / `neutral`). When a specialist acts, the loop announces it ("This is
Vera.") and asks the TTS backend to use that voice; `CommandTTS` passes the choice to your
engine as the `MNEMOS_TTS_VOICE` environment variable, so your wrapper can select a male or
female voice.

A persona is an **assistant identity, not an impersonation of a specific real person**. It
self-identifies as an assistant and must not be used to make a third party believe they are
speaking to a particular real human.

## Test

    python -m pytest voice/tests -q      # or: python voice/tests/test_voice.py
