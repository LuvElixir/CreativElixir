@tool
class_name CreativElixirSettingsDialog
extends AcceptDialog

## Settings dialog for configuring LLM providers, API keys, and models.

signal settings_saved()

var _config: CreativElixirConfigManager
var _event_bus: CreativElixirEventBus

# UI elements
var _tab_container: TabContainer
var _provider_select: OptionButton

# OpenAI tab
var _openai_base_url: LineEdit
var _openai_api_key: LineEdit
var _openai_model: LineEdit
var _openai_test_btn: Button
var _openai_test_label: Label

# Anthropic tab
var _anthropic_base_url: LineEdit
var _anthropic_api_key: LineEdit
var _anthropic_model: LineEdit
var _anthropic_test_btn: Button
var _anthropic_test_label: Label


func _init() -> void:
	title = "CreativElixir Settings"
	size = Vector2i(520, 480)
	_build_ui()


func initialize(config: CreativElixirConfigManager, event_bus: CreativElixirEventBus) -> void:
	_config = config
	_event_bus = event_bus
	_load_values()


func _build_ui() -> void:
	var main_vbox := VBoxContainer.new()
	main_vbox.add_theme_constant_override("separation", 12)

	# Active provider selector
	var provider_hbox := HBoxContainer.new()
	provider_hbox.add_theme_constant_override("separation", 8)
	main_vbox.add_child(provider_hbox)

	var provider_label := Label.new()
	provider_label.text = "Active Provider:"
	provider_hbox.add_child(provider_label)

	_provider_select = OptionButton.new()
	_provider_select.add_item("OpenAI Compatible", 0)
	_provider_select.add_item("Anthropic", 1)
	_provider_select.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	provider_hbox.add_child(_provider_select)

	# Tab container for provider configs
	_tab_container = TabContainer.new()
	_tab_container.size_flags_vertical = Control.SIZE_EXPAND_FILL
	main_vbox.add_child(_tab_container)

	# OpenAI tab
	var openai_tab := _build_provider_tab("openai")
	_tab_container.add_child(openai_tab)
	_tab_container.set_tab_title(0, "OpenAI Compatible")

	# Anthropic tab
	var anthropic_tab := _build_provider_tab("anthropic")
	_tab_container.add_child(anthropic_tab)
	_tab_container.set_tab_title(1, "Anthropic")

	add_child(main_vbox)

	# Connect the OK button
	confirmed.connect(_on_confirmed)


func _build_provider_tab(provider: String) -> VBoxContainer:
	var vbox := VBoxContainer.new()
	vbox.name = provider
	vbox.add_theme_constant_override("separation", 10)

	# Base URL
	var url_label := Label.new()
	url_label.text = "Base URL:"
	vbox.add_child(url_label)

	var url_edit := LineEdit.new()
	url_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vbox.add_child(url_edit)

	# API Key
	var key_label := Label.new()
	key_label.text = "API Key:"
	vbox.add_child(key_label)

	var key_edit := LineEdit.new()
	key_edit.secret = true
	key_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vbox.add_child(key_edit)

	# Model
	var model_label := Label.new()
	model_label.text = "Model:"
	vbox.add_child(model_label)

	var model_edit := LineEdit.new()
	model_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vbox.add_child(model_edit)

	# Test connection
	var test_hbox := HBoxContainer.new()
	test_hbox.add_theme_constant_override("separation", 8)
	vbox.add_child(test_hbox)

	var test_btn := Button.new()
	test_btn.text = "Test Connection"
	test_hbox.add_child(test_btn)

	var test_label := Label.new()
	test_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	test_hbox.add_child(test_label)

	# Store references
	match provider:
		"openai":
			_openai_base_url = url_edit
			_openai_api_key = key_edit
			_openai_model = model_edit
			_openai_test_btn = test_btn
			_openai_test_label = test_label
			url_edit.placeholder_text = CreativElixirConstants.DEFAULT_OPENAI_BASE_URL
			model_edit.placeholder_text = CreativElixirConstants.DEFAULT_OPENAI_MODEL
			test_btn.pressed.connect(_on_test_openai)
		"anthropic":
			_anthropic_base_url = url_edit
			_anthropic_api_key = key_edit
			_anthropic_model = model_edit
			_anthropic_test_btn = test_btn
			_anthropic_test_label = test_label
			url_edit.placeholder_text = CreativElixirConstants.DEFAULT_ANTHROPIC_BASE_URL
			model_edit.placeholder_text = CreativElixirConstants.DEFAULT_ANTHROPIC_MODEL
			test_btn.pressed.connect(_on_test_anthropic)

	return vbox


func _load_values() -> void:
	if not _config:
		return

	var active := _config.get_active_provider()
	_provider_select.selected = 0 if active == "openai" else 1

	# OpenAI
	var openai_url := _config.get_base_url("openai")
	_openai_base_url.text = openai_url if openai_url != CreativElixirConstants.DEFAULT_OPENAI_BASE_URL else ""
	_openai_api_key.text = _config.get_api_key("openai")
	var openai_model := _config.get_model_name("openai")
	_openai_model.text = openai_model if openai_model != CreativElixirConstants.DEFAULT_OPENAI_MODEL else ""

	# Anthropic
	var anthropic_url := _config.get_base_url("anthropic")
	_anthropic_base_url.text = anthropic_url if anthropic_url != CreativElixirConstants.DEFAULT_ANTHROPIC_BASE_URL else ""
	_anthropic_api_key.text = _config.get_api_key("anthropic")
	var anthropic_model := _config.get_model_name("anthropic")
	_anthropic_model.text = anthropic_model if anthropic_model != CreativElixirConstants.DEFAULT_ANTHROPIC_MODEL else ""


func _on_confirmed() -> void:
	if not _config:
		return

	# Save provider
	var provider := "openai" if _provider_select.selected == 0 else "anthropic"
	_config.set_provider(provider)

	# Save OpenAI settings
	var openai_url := _openai_base_url.text.strip_edges()
	if openai_url.is_empty():
		openai_url = CreativElixirConstants.DEFAULT_OPENAI_BASE_URL
	_config.set_base_url("openai", openai_url)

	if not _openai_api_key.text.strip_edges().is_empty():
		_config.set_api_key("openai", _openai_api_key.text.strip_edges())

	var openai_model := _openai_model.text.strip_edges()
	if openai_model.is_empty():
		openai_model = CreativElixirConstants.DEFAULT_OPENAI_MODEL
	_config.set_model_name("openai", openai_model)

	# Save Anthropic settings
	var anthropic_url := _anthropic_base_url.text.strip_edges()
	if anthropic_url.is_empty():
		anthropic_url = CreativElixirConstants.DEFAULT_ANTHROPIC_BASE_URL
	_config.set_base_url("anthropic", anthropic_url)

	if not _anthropic_api_key.text.strip_edges().is_empty():
		_config.set_api_key("anthropic", _anthropic_api_key.text.strip_edges())

	var anthropic_model := _anthropic_model.text.strip_edges()
	if anthropic_model.is_empty():
		anthropic_model = CreativElixirConstants.DEFAULT_ANTHROPIC_MODEL
	_config.set_model_name("anthropic", anthropic_model)

	settings_saved.emit()
	if _event_bus:
		_event_bus.settings_changed.emit()


func _on_test_openai() -> void:
	_test_provider("openai", _openai_base_url, _openai_api_key, _openai_model,
		_openai_test_btn, _openai_test_label)


func _on_test_anthropic() -> void:
	_test_provider("anthropic", _anthropic_base_url, _anthropic_api_key, _anthropic_model,
		_anthropic_test_btn, _anthropic_test_label)


func _test_provider(provider: String, url_edit: LineEdit, key_edit: LineEdit,
		model_edit: LineEdit, btn: Button, label: Label) -> void:
	if not _config:
		return

	var url := url_edit.text.strip_edges()
	if url.is_empty():
		match provider:
			"openai": url = CreativElixirConstants.DEFAULT_OPENAI_BASE_URL
			"anthropic": url = CreativElixirConstants.DEFAULT_ANTHROPIC_BASE_URL

	var key := key_edit.text.strip_edges()
	if key.is_empty():
		label.text = "Please enter an API key first."
		label.add_theme_color_override("font_color", Color.ORANGE)
		return

	var model := model_edit.text.strip_edges()
	if model.is_empty():
		match provider:
			"openai": model = CreativElixirConstants.DEFAULT_OPENAI_MODEL
			"anthropic": model = CreativElixirConstants.DEFAULT_ANTHROPIC_MODEL

	btn.disabled = true
	label.text = "Testing..."
	label.add_theme_color_override("font_color", Color.YELLOW)

	# We need an ApiManager for test — get it from the tree
	var api_manager := _find_api_manager()
	if not api_manager:
		label.text = "Internal error: API manager not found."
		label.add_theme_color_override("font_color", Color.RED)
		btn.disabled = false
		return

	api_manager.test_connection(provider, url, key, model,
		func(success: bool, message: String) -> void:
			btn.disabled = false
			label.text = message
			if success:
				label.add_theme_color_override("font_color", Color.GREEN)
			else:
				label.add_theme_color_override("font_color", Color.RED)
	)


func _find_api_manager() -> CreativElixirApiManager:
	# Walk up the tree to find the API manager
	var node := get_parent()
	while node:
		for child in node.get_children():
			if child is CreativElixirApiManager:
				return child
		node = node.get_parent()
	return null
