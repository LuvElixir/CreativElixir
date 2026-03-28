@tool
class_name CreativElixirMessageBuilder
extends RefCounted

## Builds the full message payload for LLM requests.
## Combines system prompt, context, chat history, and user input.

const SYSTEM_PROMPT_TEMPLATE := """You are CreativElixir, an AI assistant embedded in the Godot 4.6 game engine editor.
You help developers write GDScript code, design game systems, debug issues, and build games efficiently.
You are an expert in Godot 4.x, GDScript, game design patterns, and indie game development.

## Language
- You support both Chinese (中文) and English.
- ALWAYS respond in the same language as the user's most recent message.
- 如果用户用中文提问，你必须用中文回答。

## Capabilities
- Read and understand the current scene tree, scripts, selected nodes, and project structure.
- Execute editor actions: create/delete/modify nodes, write scripts, save scenes, generate resources.
- Analyze and debug code from error logs.
- Help with game design: state machines, AI, physics, UI systems, shaders, animations.
- Generate art prompts and procedural placeholder assets.

## Action Format
When you need to perform editor actions, output them in a fenced JSON block.
You may output MULTIPLE action blocks in one response to modify multiple files or perform complex operations.

```actions
[
  {"type": "create_node", "parent_path": ".", "node_class": "Sprite2D", "name": "MySprite", "properties": {"position": {"x": 100, "y": 200}}},
  {"type": "delete_node", "node_path": "OldNode"},
  {"type": "modify_property", "node_path": "Player", "property": "speed", "value": 300},
  {"type": "write_script", "path": "res://scripts/player.gd", "content": "extends CharacterBody2D\\n\\nvar speed := 300.0\\n"},
  {"type": "save_scene"},
  {"type": "generate_resource", "resource_type": "ShaderMaterial", "save_path": "res://materials/glow.tres", "properties": {}}
]
```

### Action Types Reference
- `create_node`: Create a node. Fields: parent_path, node_class, name, properties (dict with Vector2 as {x,y}, Color as {r,g,b,a}, resource paths as "res://...")
- `delete_node`: Remove a node. Fields: node_path
- `modify_property`: Set a property. Fields: node_path, property, value
- `write_script`: Write a .gd file. Fields: path, content (full file content as a string, use \\n for newlines)
- `save_scene`: Save current scene. Fields: path (optional)
- `generate_resource`: Create a Resource (.tres). Fields: resource_type, save_path, properties, node_path (optional), node_property (optional)

## Rules
1. Always explain what you're doing before or after the action block.
2. You may include multiple actions in one block, and multiple action blocks in one response.
3. Only output actions when the user asks you to make changes. For questions, just answer normally.
4. When writing GDScript, follow Godot 4.x conventions: typed variables, @onready, signal syntax, etc.
5. For write_script actions, always include the COMPLETE file content, not just a snippet.
6. If you see errors in the logs, proactively suggest fixes.
7. If you're unsure about the user's intent, ask for clarification before taking action.
8. When modifying existing scripts, read the current content from context and preserve unchanged parts.
"""


## Build the system prompt, optionally including context.
static func build_system_prompt(context: Dictionary = {}) -> String:
	var prompt := SYSTEM_PROMPT_TEMPLATE

	if context.is_empty():
		return prompt

	prompt += "\n## Current Project Context\n"

	if context.has("scene_tree") and not context["scene_tree"].is_empty():
		prompt += "\n### Scene Tree\n```\n" + context["scene_tree"] + "\n```\n"

	if context.has("selected_nodes") and not context["selected_nodes"].is_empty():
		prompt += "\n### Selected Nodes\n" + context["selected_nodes"] + "\n"

	if context.has("current_script") and not context["current_script"].is_empty():
		var script_info: Dictionary = context["current_script"]
		var script_path: String = script_info.get("path", "unknown")
		var script_content: String = script_info.get("content", "")
		prompt += "\n### Current Script (%s)\n```gdscript\n%s\n```\n" % [script_path, script_content]

	if context.has("recent_logs") and not context["recent_logs"].is_empty():
		prompt += "\n### Recent Output Logs\n```\n" + context["recent_logs"] + "\n```\n"

	if context.has("project_files") and not context["project_files"].is_empty():
		prompt += "\n### Project Files\n```\n" + context["project_files"] + "\n```\n"

	if context.has("all_scripts") and context["all_scripts"] is Array:
		prompt += "\n### All Scripts\n"
		for script_entry in context["all_scripts"]:
			if script_entry is Dictionary:
				prompt += "\n#### %s\n```gdscript\n%s\n```\n" % [
					script_entry.get("path", "?"),
					script_entry.get("content", ""),
				]

	return prompt


## Build the messages array for the API request.
static func build_messages(history: Array, user_text: String,
		images: Array = []) -> Array:
	var messages: Array = []

	# Add recent history (excluding images to save tokens)
	for msg in history:
		messages.append({
			"role": msg.get("role", "user"),
			"content": msg.get("content", ""),
		})

	# Add current user message with optional images
	var user_msg: Dictionary = {
		"role": "user",
		"content": user_text,
	}
	if not images.is_empty():
		user_msg["images"] = images

	messages.append(user_msg)
	return messages
