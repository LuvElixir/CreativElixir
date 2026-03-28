@tool
class_name CreativElixirChatPanel
extends VBoxContainer

## Shared chat UI panel — used by both the dock and floating window.
## Contains the header bar, message list, and input area.
## Loads previous chat history on startup.

var _chat_controller  # CreativElixirChatController
var _event_bus: CreativElixirEventBus
var _config: CreativElixirConfigManager

# Header
var _mode_toggle: OptionButton
var _screenshot_toggle: CheckButton
var _art_prompt_btn: Button
var _pop_out_btn: Button
var _settings_btn: Button
var _clear_btn: Button

# Status bar
var _status_label: Label
var _provider_label: Label

# Chat area
var _chat_scroll: ScrollContainer
var _message_container: VBoxContainer
var _loading_label: Label

# Input area
var _input_text: TextEdit
var _send_btn: Button
var _cancel_btn: Button

var _is_docked := true


func _init() -> void:
	_build_ui()


func initialize(controller, event_bus: CreativElixirEventBus,
		config: CreativElixirConfigManager) -> void:
	_chat_controller = controller
	_event_bus = event_bus
	_config = config
	_connect_signals()
	_update_provider_display()
	# Load previous history into UI
	call_deferred("_load_history_into_ui")


func _build_ui() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_theme_constant_override("separation", 2)

	# ── Header Bar ──
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 4)
	add_child(header)

	_mode_toggle = OptionButton.new()
	_mode_toggle.add_item("Smart", CreativElixirConstants.ContextMode.SMART)
	_mode_toggle.add_item("Full Scan", CreativElixirConstants.ContextMode.FULL_SCAN)
	_mode_toggle.selected = 0
	_mode_toggle.tooltip_text = "Smart: current scene/script. Full Scan: entire project (for debugging)."
	header.add_child(_mode_toggle)

	_screenshot_toggle = CheckButton.new()
	_screenshot_toggle.text = "Viewport"
	_screenshot_toggle.button_pressed = true
	_screenshot_toggle.tooltip_text = "Attach editor viewport screenshot (Vision)"
	header.add_child(_screenshot_toggle)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(spacer)

	_art_prompt_btn = Button.new()
	_art_prompt_btn.text = "Art"
	_art_prompt_btn.tooltip_text = "Art Prompt Generator"
	_art_prompt_btn.pressed.connect(_on_art_pressed)
	header.add_child(_art_prompt_btn)

	_pop_out_btn = Button.new()
	_pop_out_btn.text = "Pop Out"
	_pop_out_btn.tooltip_text = "Toggle dock / floating window"
	_pop_out_btn.pressed.connect(_on_pop_out_pressed)
	header.add_child(_pop_out_btn)

	_settings_btn = Button.new()
	_settings_btn.text = "Settings"
	_settings_btn.tooltip_text = "Configure API providers and keys"
	_settings_btn.pressed.connect(_on_settings_pressed)
	header.add_child(_settings_btn)

	_clear_btn = Button.new()
	_clear_btn.text = "Clear"
	_clear_btn.tooltip_text = "Clear chat history"
	_clear_btn.pressed.connect(_on_clear_pressed)
	header.add_child(_clear_btn)

	# ── Status Bar ──
	var status_bar := HBoxContainer.new()
	status_bar.add_theme_constant_override("separation", 8)
	add_child(status_bar)

	_provider_label = Label.new()
	_provider_label.add_theme_font_size_override("font_size", 11)
	_provider_label.add_theme_color_override("font_color", Color(0.5, 0.7, 0.5))
	status_bar.add_child(_provider_label)

	var status_spacer := Control.new()
	status_spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	status_bar.add_child(status_spacer)

	_status_label = Label.new()
	_status_label.add_theme_font_size_override("font_size", 11)
	_status_label.add_theme_color_override("font_color", Color(0.6, 0.6, 0.6))
	status_bar.add_child(_status_label)

	# ── Separator ──
	add_child(HSeparator.new())

	# ── Chat Scroll Area ──
	_chat_scroll = ScrollContainer.new()
	_chat_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_chat_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_chat_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(_chat_scroll)

	_message_container = VBoxContainer.new()
	_message_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_message_container.add_theme_constant_override("separation", 8)
	_chat_scroll.add_child(_message_container)

	# Loading indicator
	_loading_label = Label.new()
	_loading_label.text = "Thinking..."
	_loading_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_loading_label.add_theme_color_override("font_color", Color(0.7, 0.7, 0.3))
	_loading_label.visible = false
	_message_container.add_child(_loading_label)

	# ── Separator ──
	add_child(HSeparator.new())

	# ── Input Area ──
	var input_bar := HBoxContainer.new()
	input_bar.add_theme_constant_override("separation", 4)
	add_child(input_bar)

	_input_text = TextEdit.new()
	_input_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_input_text.custom_minimum_size.y = 60
	_input_text.placeholder_text = "Type your message... (Ctrl+Enter to send)"
	_input_text.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	input_bar.add_child(_input_text)

	var btn_vbox := VBoxContainer.new()
	btn_vbox.add_theme_constant_override("separation", 2)
	input_bar.add_child(btn_vbox)

	_send_btn = Button.new()
	_send_btn.text = "Send"
	_send_btn.custom_minimum_size = Vector2(70, 0)
	_send_btn.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_send_btn.pressed.connect(_on_send_pressed)
	btn_vbox.add_child(_send_btn)

	_cancel_btn = Button.new()
	_cancel_btn.text = "Cancel"
	_cancel_btn.custom_minimum_size = Vector2(70, 0)
	_cancel_btn.visible = false
	_cancel_btn.pressed.connect(_on_cancel_pressed)
	btn_vbox.add_child(_cancel_btn)


func _connect_signals() -> void:
	if not _event_bus:
		return

	_event_bus.response_received.connect(_on_response_received)
	_event_bus.api_error.connect(_on_api_error)
	_event_bus.request_started.connect(_on_request_started)
	_event_bus.request_finished.connect(_on_request_finished)
	_event_bus.action_executed.connect(_on_action_executed)
	_event_bus.settings_changed.connect(_update_provider_display)


func _input(event: InputEvent) -> void:
	if not _input_text or not _input_text.has_focus():
		return
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ENTER and event.ctrl_pressed:
			_on_send_pressed()
			get_viewport().set_input_as_handled()


# ── Public Methods ──────────────────────────────────────────────

func set_docked(docked: bool) -> void:
	_is_docked = docked
	if _pop_out_btn:
		_pop_out_btn.text = "Pop Out" if docked else "Dock"


func add_message(role: String, content: String, timestamp: String = "") -> void:
	var bubble := CreativElixirMessageBubble.new()
	var idx := _loading_label.get_index()
	_message_container.add_child(bubble)
	_message_container.move_child(bubble, idx)
	bubble.setup(role, content, timestamp)
	bubble.apply_requested.connect(_on_code_apply_requested)
	_scroll_to_bottom()


func clear_messages() -> void:
	for child in _message_container.get_children():
		if child != _loading_label:
			child.queue_free()


# ── Signal Handlers ─────────────────────────────────────────────

func _on_send_pressed() -> void:
	var text := _input_text.text.strip_edges()
	if text.is_empty():
		return

	_input_text.text = ""
	add_message("user", text)

	if _chat_controller and _chat_controller.has_method("handle_user_message"):
		var context_mode: int = _mode_toggle.get_selected_id()
		var include_screenshot: bool = _screenshot_toggle.button_pressed
		_chat_controller.handle_user_message(text, context_mode, include_screenshot)


func _on_cancel_pressed() -> void:
	if _chat_controller and _chat_controller.has_method("cancel_request"):
		_chat_controller.cancel_request()
	elif _chat_controller:
		# Fallback: cancel via api_manager
		var api_mgr = _chat_controller.get_node_or_null("../ApiManager")
		if api_mgr and api_mgr.has_method("cancel_request"):
			api_mgr.cancel_request()


func _on_request_started() -> void:
	_loading_label.visible = true
	_send_btn.visible = false
	_cancel_btn.visible = true
	_status_label.text = "Requesting..."
	_status_label.add_theme_color_override("font_color", Color(0.7, 0.7, 0.3))


func _on_request_finished() -> void:
	_loading_label.visible = false
	_send_btn.visible = true
	_cancel_btn.visible = false
	_status_label.text = "Ready"
	_status_label.add_theme_color_override("font_color", Color(0.6, 0.6, 0.6))


func _on_response_received(result: Dictionary) -> void:
	var content: String = result.get("content", "")
	if not content.is_empty():
		add_message("assistant", content)
	# Show token usage if available
	var usage: Dictionary = result.get("usage", {})
	if not usage.is_empty():
		var total = usage.get("total_tokens", usage.get("input_tokens", 0) + usage.get("output_tokens", 0))
		if total > 0:
			_status_label.text = "Tokens: %d" % total


func _on_api_error(error_message: String) -> void:
	add_message("assistant", "[color=red]Error: " + error_message + "[/color]")


func _on_action_executed(action_name: String, success: bool, message: String) -> void:
	var color := "green" if success else "red"
	var status := "OK" if success else "FAIL"
	add_message("assistant",
		"[color=%s][%s] %s: %s[/color]" % [color, status, action_name, message])


func _on_clear_pressed() -> void:
	clear_messages()
	if _event_bus:
		_event_bus.chat_cleared.emit()


func _on_pop_out_pressed() -> void:
	if _event_bus:
		if _is_docked:
			_event_bus.pop_out_requested.emit()
		else:
			_event_bus.dock_requested.emit()


func _on_settings_pressed() -> void:
	if _event_bus:
		_event_bus.settings_requested.emit()


func _on_art_pressed() -> void:
	if _event_bus:
		_event_bus.art_panel_requested.emit()


func _on_code_apply_requested(code: String, file_path: String) -> void:
	if _chat_controller and _chat_controller.has_method("apply_code"):
		_chat_controller.apply_code(code, file_path)


# ── Private Helpers ─────────────────────────────────────────────

func _scroll_to_bottom() -> void:
	await get_tree().process_frame
	if is_instance_valid(_chat_scroll):
		_chat_scroll.scroll_vertical = _chat_scroll.get_v_scroll_bar().max_value


func _update_provider_display() -> void:
	if not _config or not _provider_label:
		return
	var provider := _config.get_active_provider()
	var model := _config.get_model_name(provider)
	_provider_label.text = "%s / %s" % [provider.to_upper(), model]


func _load_history_into_ui() -> void:
	if not _chat_controller or not _chat_controller.has_method("get_chat_history"):
		return
	var history: Array = _chat_controller.get_chat_history()
	for msg in history:
		var role: String = msg.get("role", "user")
		var content: String = msg.get("content", "")
		var timestamp: String = msg.get("timestamp", "")
		if not content.is_empty():
			add_message(role, content, timestamp)
