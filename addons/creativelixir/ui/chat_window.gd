@tool
class_name CreativElixirChatWindow
extends Window

## 浮动窗口，弹出时承载共享的 ChatPanel。

signal window_close_requested()

var _chat_panel: CreativElixirChatPanel
var _margin: MarginContainer


func _init() -> void:
	title = "CreativElixir"
	size = Vector2i(600, 800)
	min_size = Vector2i(400, 500)
	transient = true
	exclusive = false
	wrap_controls = true

	_margin = MarginContainer.new()
	_margin.add_theme_constant_override("margin_left", 8)
	_margin.add_theme_constant_override("margin_right", 8)
	_margin.add_theme_constant_override("margin_top", 8)
	_margin.add_theme_constant_override("margin_bottom", 8)
	add_child(_margin)


func _ready() -> void:
	close_requested.connect(_on_close_requested)


func attach_chat_panel(panel: CreativElixirChatPanel) -> void:
	_chat_panel = panel
	if _chat_panel.get_parent():
		_chat_panel.get_parent().remove_child(_chat_panel)
	_margin.add_child(_chat_panel)
	_chat_panel.set_docked(false)


func detach_chat_panel() -> CreativElixirChatPanel:
	if _chat_panel and _chat_panel.get_parent() == _margin:
		_margin.remove_child(_chat_panel)
	return _chat_panel


func _on_close_requested() -> void:
	window_close_requested.emit()
