@tool
class_name CreativElixirChatWindow
extends Window

## Floating window that hosts the shared ChatPanel when popped out.

signal window_close_requested()

var _chat_panel: CreativElixirChatPanel


func _init() -> void:
	title = "CreativElixir"
	size = Vector2i(600, 800)
	min_size = Vector2i(400, 500)
	transient = true
	exclusive = false
	wrap_controls = true


func _ready() -> void:
	close_requested.connect(_on_close_requested)


func attach_chat_panel(panel: CreativElixirChatPanel) -> void:
	_chat_panel = panel
	if _chat_panel.get_parent():
		_chat_panel.get_parent().remove_child(_chat_panel)
	add_child(_chat_panel)
	_chat_panel.set_docked(false)


func detach_chat_panel() -> CreativElixirChatPanel:
	if _chat_panel and _chat_panel.get_parent() == self:
		remove_child(_chat_panel)
	return _chat_panel


func _on_close_requested() -> void:
	window_close_requested.emit()
