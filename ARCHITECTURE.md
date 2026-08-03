# Architecture & message protocol

Handful is a **single FastAPI service** that runs the voice/AI agent **and** serves the
frontend, so the whole experience lives at one URL. This doc covers how the browser and
backend talk. For setup and a feature overview, see the [README](README.md).

## The pieces

- **Frontend** — the "DC" notecard UI, served from `handful/static/index.html`. It does
  wake-word detection and speech-to-text in the browser (Web Speech API), then sends the
  recognized command text to the backend.
- **Voice agent** — the FastAPI + Deepgram Voice Agent (`handful/agent_manager.py`).
  GPT-4o-mini reasons and calls functions; Aura-2 speaks the replies back as audio.
- **Recipe/session state** — `handful/recipe.py` + `handful/models.py`, the source of
  truth the on-screen notecards mirror.

## How the pieces talk

The browser opens one `/converse` WebSocket ⇄ the Deepgram agent. The frontend reacts to
these server messages (`handful/static/index.html` → `handleServer`):

| Server message / function call        | Frontend effect                                  |
|----------------------------------------|--------------------------------------------------|
| `set_available_ingredients`            | chips on the "What's in your kitchen?" screen     |
| `suggest_recipes`                      | the 2–3 recipe option cards                        |
| `set_recipe` + `recipe_update`         | builds the notecard deck (overview + step cards)  |
| `advance_step` / `go_to_step` / `get_current_step` | moves the deck to that step           |
| `substitute_ingredient`                | swap toast + updated ingredient in the deck       |
| `timer_update` / `timer_finished`      | the floating timer overlay                        |
| audio bytes                            | played back as the agent's voice                  |

Step index `k` (0-based) maps to deck card `k + 1` (card `0` is the overview).

`set_available_ingredients` and `suggest_recipes` are custom functions (`handful/functions.py`,
handled in `handful/agent_manager.py`) so the kitchen screen gets structured data instead of
only spoken suggestions. The agent is instructed to call them in `prompts/cooking_assistant.txt`.

## Offline demo

No Deepgram key? The page still works as a **standalone demo**: if the agent doesn't become
ready within a few seconds, the kitchen screen replays a canned ingredient → recipe → step
sequence so you can click through the whole flow offline.

## Debugging

`window.__handful` is exposed in the browser console — inspect `__handful.state`, or push a
simulated server event, e.g.:

```js
__handful.handleServer({ type:'function_call', name:'suggest_recipes',
  result:{ recipes:[{name:'Omelette', time:'10 MIN', difficulty:'EASY'}] } })
```
