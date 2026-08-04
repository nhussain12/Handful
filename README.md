# Handful

A hands-free, voice-native cooking assistant. Tell it what you have or what you want to
make, and it reads the recipe aloud on a touchless display so you never touch your phone while cooking.

Built at UC Berkeley's AI Hackathon. → [Devpost](https://devpost.com/software/handful-hc7826)

## Features

- Start from ingredients (*"eggs, bread, spinach"*) or a dish (*"let's do shakshuka"*).
- Wake word — address it as **"Chef"**, with fuzzy matching for speech-recognition mishears.
- A notecard deck of ingredients, recipe options, and steps that tracks the conversation.
- Live recipe editing by voice: substitute ingredients, add/reword/remove steps.
- Multiple concurrent voice-controlled timers.
- Saved session notes ("less salt next time") persisted per recipe.

## How it works

A single FastAPI service runs the voice agent and serves the frontend, with speech,
reasoning, and UI synced over one WebSocket.

```
 🎙️  Browser                              FastAPI  /converse         Deepgram Voice Agent
 ├─ Web Speech API ── "Chef, …" text ──▶   WebSocket  ── inject ──▶   ├─ GPT-4o-mini  reasoning + tool calls
 │  (wake word + STT)                          │                      └─ Aura-2       text-to-speech
 ├─ notecard UI    ◀── function-call updates ──┤
 └─ audio out      ◀── agent voice (PCM) ──────┘
```

The browser does wake-word detection and speech-to-text (Web Speech API) and sends command
text down the socket. Deepgram reasons over it (GPT-4o-mini) and speaks back (Aura-2). Each
function call both answers the agent and pushes a UI update, so the notecards stay a
projection of the same recipe state the agent reasons over.

> The backend also accepts raw mic audio and transcribes it server-side with Deepgram
> **Nova-3** — the path used by the bundled [`reference_client.html`](reference_client.html).

| Agent function call                                    | On-screen effect                          |
| ------------------------------------------------------ | ----------------------------------------- |
| `set_available_ingredients`                            | chips on the "What's in your kitchen?" screen |
| `suggest_recipes`                                      | the 2–3 recipe option cards               |
| `set_recipe`                                           | builds the notecard deck (overview + steps) |
| `advance_step` / `go_to_step`                          | moves the deck to that step               |
| `add_step` / `update_step` / `remove_step`             | inserts, rewrites, or drops a step card   |
| `add_ingredient` / `remove_ingredient` / `substitute_ingredient` | updates the ingredient list + swap toast |
| `start_timer` / `cancel_timer`                         | the floating timer overlay                |
| `add_note` / `save_session`                            | persists the session to a notes file      |

## Tech stack

| Layer               | Technology                                                        |
| ------------------- | ----------------------------------------------------------------- |
| **Speech (client)** | Web Speech API — wake-word ("Chef") detection + speech-to-text    |
| **Voice agent**     | [Deepgram Voice Agent](https://deepgram.com) — Aura-2 (TTS), Nova-3 (server-side STT) |
| **Reasoning**       | GPT-4o-mini with function calling                                 |
| **Backend**         | Python 3.13, FastAPI, WebSockets, `asyncio`                       |
| **Frontend**        | Vanilla JS + CSS notecard UI, single WebSocket client             |
| **Tooling**         | [uv](https://docs.astral.sh/uv/)                                  |

## Project structure

```
Handful/
├── main.py                 uvicorn entrypoint
├── handful/                the application package
│   ├── server.py           FastAPI app, routes, /converse WebSocket
│   ├── agent_manager.py    Deepgram session, function-call dispatch, UI sync
│   ├── functions.py        tool/function schemas exposed to the model
│   ├── recipe.py           recipe + session state manager
│   ├── timer.py            async multi-timer manager
│   ├── models.py           dataclasses (Recipe, Ingredient, Timer, Session…)
│   └── static/             the served frontend (index.html, support.js, assets)
├── prompts/                the cooking-assistant system prompt
├── reference_client.html   a minimal dev client for the /converse endpoint
├── pyproject.toml          dependencies (managed with uv)
└── ARCHITECTURE.md         WebSocket message protocol + debugging notes
```

## Run it locally

Requires a [Deepgram API key](https://console.deepgram.com/) and Chrome.

```bash
cp .env.example .env                 # then add your key:
echo "DEEPGRAM_API_KEY=sk_..." > .env
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in Chrome, click **Get Started**, allow the microphone, and say
**"Chef, …"**. Without a key, the frontend runs a canned demo flow you can click through.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the WebSocket message protocol and debugging notes.

## Roadmap

- Mobile pantry scanning (photograph what you have)
- User-uploaded and saved recipes
- Cooking-specific models for substitutions and scaling
