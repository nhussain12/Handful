# Handful — consolidated app

Hands-free voice cooking assistant. This `backend/` folder is the **single runnable app**:
a FastAPI server that runs the voice/AI agent **and** serves the polished frontend, so
the whole experience lives at one URL.

It merges the three hackathon repos:

- **Frontend** (the "DC" notecard UI) — served from `handful/static/index.html`
  (ported from `Handful/handful_frontend_uncompressed/`).
- **Voice + recipe backend** — the FastAPI / Deepgram agent (from `ucb_aihack_greg`).
- **Recipe/cards data model** — informed the frontend deck (from `pav_aihacks`).

## Run it

```bash
cd backend
cp .env.example .env          # then put your Deepgram key in it:
echo "DEEPGRAM_API_KEY=sk_..." > .env
uv sync                       # installs deps (fetches Python 3.13 if needed)
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in Chrome, click **Get Started**, allow the microphone,
and say **"Chef, …"**.

> Wake word + speech-to-text run **in the browser** (Web Speech API), which then sends
> the text to the agent. The agent (Deepgram + GPT-4o-mini) thinks, speaks back as audio,
> and calls functions that drive the screen. Use **Chrome** — Web Speech is most reliable there.

No key? The page still works as a **standalone demo**: if the agent doesn't become ready
within a few seconds, the kitchen screen replays a canned ingredient/recipe sequence so you
can click through the whole flow offline.

## How the pieces talk

Browser `/converse` WebSocket ⇄ Deepgram agent. The frontend reacts to these server messages
(`backend/handful/static/index.html` → `handleServer`):

| Server message / function call        | Frontend effect                                  |
|----------------------------------------|--------------------------------------------------|
| `set_available_ingredients`            | chips on the "What's in your kitchen?" screen     |
| `suggest_recipes`                      | the 2–3 recipe option cards                        |
| `set_recipe` + `recipe_update`         | builds the notecard deck (overview + step cards)  |
| `advance_step` / `go_to_step` / `get_current_step` | moves the deck to that step           |
| `substitute_ingredient`                | swap toast + updated ingredient in the deck       |
| `timer_update` / `timer_finished`      | the floating timer overlay                        |
| audio bytes                            | played back as the agent's voice                  |

Backend index `k` (0-based step) maps to deck card `k + 1` (card `0` is the overview).

`set_available_ingredients` and `suggest_recipes` were **added** to the backend
(`handful/functions.py`, handled in `handful/agent_manager.py`) so the kitchen screen gets
structured data instead of only spoken suggestions. The agent is instructed to call them in
`prompts/cooking_assistant.txt`.

## Verified

Tested in a headless browser against the running server:

- Server boots; `/`, `/health`, `/support.js`, `/hero.png` serve correctly.
- Frontend loads with no console errors.
- **Offline path**: landing → kitchen → ingredient chips → 3 recipe options → pick →
  deck → overview → step cards → running timer card.
- **Live message path** (simulated backend events): ingredient chips, dynamic recipe
  suggestions, dynamic deck build from `recipe_update`, "In the Pan" derivation,
  `advance_step`/`go_to_step` index mapping, timer overlay, and substitution toast — all
  correct, with no text/panel overlap at laptop resolutions.

## Needs a live Deepgram key + mic to verify (only you can run this)

- Real WebSocket round-trip to the Deepgram agent.
- Wake-word capture and end-to-end audio (TTS playback).
- The agent actually calling the functions as instructed by the prompt — this depends on
  the model's behavior and may need prompt tuning once you hear it live.

## Debugging

`window.__handful` is exposed in the browser console — inspect `__handful.state`, or push a
simulated server event, e.g.:

```js
__handful.handleServer({ type:'function_call', name:'suggest_recipes',
  result:{ recipes:[{name:'Omelette', time:'10 MIN', difficulty:'EASY'}] } })
```
