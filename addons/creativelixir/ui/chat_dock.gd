@tool
class_name CreativElixirChatDock
extends Control

## 停靠面板包装器，嵌入共享的 ChatPanel。

var _chat_panel: CreativElixirChatPanel


func _init() -> void:
	name = "CreativElixir"
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(320, 400)


func initialize(controller, event_bus: CreativElixirEventBus,
		config: CreativElixirConfigManager) -> void:
	_chat_panel = CreativElixirChatPanel.new()
	add_child(_chat_panel)
	_chat_panel.initialize(controller, event_bus, config)
	_chat_panel.set_docked(true)


func get_chat_panel() -> CreativElixirChatPanel:
	return _chat_panel


## Remove the chat panel (for re-parenting to window).
func detach_chat_panel() -> CreativElixirChatPanel:
	if _chat_panel and _chat_panel.get_parent() == self:
		remove_child(_chat_panel)
	return _chat_panel


## Re-attach the chat panel (returning from window).
func attach_chat_panel(panel: CreativElixirChatPanel) -> void:
	_chat_panel = panel
	if _chat_panel.get_parent():
		_chat_panel.get_parent().remove_child(_chat_panel)
	add_child(_chat_panel)
	_chat_panel.set_docked(true)
