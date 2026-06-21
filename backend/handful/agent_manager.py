from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from deepgram import AsyncDeepgramClient
from deepgram.agent.v1.types import (
    AgentV1FunctionCallRequest,
    AgentV1SendFunctionCallResponse,
    AgentV1Settings,
    AgentV1SettingsAgent,
    AgentV1SettingsAgentListen,
    AgentV1SettingsAgentListenProvider_V1,
    AgentV1SettingsAudio,
    AgentV1SettingsAudioInput,
    AgentV1SettingsAudioOutput,
)
from deepgram.core.events import EventType
from deepgram.types.speak_settings_v1 import SpeakSettingsV1
from deepgram.types.speak_settings_v1provider import SpeakSettingsV1Provider_Deepgram
from deepgram.types.think_settings_v1 import ThinkSettingsV1
from deepgram.types.think_settings_v1provider import ThinkSettingsV1Provider_OpenAi

from .functions import FUNCTION_DEFINITIONS
from .recipe import RecipeStateManager
from .timer import TimerManager

logger = logging.getLogger(__name__)

SAMPLE_RATE = 24000
SYSTEM_PROMPT = Path("prompts/cooking_assistant.txt").read_text()


class AgentSession:
    def __init__(self, client_send: callable):
        self._client_send = client_send
        self.recipe = RecipeStateManager()
        self.timers = TimerManager()
        self._agent = None
        self._settings_applied = asyncio.Event()
        self.available_ingredients: list[str] = []
        self.suggested_recipes: list[dict] = []

        self.timers.set_on_timer_finished(self._on_timer_finished)

    def _set_available_ingredients(self, ingredients: list[str] | None = None) -> dict:
        self.available_ingredients = ingredients or []
        return {"success": True, "ingredients": self.available_ingredients}

    def _suggest_recipes(self, recipes: list[dict] | None = None) -> dict:
        self.suggested_recipes = recipes or []
        return {"success": True, "recipes": self.suggested_recipes}

    async def _on_timer_finished(self, timer_id: str, label: str) -> None:
        await self._send_to_client({"type": "timer_finished", "timer_id": timer_id, "label": label})
        if self._agent:
            from deepgram.agent.v1.types import AgentV1InjectUserMessage
            msg = AgentV1InjectUserMessage(
                type="InjectUserMessage",
                content=f"[System: The timer '{label}' has finished.]",
            )
            await self._agent.send_inject_user_message(msg)

    async def _send_to_client(self, data: dict) -> None:
        try:
            await self._client_send(json.dumps(data))
        except Exception:
            pass

    def _build_settings(self) -> AgentV1Settings:
        return AgentV1Settings(
            audio=AgentV1SettingsAudio(
                input=AgentV1SettingsAudioInput(
                    encoding="linear16",
                    sample_rate=SAMPLE_RATE,
                ),
                output=AgentV1SettingsAudioOutput(
                    encoding="linear16",
                    sample_rate=SAMPLE_RATE,
                ),
            ),
            agent=AgentV1SettingsAgent(
                listen=AgentV1SettingsAgentListen(
                    provider=AgentV1SettingsAgentListenProvider_V1(
                        type="deepgram",
                        model="nova-3",
                    ),
                ),
                think=ThinkSettingsV1(
                    provider=ThinkSettingsV1Provider_OpenAi(
                        type="open_ai",
                        model="gpt-4o-mini",
                        temperature=0.7,
                    ),
                    prompt=SYSTEM_PROMPT,
                    functions=FUNCTION_DEFINITIONS,
                ),
                speak=SpeakSettingsV1(
                    provider=SpeakSettingsV1Provider_Deepgram(
                        type="deepgram",
                        model="aura-2-asteria-en",
                    ),
                ),
                greeting="Hello! I'm Handful. What would you like to cook today?",
            ),
        )

    async def _handle_function_call(self, request: AgentV1FunctionCallRequest) -> None:
        for func in request.functions:
            func_id = func.id
            func_name = func.name
            try:
                args = json.loads(func.arguments)
            except json.JSONDecodeError:
                args = {}

            handler = self._get_function_handler(func_name)
            if handler is None:
                result = json.dumps({"success": False, "error": f"Unknown function: {func_name}"})
            else:
                if asyncio.iscoroutinefunction(handler):
                    result_data = await handler(**args)
                else:
                    result_data = handler(**args)
                result = json.dumps(result_data)

            response = AgentV1SendFunctionCallResponse(
                type="FunctionCallResponse",
                id=func_id,
                name=func_name,
                content=result,
            )
            await self._agent.send_function_call_response(response)

            await self._send_to_client(
                {"type": "function_call", "name": func_name, "args": args, "result": json.loads(result)}
            )

            RECIPE_FUNCTIONS = {"set_recipe", "advance_step", "go_to_step", "substitute_ingredient"}
            if func_name in RECIPE_FUNCTIONS:
                state = self.recipe.get_state()
                if state.get("success"):
                    await self._send_to_client({"type": "recipe_update", "recipe": state["recipe"]})

    def _get_function_handler(self, name: str) -> callable | None:
        handlers = {
            "set_available_ingredients": self._set_available_ingredients,
            "suggest_recipes": self._suggest_recipes,
            "start_timer": self.timers.start_timer,
            "cancel_timer": self.timers.cancel_timer,
            "get_timers": self.timers.get_timers,
            "set_recipe": self.recipe.set_recipe,
            "get_current_step": self.recipe.get_current_step,
            "advance_step": self.recipe.advance_step,
            "go_to_step": self.recipe.go_to_step,
            "substitute_ingredient": self.recipe.substitute_ingredient,
            "add_note": self.recipe.add_note,
            "save_session": self.recipe.save_session,
        }
        return handlers.get(name)

    async def _on_dg_message(self, message) -> None:
        if isinstance(message, bytes):
            try:
                await self._client_send(message)
            except Exception:
                pass
            return

        msg_type = getattr(message, "type", None)

        if msg_type == "SettingsApplied":
            self._settings_applied.set()
            await self._send_to_client({"type": "settings_applied"})

        elif msg_type == "ConversationText":
            role = getattr(message, "role", "unknown")
            content = getattr(message, "content", "")
            await self._send_to_client({"type": "conversation_text", "role": role, "content": content})

        elif msg_type == "UserStartedSpeaking":
            await self._send_to_client({"type": "user_started_speaking"})

        elif msg_type == "AgentThinking":
            await self._send_to_client({"type": "agent_thinking"})

        elif msg_type == "AgentStartedSpeaking":
            await self._send_to_client({"type": "agent_started_speaking"})

        elif msg_type == "AgentAudioDone":
            await self._send_to_client({"type": "agent_audio_done"})

        elif msg_type == "FunctionCallRequest":
            await self._handle_function_call(message)

        elif msg_type == "Error":
            code = getattr(message, "code", "unknown")
            description = getattr(message, "description", "unknown error")
            logger.error(f"Deepgram agent error: {code} - {description}")
            await self._send_to_client({"type": "error", "code": code, "message": description})

    async def run(self, api_key: str, client_media_iter) -> None:
        dg = AsyncDeepgramClient(api_key=api_key)

        async with dg.agent.v1.connect() as agent:
            self._agent = agent
            agent.on(EventType.MESSAGE, self._on_dg_message)

            listen_task = asyncio.create_task(agent.start_listening())
            await agent.send_settings(self._build_settings())

            try:
                await asyncio.wait_for(self._settings_applied.wait(), timeout=15.0)
            except asyncio.TimeoutError:
                logger.error("Timed out waiting for settings to apply")
                await self._send_to_client({"type": "error", "message": "Agent settings timed out"})
                return

            await self._send_to_client({"type": "ready"})

            timer_update_task = asyncio.create_task(self._timer_update_loop())

            try:
                async for media_bytes in client_media_iter:
                    await agent.send_media(media_bytes)
            except Exception as exc:
                logger.info(f"Client media stream ended: {exc}")
            finally:
                timer_update_task.cancel()
                listen_task.cancel()

    async def _timer_update_loop(self) -> None:
        while True:
            await asyncio.sleep(1.0)
            updates = self.timers.get_active_timers()
            if updates:
                try:
                    await self._send_to_client({"type": "timer_update", "timers": updates})
                except Exception:
                    break
