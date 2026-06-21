from __future__ import annotations

from deepgram.types.think_settings_v1functions_item import ThinkSettingsV1FunctionsItem

FUNCTION_DEFINITIONS: list[ThinkSettingsV1FunctionsItem] = [
    ThinkSettingsV1FunctionsItem(
        name="start_timer",
        description="Start a countdown timer for a specified number of minutes",
        parameters={
            "type": "object",
            "properties": {
                "minutes": {
                    "type": "number",
                    "description": "Number of minutes for the timer",
                },
                "label": {
                    "type": "string",
                    "description": "What this timer is for, e.g. 'chicken' or 'pasta'",
                },
            },
            "required": ["minutes", "label"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="cancel_timer",
        description="Cancel a running timer by its label",
        parameters={
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Label of the timer to cancel, e.g. 'chicken'",
                },
            },
            "required": ["label"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="get_timers",
        description="Get the status of all running timers",
        parameters={
            "type": "object",
            "properties": {},
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="set_available_ingredients",
        description="Record the ingredients the user says they have on hand. Call this as soon as the user lists what is in their kitchen, and again whenever they add more. Pass the full current list each time.",
        parameters={
            "type": "object",
            "properties": {
                "ingredients": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Plain ingredient names the user has, e.g. ['flour', 'eggs', 'butter']",
                },
            },
            "required": ["ingredients"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="suggest_recipes",
        description="Offer the user a short list of recipe options to choose from, based on the ingredients they have. Call this after the user has listed their ingredients, before set_recipe. Offer two or three options.",
        parameters={
            "type": "object",
            "properties": {
                "recipes": {
                    "type": "array",
                    "description": "Two or three recipe options to present",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Recipe name"},
                            "time": {"type": "string", "description": "Rough total time, e.g. '20 MIN'"},
                            "difficulty": {"type": "string", "description": "EASY, MEDIUM, or HARD"},
                        },
                        "required": ["name"],
                    },
                },
            },
            "required": ["recipes"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="set_recipe",
        description="Set the current recipe with name, ingredients, and steps. Call this when the user picks one of the suggested dishes (by name or number) or names a dish they want to make.",
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the recipe",
                },
                "ingredients": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of ingredients with quantities, e.g. ['2 cups, flour', '1 tbsp, sugar']",
                },
                "steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of cooking steps in order",
                },
            },
            "required": ["name", "ingredients", "steps"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="get_current_step",
        description="Get the current step of the recipe the user is on",
        parameters={
            "type": "object",
            "properties": {},
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="advance_step",
        description="Advance to the next step of the recipe",
        parameters={
            "type": "object",
            "properties": {},
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="go_to_step",
        description="Go to a specific step in the recipe",
        parameters={
            "type": "object",
            "properties": {
                "step_index": {
                    "type": "integer",
                    "description": "The step number to go to (0-indexed)",
                },
            },
            "required": ["step_index"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="substitute_ingredient",
        description="Substitute an ingredient in the current recipe for a different one",
        parameters={
            "type": "object",
            "properties": {
                "original": {
                    "type": "string",
                    "description": "The original ingredient to replace",
                },
                "replacement": {
                    "type": "string",
                    "description": "What to replace the original ingredient with",
                },
                "reason": {
                    "type": "string",
                    "description": "Why the substitution is being made",
                },
            },
            "required": ["original", "replacement"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="add_step",
        description="Add a new step to the current recipe (e.g. the dish gets more involved, or the user wants an extra step). A new notecard appears for it on screen.",
        parameters={
            "type": "object",
            "properties": {
                "instruction": {
                    "type": "string",
                    "description": "The full instruction text for the new step",
                },
                "position": {
                    "type": "integer",
                    "description": "Optional 0-indexed position to insert the step at. Omit to add it at the end.",
                },
            },
            "required": ["instruction"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="update_step",
        description="Change the wording of a step. The notecard for that step updates to match. To change the step the user is currently on (e.g. they say 'change this step' or 'actually, do it this way'), omit step_index.",
        parameters={
            "type": "object",
            "properties": {
                "instruction": {
                    "type": "string",
                    "description": "The new instruction text for that step",
                },
                "step_index": {
                    "type": "integer",
                    "description": "0-indexed step to change. Omit to change the current step the user is on.",
                },
            },
            "required": ["instruction"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="remove_step",
        description="Remove a step from the recipe that is no longer needed. Its notecard is removed. Omit step_index to remove the current step.",
        parameters={
            "type": "object",
            "properties": {
                "step_index": {
                    "type": "integer",
                    "description": "0-indexed step to remove. Omit to remove the current step.",
                },
            },
            "required": [],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="add_ingredient",
        description="Add an ingredient to the current recipe (e.g. the user decides to throw something extra in). It appears in the ingredient list on the cards.",
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Ingredient name, e.g. 'mushrooms'",
                },
                "quantity": {
                    "type": "string",
                    "description": "Amount, e.g. '1 cup' (optional)",
                },
            },
            "required": ["name"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="remove_ingredient",
        description="Remove an ingredient from the current recipe. It disappears from the ingredient list on the cards.",
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Ingredient name to remove",
                },
            },
            "required": ["name"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="add_note",
        description="Add a note to the current cooking session (e.g., what the user learned, changes made, rating)",
        parameters={
            "type": "object",
            "properties": {
                "note": {
                    "type": "string",
                    "description": "The note content to save",
                },
            },
            "required": ["note"],
        },
    ),
    ThinkSettingsV1FunctionsItem(
        name="save_session",
        description="Save the current cooking session notes to a file. Call this when the user is done cooking or asks to save their session.",
        parameters={
            "type": "object",
            "properties": {},
        },
    ),
]
