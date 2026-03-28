@tool
extends EditorPlugin

## CreativElixir — AI-powered development assistant for Godot 4.x
##
## Main plugin entry point. Manages lifecycle of all subsystems:
## EventBus, ConfigManager, ApiManager, ChatController, and UI components.

var _event_bus: CreativElixirEventBus
var _config_manager: CreativElixirConfigManager
var _api_manager: CreativElixirApiManager
var _chat_controller: CreativElixirChatController

var _dock: CreativElixirChatDock
var _window: CreativElixirChatWindow
var _settings_dialog: CreativElixirSettingsDialog

var _is_popped_out := false


func _enter_tree() -> void:
	# Initialize core subsystems
	_event_bus = CreativElixirEventBus.new()
	_event_bus.name = "EventBus"
	add_child(_event_bus)

	_config_manager = CreativElixirConfigManager.new()
	_config_manager.name = "ConfigManager"
	add_child(_config_manager)

	_api_manager = CreativElixirApiManager.new(_config_manager, _event_bus)
	_api_manager.name = "ApiManager"
	add_child(_api_manager)

	_chat_controller = CreativElixirChatController.new(_api_manager, _event_bus, _config_manager)
	_chat_controller.name = "ChatController"
	add_child(_chat_controller)

	# Initialize dock UI
	_dock = CreativElixirChatDock.new()
	_dock.initialize(_chat_controller, _event_bus, _config_manager)
	add_control_to_dock(DOCK_SLOT_RIGHT_UL, _dock)

	# Initialize settings dialog (hidden by default)
	_settings_dialog = CreativElixirSettingsDialog.new()
	_settings_dialog.initialize(_config_manager, _event_bus)
	EditorInterface.get_base_control().add_child(_settings_dialog)

	# Connect UI signals
	_event_bus.pop_out_requested.connect(_on_pop_out)
	_event_bus.dock_requested.connect(_on_dock_back)
	_event_bus.settings_requested.connect(_on_settings_requested)

	print("CreativElixir v%s loaded." % CreativElixirConstants.PLUGIN_VERSION)


func _exit_tree() -> void:
	# Clean up window
	if _window and is_instance_valid(_window):
		_window.queue_free()
		_window = null

	# Clean up settings dialog
	if _settings_dialog and is_instance_valid(_settings_dialog):
		_settings_dialog.queue_free()
		_settings_dialog = null

	# Clean up dock
	if _dock and is_instance_valid(_dock):
		remove_control_from_docks(_dock)
		_dock.queue_free()
		_dock = null

	print("CreativElixir unloaded.")


# ── Pop Out / Dock Back ───────────────────────────────────────────

func _on_pop_out() -> void:
	if _is_popped_out:
		return

	# Detach ChatPanel from dock
	var panel := _dock.detach_chat_panel()
	if not panel:
		return

	# Create floating window
	_window = CreativElixirChatWindow.new()
	EditorInterface.get_base_control().add_child(_window)
	_window.attach_chat_panel(panel)
	_window.window_close_requested.connect(_on_dock_back)
	_window.popup_centered()

	_is_popped_out = true


func _on_dock_back() -> void:
	if not _is_popped_out:
		return

	if not _window or not is_instance_valid(_window):
		_is_popped_out = false
		return

	# Detach ChatPanel from window
	var panel := _window.detach_chat_panel()
	_window.queue_free()
	_window = null

	# Re-attach to dock
	if panel and _dock and is_instance_valid(_dock):
		_dock.attach_chat_panel(panel)

	_is_popped_out = false


# ── Settings ──────────────────────────────────────────────────────

func _on_settings_requested() -> void:
	if _settings_dialog and is_instance_valid(_settings_dialog):
		_settings_dialog.popup_centered()
