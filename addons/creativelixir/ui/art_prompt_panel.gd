@tool
class_name CreativElixirArtPromptPanel
extends AcceptDialog

## Art Prompt Generator panel.
## Analyzes project style, generates platform-specific prompts,
## supports batch variants, reference image analysis, and placeholder generation.

var _config: CreativElixirConfigManager
var _event_bus: CreativElixirEventBus

# Style section
var _analyze_btn: Button
var _style_summary: RichTextLabel
var _ref_image_btn: Button
var _ref_image_path: String = ""

# Prompt section
var _description_input: TextEdit
var _platform_select: OptionButton
var _transparent_bg: CheckButton

# Variant section
var _variant_container: VBoxContainer
var _add_variant_btn: Button
var _variant_axes: Array = []  # Array of {name_edit: LineEdit, values_edit: LineEdit}

# Output section
var _prompt_output: TextEdit
var _copy_btn: Button
var _gen_all_btn: Button
var _placeholder_btn: Button
var _import_guide_btn: Button

# State
var _style_profile: Dictionary = {}
var _generated_prompts: Array = []


func _init() -> void:
	title = "CreativElixir — Art Prompt Generator"
	size = Vector2i(650, 750)
	ok_button_text = "Close"
	_build_ui()


func initialize(config: CreativElixirConfigManager,
		event_bus: CreativElixirEventBus) -> void:
	_config = config
	_event_bus = event_bus

	# Load cached style profile
	if _config:
		_style_profile = _config.get_project_style()
		if not _style_profile.is_empty():
			_update_style_display()


func _build_ui() -> void:
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED

	var main_vbox := VBoxContainer.new()
	main_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	main_vbox.add_theme_constant_override("separation", 10)
	scroll.add_child(main_vbox)
	add_child(scroll)

	# ── Style Analysis Section ──
	var style_label := Label.new()
	style_label.text = "--- Style Analysis ---"
	style_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	main_vbox.add_child(style_label)

	var style_hbox := HBoxContainer.new()
	style_hbox.add_theme_constant_override("separation", 8)
	main_vbox.add_child(style_hbox)

	_analyze_btn = Button.new()
	_analyze_btn.text = "Analyze Project Style"
	_analyze_btn.pressed.connect(_on_analyze_pressed)
	style_hbox.add_child(_analyze_btn)

	_ref_image_btn = Button.new()
	_ref_image_btn.text = "Load Reference Image..."
	_ref_image_btn.pressed.connect(_on_ref_image_pressed)
	style_hbox.add_child(_ref_image_btn)

	_style_summary = RichTextLabel.new()
	_style_summary.bbcode_enabled = true
	_style_summary.fit_content = true
	_style_summary.scroll_active = false
	_style_summary.custom_minimum_size.y = 60
	_style_summary.text = "(Click 'Analyze' to detect your project's art style)"
	main_vbox.add_child(_style_summary)

	main_vbox.add_child(HSeparator.new())

	# ── Description Section ──
	var desc_label := Label.new()
	desc_label.text = "Description (what you want to generate):"
	main_vbox.add_child(desc_label)

	_description_input = TextEdit.new()
	_description_input.custom_minimum_size.y = 80
	_description_input.placeholder_text = "e.g., a warrior character with a sword and shield, facing right, idle pose"
	_description_input.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	main_vbox.add_child(_description_input)

	# Platform + options
	var opts_hbox := HBoxContainer.new()
	opts_hbox.add_theme_constant_override("separation", 8)
	main_vbox.add_child(opts_hbox)

	var platform_label := Label.new()
	platform_label.text = "Platform:"
	opts_hbox.add_child(platform_label)

	_platform_select = OptionButton.new()
	for name in CreativElixirPromptTemplates.get_all_platform_names():
		_platform_select.add_item(name)
	opts_hbox.add_child(_platform_select)

	_transparent_bg = CheckButton.new()
	_transparent_bg.text = "Transparent BG"
	_transparent_bg.button_pressed = true
	opts_hbox.add_child(_transparent_bg)

	main_vbox.add_child(HSeparator.new())

	# ── Variant Section ──
	var variant_label := Label.new()
	variant_label.text = "--- Batch Variants (optional) ---"
	variant_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	main_vbox.add_child(variant_label)

	_variant_container = VBoxContainer.new()
	_variant_container.add_theme_constant_override("separation", 4)
	main_vbox.add_child(_variant_container)

	_add_variant_btn = Button.new()
	_add_variant_btn.text = "+ Add Variant Axis"
	_add_variant_btn.pressed.connect(_on_add_variant)
	main_vbox.add_child(_add_variant_btn)

	main_vbox.add_child(HSeparator.new())

	# ── Generate Buttons ──
	var gen_hbox := HBoxContainer.new()
	gen_hbox.add_theme_constant_override("separation", 8)
	main_vbox.add_child(gen_hbox)

	var gen_btn := Button.new()
	gen_btn.text = "Generate Prompt"
	gen_btn.pressed.connect(_on_generate_pressed)
	gen_hbox.add_child(gen_btn)

	_gen_all_btn = Button.new()
	_gen_all_btn.text = "Generate All Platforms"
	_gen_all_btn.pressed.connect(_on_generate_all_pressed)
	gen_hbox.add_child(_gen_all_btn)

	main_vbox.add_child(HSeparator.new())

	# ── Output Section ──
	var output_label := Label.new()
	output_label.text = "Generated Prompts:"
	main_vbox.add_child(output_label)

	_prompt_output = TextEdit.new()
	_prompt_output.custom_minimum_size.y = 150
	_prompt_output.editable = false
	_prompt_output.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	main_vbox.add_child(_prompt_output)

	var action_hbox := HBoxContainer.new()
	action_hbox.add_theme_constant_override("separation", 8)
	main_vbox.add_child(action_hbox)

	_copy_btn = Button.new()
	_copy_btn.text = "Copy All"
	_copy_btn.pressed.connect(_on_copy_pressed)
	action_hbox.add_child(_copy_btn)

	_placeholder_btn = Button.new()
	_placeholder_btn.text = "Generate Placeholder"
	_placeholder_btn.tooltip_text = "Create procedural Godot resources as placeholder art"
	_placeholder_btn.pressed.connect(_on_placeholder_pressed)
	action_hbox.add_child(_placeholder_btn)

	_import_guide_btn = Button.new()
	_import_guide_btn.text = "Import Guide"
	_import_guide_btn.tooltip_text = "Show Godot import workflow for this art style"
	_import_guide_btn.pressed.connect(_on_import_guide_pressed)
	action_hbox.add_child(_import_guide_btn)


# ── Event Handlers ────────────────────────────────────────────────

func _on_analyze_pressed() -> void:
	_analyze_btn.disabled = true
	_analyze_btn.text = "Analyzing..."

	# Run analysis (this is synchronous but fast)
	_style_profile = CreativElixirStyleAnalyzer.analyze_project()
	_update_style_display()

	# Cache the result
	if _config:
		_config.save_project_style(_style_profile)

	_analyze_btn.disabled = false
	_analyze_btn.text = "Analyze Project Style"


func _on_ref_image_pressed() -> void:
	# Open a file dialog to select a reference image
	var dialog := FileDialog.new()
	dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	dialog.access = FileDialog.ACCESS_FILESYSTEM
	dialog.filters = PackedStringArray(["*.png", "*.jpg", "*.jpeg", "*.webp", "*.svg"])
	dialog.title = "Select Reference Image"
	add_child(dialog)

	dialog.file_selected.connect(func(path: String) -> void:
		_ref_image_path = path
		var img := Image.load_from_file(path)
		if img:
			var ref_style := CreativElixirStyleAnalyzer.analyze_reference_image(img)
			# Merge reference colors into the style profile
			if _style_profile.is_empty():
				_style_profile = ref_style
			else:
				_style_profile["ref_image"] = ref_style
			_update_style_display()
		dialog.queue_free()
	)

	dialog.canceled.connect(func() -> void:
		dialog.queue_free()
	)

	dialog.popup_centered(Vector2i(500, 400))


func _on_generate_pressed() -> void:
	var desc := _description_input.text.strip_edges()
	if desc.is_empty():
		_prompt_output.text = "Please enter a description first."
		return

	var platform: int = _platform_select.selected
	var axes := _collect_variant_axes()
	var options := {"transparent_bg": _transparent_bg.button_pressed}

	_generated_prompts = CreativElixirPromptGenerator.generate(
		desc, platform, _style_profile, axes, options
	)
	_display_prompts()


func _on_generate_all_pressed() -> void:
	var desc := _description_input.text.strip_edges()
	if desc.is_empty():
		_prompt_output.text = "Please enter a description first."
		return

	var axes := _collect_variant_axes()
	var options := {"transparent_bg": _transparent_bg.button_pressed}

	_generated_prompts = CreativElixirPromptGenerator.generate_all_platforms(
		desc, _style_profile, axes, options
	)
	_display_prompts()


func _on_add_variant() -> void:
	var hbox := HBoxContainer.new()
	hbox.add_theme_constant_override("separation", 4)

	var name_edit := LineEdit.new()
	name_edit.placeholder_text = "Axis (e.g., color)"
	name_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hbox.add_child(name_edit)

	var values_edit := LineEdit.new()
	values_edit.placeholder_text = "Values (comma-separated: red, blue, green)"
	values_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hbox.add_child(values_edit)

	var remove_btn := Button.new()
	remove_btn.text = "×"
	remove_btn.pressed.connect(func() -> void:
		_variant_axes.erase({"name_edit": name_edit, "values_edit": values_edit})
		hbox.queue_free()
	)
	hbox.add_child(remove_btn)

	_variant_container.add_child(hbox)
	_variant_axes.append({"name_edit": name_edit, "values_edit": values_edit})


func _on_copy_pressed() -> void:
	var text := _prompt_output.text
	if not text.is_empty():
		DisplayServer.clipboard_set(text)


func _on_placeholder_pressed() -> void:
	var colors: Array = _style_profile.get("colors", ["#888888"])

	# Generate a gradient texture placeholder
	var tex := CreativElixirPlaceholderGenerator.generate_gradient_texture(
		colors, Vector2i(64, 64),
		"res://addons/creativelixir/generated/placeholder_gradient.tres"
	)

	# Generate a SpriteFrames placeholder
	var frames := CreativElixirPlaceholderGenerator.generate_sprite_frames(
		"idle", 4, colors, Vector2i(32, 32), 8.0,
		"res://addons/creativelixir/generated/placeholder_frames.tres"
	)

	_prompt_output.text += "\n\n--- Placeholders Generated ---\n"
	_prompt_output.text += "• GradientTexture2D → res://addons/creativelixir/generated/placeholder_gradient.tres\n"
	_prompt_output.text += "• SpriteFrames (4 frames) → res://addons/creativelixir/generated/placeholder_frames.tres\n"
	_prompt_output.text += "\nAssign these to your Sprite2D/AnimatedSprite2D nodes as temporary art."


func _on_import_guide_pressed() -> void:
	var guide := CreativElixirPromptGenerator.generate_import_guide(_style_profile)
	_prompt_output.text = guide


# ── Helpers ───────────────────────────────────────────────────────

func _update_style_display() -> void:
	var desc: String = _style_profile.get("description", "No analysis yet.")
	var colors: Array = _style_profile.get("colors", [])

	var bbcode := "[b]Style:[/b] %s\n" % _style_profile.get("style", "unknown")
	bbcode += "[b]Pixel Art:[/b] %s\n" % str(_style_profile.get("pixel_art", false))

	if not colors.is_empty():
		bbcode += "[b]Colors:[/b] "
		for c in colors:
			bbcode += "[bgcolor=%s]  [/bgcolor] %s  " % [c, c]
		bbcode += "\n"

	bbcode += desc

	if _style_profile.has("ref_image"):
		var ref: Dictionary = _style_profile["ref_image"]
		bbcode += "\n[b]Reference:[/b] %s" % ref.get("description", "")

	_style_summary.text = bbcode


func _collect_variant_axes() -> Array:
	var axes: Array = []
	for entry in _variant_axes:
		var name_edit: LineEdit = entry["name_edit"]
		var values_edit: LineEdit = entry["values_edit"]

		if not is_instance_valid(name_edit) or not is_instance_valid(values_edit):
			continue

		var axis_name := name_edit.text.strip_edges()
		var values_str := values_edit.text.strip_edges()
		if axis_name.is_empty() or values_str.is_empty():
			continue

		var values: Array = []
		for v in values_str.split(","):
			var trimmed := v.strip_edges()
			if not trimmed.is_empty():
				values.append(trimmed)

		if not values.is_empty():
			axes.append({"name": axis_name, "values": values})

	return axes


func _display_prompts() -> void:
	if _generated_prompts.is_empty():
		_prompt_output.text = "(No prompts generated)"
		return

	var text := ""
	for i in range(_generated_prompts.size()):
		var p: Dictionary = _generated_prompts[i]
		text += "=== %s [%s] ===\n" % [p.get("platform", ""), p.get("variant_label", "")]
		text += p.get("prompt", "") + "\n\n"

	_prompt_output.text = text.strip_edges()
