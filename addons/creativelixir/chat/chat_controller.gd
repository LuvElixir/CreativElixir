@tool
class_name CreativElixirChatController
extends Node

## Central orchestrator connecting UI, API, context, and agent systems.
## All chat operations flow through this controller.

var _api_manager: CreativElixirApiManager
var _event_bus: CreativElixirEventBus
var _config: CreativElixirConfigManager
var _chat_history: Array = []  # Array of {"role": String, "content": String}


func _init(api_manager: CreativElixirApiManager = null,
		event_bus: CreativElixirEventBus = null,
		config: CreativElixirConfigManager = null) -> void:
	_api_manager = api_manager
	_event_bus = event_bus
	_config = config


func _ready() -> void:
	if _event_bus:
		_event_bus.response_received.connect(_on_response_received)
		_event_bus.chat_cleared.connect(_on_chat_cleared)


## Handle a user message from the UI.
func handle_user_message(text: String, context_mode: int,
		include_screenshot: bool) -> void:
	if not _api_manager:
		if _event_bus:
			_event_bus.api_error.emit("API manager not initialized.")
		return

	# Gather context (Phase 2 — for now, empty context)
	var context := _gather_context(context_mode)

	# Capture screenshot (Phase 2 — for now, skip)
	var images: Array = []
	# TODO: if include_screenshot: images = [viewport_capture.capture()]

	# Build system prompt with context
	var system_prompt := CreativElixirMessageBuilder.build_system_prompt(context)

	# Build messages array
	var recent_history := _get_recent_history(CreativElixirConstants.MAX_CHAT_HISTORY_MESSAGES)
	var messages := CreativElixirMessageBuilder.build_messages(recent_history, text, images)

	# Record user message in history
	_chat_history.append({"role": "user", "content": text})

	# Send to API
	_api_manager.send_message(messages, system_prompt)


## Apply a code block to a file. Used by the "Apply" button in chat.
func apply_code(code: String, file_path: String) -> void:
	if file_path.is_empty():
		# Try to write to the currently open script
		# Phase 3 will implement this properly via EditorInterface
		if _event_bus:
			_event_bus.api_error.emit("No target file specified for code apply. Feature coming in Phase 3.")
		return

	# Write the code to the file
	var file := FileAccess.open(file_path, FileAccess.WRITE)
	if not file:
		if _event_bus:
			_event_bus.api_error.emit("Failed to open file for writing: " + file_path)
		return

	file.store_string(code)
	file.close()

	if _event_bus:
		_event_bus.action_executed.emit("write_script", true, "Code applied to " + file_path)


func get_chat_history() -> Array:
	return _chat_history.duplicate()


# ── Private ───────────────────────────────────────────────────────

func _gather_context(_mode: int) -> Dictionary:
	# Phase 2 will implement full context gathering.
	# For now, return empty context.
	return {}


func _get_recent_history(max_count: int) -> Array:
	if _chat_history.size() <= max_count:
		return _chat_history.duplicate()
	return _chat_history.slice(_chat_history.size() - max_count)


func _on_response_received(result: Dictionary) -> void:
	var content: String = result.get("content", "")
	if not content.is_empty():
		_chat_history.append({"role": "assistant", "content": content})

		# Phase 3: Parse actions from response and execute them
		# var parsed = action_parser.parse(content)
		# action_executor.execute_all(parsed.actions)


func _on_chat_cleared() -> void:
	_chat_history.clear()
