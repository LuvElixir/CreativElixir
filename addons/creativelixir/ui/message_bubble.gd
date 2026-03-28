@tool
class_name CreativElixirMessageBubble
extends PanelContainer

## A single chat message display with optional code-apply buttons.

signal copy_requested(code: String)
signal apply_requested(code: String, file_path: String)

var _role_label: Label
var _time_label: Label
var _content_label: RichTextLabel
var _action_bar: HBoxContainer
var _copy_button: Button
var _apply_button: Button

var _code_blocks: Array[Dictionary] = []  # [{code: String, language: String, path: String}]
var _is_user: bool = false


func _init() -> void:
	_build_ui()


func setup(role: String, content: String, timestamp: String = "") -> void:
	_is_user = (role == "user")
	_role_label.text = "You" if _is_user else "CreativElixir"

	if timestamp.is_empty():
		var time := Time.get_datetime_dict_from_system()
		timestamp = "%02d:%02d" % [time["hour"], time["minute"]]
	_time_label.text = timestamp

	# Parse content for code blocks and format
	_set_content(content)

	# Style based on role
	if _is_user:
		_role_label.add_theme_color_override("font_color", Color(0.5, 0.8, 1.0))
	else:
		_role_label.add_theme_color_override("font_color", Color(0.5, 1.0, 0.7))

	# Show action bar only for assistant messages with code blocks
	_action_bar.visible = not _is_user and not _code_blocks.is_empty()


func _build_ui() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 4)
	add_child(vbox)

	# Header
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 8)
	vbox.add_child(header)

	_role_label = Label.new()
	_role_label.add_theme_font_size_override("font_size", 13)
	header.add_child(_role_label)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(spacer)

	_time_label = Label.new()
	_time_label.add_theme_font_size_override("font_size", 11)
	_time_label.add_theme_color_override("font_color", Color(0.6, 0.6, 0.6))
	header.add_child(_time_label)

	# Content
	_content_label = RichTextLabel.new()
	_content_label.bbcode_enabled = true
	_content_label.fit_content = true
	_content_label.scroll_active = false
	_content_label.selection_enabled = true
	_content_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vbox.add_child(_content_label)

	# Action bar
	_action_bar = HBoxContainer.new()
	_action_bar.visible = false
	_action_bar.add_theme_constant_override("separation", 8)
	_action_bar.alignment = BoxContainer.ALIGNMENT_END
	vbox.add_child(_action_bar)

	_copy_button = Button.new()
	_copy_button.text = "Copy Code"
	_copy_button.pressed.connect(_on_copy_pressed)
	_action_bar.add_child(_copy_button)

	_apply_button = Button.new()
	_apply_button.text = "Apply Code"
	_apply_button.pressed.connect(_on_apply_pressed)
	_action_bar.add_child(_apply_button)


func _set_content(content: String) -> void:
	_code_blocks.clear()

	# Convert markdown-style code blocks to BBCode
	var bbcode := _markdown_to_bbcode(content)
	_content_label.text = bbcode


func _markdown_to_bbcode(text: String) -> String:
	var result := ""
	var lines := text.split("\n")
	var in_code_block := false
	var code_buffer := ""
	var code_lang := ""
	var i := 0

	while i < lines.size():
		var line: String = lines[i]

		if not in_code_block and line.strip_edges().begins_with("```"):
			# Start of code block
			in_code_block = true
			code_lang = line.strip_edges().substr(3).strip_edges()
			# Skip "actions" blocks for display too — they are functional blocks
			code_buffer = ""
			result += "[bgcolor=#1e1e2e][code]"
			i += 1
			continue

		if in_code_block and line.strip_edges() == "```":
			# End of code block
			in_code_block = false
			result += "[/code][/bgcolor]\n"

			# Store the code block for copy/apply
			if not code_buffer.strip_edges().is_empty():
				_code_blocks.append({
					"code": code_buffer.strip_edges(),
					"language": code_lang,
				})
			code_buffer = ""
			code_lang = ""
			i += 1
			continue

		if in_code_block:
			code_buffer += line + "\n"
			result += line + "\n"
		else:
			# Basic markdown formatting
			var formatted := line
			# Bold **text**
			formatted = _replace_pattern(formatted, "**", "[b]", "[/b]")
			# Inline code `text`
			formatted = _replace_pattern(formatted, "`", "[code]", "[/code]")
			result += formatted + "\n"

		i += 1

	# Handle unclosed code block
	if in_code_block:
		result += "[/code][/bgcolor]\n"
		if not code_buffer.strip_edges().is_empty():
			_code_blocks.append({
				"code": code_buffer.strip_edges(),
				"language": code_lang,
			})

	return result.strip_edges()


func _replace_pattern(text: String, marker: String, open_tag: String, close_tag: String) -> String:
	var result := ""
	var parts := text.split(marker)
	for j in range(parts.size()):
		result += parts[j]
		if j < parts.size() - 1:
			if j % 2 == 0:
				result += open_tag
			else:
				result += close_tag
	return result


func _on_copy_pressed() -> void:
	if _code_blocks.is_empty():
		return
	# Copy the first code block (or all concatenated)
	var all_code := ""
	for block in _code_blocks:
		if not all_code.is_empty():
			all_code += "\n\n"
		all_code += block["code"]
	DisplayServer.clipboard_set(all_code)
	copy_requested.emit(all_code)


func _on_apply_pressed() -> void:
	if _code_blocks.is_empty():
		return
	var block: Dictionary = _code_blocks[0]
	apply_requested.emit(block.get("code", ""), block.get("path", ""))
