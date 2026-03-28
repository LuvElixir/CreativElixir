@tool
class_name CreativElixirChatController
extends Node

## Central orchestrator connecting UI, API, context, and agent systems.
## All chat operations flow through this controller.

var _api_manager: CreativElixirApiManager
var _event_bus: CreativElixirEventBus
var _config: CreativElixirConfigManager
var _context_gatherer: CreativElixirContextGatherer
var _action_parser: CreativElixirActionParser
var _action_executor: CreativElixirActionExecutor
var _chat_history: Array = []  # Array of {"role": String, "content": String}


func _init(api_manager: CreativElixirApiManager = null,
		event_bus: CreativElixirEventBus = null,
		config: CreativElixirConfigManager = null) -> void:
	_api_manager = api_manager
	_event_bus = event_bus
	_config = config
	_action_parser = CreativElixirActionParser.new()


func _ready() -> void:
	# Context gatherer needs to be in the tree (has child LogReader)
	_context_gatherer = CreativElixirContextGatherer.new()
	_context_gatherer.name = "ContextGatherer"
	add_child(_context_gatherer)

	if _event_bus:
		_event_bus.response_received.connect(_on_response_received)
		_event_bus.chat_cleared.connect(_on_chat_cleared)


## Set the UndoRedo manager (called from main plugin after tree is ready).
func set_undo_redo(undo_redo: EditorUndoRedoManager) -> void:
	_action_executor = CreativElixirActionExecutor.new(_event_bus, undo_redo)
	_action_executor.name = "ActionExecutor"
	add_child(_action_executor)


## Handle a user message from the UI.
func handle_user_message(text: String, context_mode: int,
		include_screenshot: bool) -> void:
	if not _api_manager:
		if _event_bus:
			_event_bus.api_error.emit("API manager not initialized.")
		return

	# Gather context
	var context := _context_gatherer.gather(context_mode)

	# Capture screenshot
	var images: Array = []
	if include_screenshot:
		var screenshot := CreativElixirViewportCapture.capture()
		if screenshot:
			images.append(screenshot)

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
	var result := CreativElixirCodeApplier.apply(code, file_path)
	if _event_bus:
		_event_bus.action_executed.emit(
			"apply_code",
			result.get("success", false),
			result.get("message", "")
		)


func get_chat_history() -> Array:
	return _chat_history.duplicate()


## Get recent errors from the log reader.
func get_recent_errors() -> String:
	if _context_gatherer:
		return _context_gatherer.get_recent_errors()
	return ""


# ── Private ───────────────────────────────────────────────────────

func _get_recent_history(max_count: int) -> Array:
	if _chat_history.size() <= max_count:
		return _chat_history.duplicate()
	return _chat_history.slice(_chat_history.size() - max_count)


func _on_response_received(result: Dictionary) -> void:
	var content: String = result.get("content", "")
	if content.is_empty():
		return

	_chat_history.append({"role": "assistant", "content": content})

	# Parse actions from response
	var parsed := _action_parser.parse(content)
	var actions: Array = parsed.get("actions", [])

	# Execute actions if any
	if not actions.is_empty() and _action_executor:
		_action_executor.execute_all(actions)


func _on_chat_cleared() -> void:
	_chat_history.clear()
