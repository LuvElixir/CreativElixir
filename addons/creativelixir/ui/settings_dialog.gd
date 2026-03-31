@tool
class_name CreativElixirSettingsDialog
extends AcceptDialog

## 设置对话框 — 配置 API 格式、接口地址、密钥和模型。
## 支持任何兼容 OpenAI 或 Anthropic API 格式的提供者。

signal settings_saved()

var _config: CreativElixirConfigManager
var _event_bus: CreativElixirEventBus
var _api_manager: CreativElixirApiManager

# UI elements
var _format_select: OptionButton
var _base_url_edit: LineEdit
var _api_key_edit: LineEdit
var _model_edit: LineEdit
var _test_btn: Button
var _test_label: Label


func _init() -> void:
	title = "CreativElixir 设置"
	size = Vector2i(520, 400)
	ok_button_text = "保存"
	_build_ui()


func initialize(config: CreativElixirConfigManager, event_bus: CreativElixirEventBus,
		api_manager: CreativElixirApiManager = null) -> void:
	_config = config
	_event_bus = event_bus
	_api_manager = api_manager
	_load_values()


func _build_ui() -> void:
	var main_vbox := VBoxContainer.new()
	main_vbox.add_theme_constant_override("separation", 12)

	# ── API Format selector ──
	var format_hbox := HBoxContainer.new()
	format_hbox.add_theme_constant_override("separation", 8)
	main_vbox.add_child(format_hbox)

	var format_label := Label.new()
	format_label.text = "API 格式:"
	format_label.custom_minimum_size.x = 80
	format_hbox.add_child(format_label)

	_format_select = OptionButton.new()
	_format_select.add_item("OpenAI 兼容", 0)
	_format_select.add_item("Anthropic 兼容", 1)
	_format_select.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_format_select.item_selected.connect(_on_format_changed)
	format_hbox.add_child(_format_select)

	var hint_label := Label.new()
	hint_label.text = "支持所有兼容 OpenAI / Anthropic API 格式的服务商（DeepSeek、OpenRouter、Together 等）"
	hint_label.add_theme_font_size_override("font_size", 11)
	hint_label.add_theme_color_override("font_color", Color(0.6, 0.6, 0.6))
	hint_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	main_vbox.add_child(hint_label)

	main_vbox.add_child(HSeparator.new())

	# ── Base URL ──
	var url_hbox := HBoxContainer.new()
	url_hbox.add_theme_constant_override("separation", 8)
	main_vbox.add_child(url_hbox)

	var url_label := Label.new()
	url_label.text = "接口地址:"
	url_label.custom_minimum_size.x = 80
	url_hbox.add_child(url_label)

	_base_url_edit = LineEdit.new()
	_base_url_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_base_url_edit.placeholder_text = CreativElixirConstants.DEFAULT_OPENAI_BASE_URL
	url_hbox.add_child(_base_url_edit)

	# ── API Key ──
	var key_hbox := HBoxContainer.new()
	key_hbox.add_theme_constant_override("separation", 8)
	main_vbox.add_child(key_hbox)

	var key_label := Label.new()
	key_label.text = "API 密钥:"
	key_label.custom_minimum_size.x = 80
	key_hbox.add_child(key_label)

	_api_key_edit = LineEdit.new()
	_api_key_edit.secret = true
	_api_key_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_api_key_edit.placeholder_text = "sk-..."
	key_hbox.add_child(_api_key_edit)

	# ── Model ──
	var model_hbox := HBoxContainer.new()
	model_hbox.add_theme_constant_override("separation", 8)
	main_vbox.add_child(model_hbox)

	var model_label := Label.new()
	model_label.text = "模型:"
	model_label.custom_minimum_size.x = 80
	model_hbox.add_child(model_label)

	_model_edit = LineEdit.new()
	_model_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_model_edit.placeholder_text = CreativElixirConstants.DEFAULT_OPENAI_MODEL
	model_hbox.add_child(_model_edit)

	# ── Test Connection ──
	main_vbox.add_child(HSeparator.new())

	var test_hbox := HBoxContainer.new()
	test_hbox.add_theme_constant_override("separation", 8)
	main_vbox.add_child(test_hbox)

	_test_btn = Button.new()
	_test_btn.text = "测试连接"
	_test_btn.custom_minimum_size.x = 100
	_test_btn.pressed.connect(_on_test_pressed)
	test_hbox.add_child(_test_btn)

	_test_label = Label.new()
	_test_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	test_hbox.add_child(_test_label)

	add_child(main_vbox)
	confirmed.connect(_on_confirmed)


func _on_format_changed(index: int) -> void:
	if index == 0:  # OpenAI
		_base_url_edit.placeholder_text = CreativElixirConstants.DEFAULT_OPENAI_BASE_URL
		_model_edit.placeholder_text = CreativElixirConstants.DEFAULT_OPENAI_MODEL
	else:  # Anthropic
		_base_url_edit.placeholder_text = CreativElixirConstants.DEFAULT_ANTHROPIC_BASE_URL
		_model_edit.placeholder_text = CreativElixirConstants.DEFAULT_ANTHROPIC_MODEL


func _load_values() -> void:
	if not _config:
		return

	var fmt := _config.get_api_format()
	_format_select.selected = 0 if fmt == "openai" else 1
	_on_format_changed(_format_select.selected)

	var url := _config.get_base_url()
	var default_url := CreativElixirConstants.DEFAULT_OPENAI_BASE_URL if fmt == "openai" \
		else CreativElixirConstants.DEFAULT_ANTHROPIC_BASE_URL
	_base_url_edit.text = url if url != default_url else ""

	_api_key_edit.text = _config.get_api_key()

	var model := _config.get_model_name()
	var default_model := CreativElixirConstants.DEFAULT_OPENAI_MODEL if fmt == "openai" \
		else CreativElixirConstants.DEFAULT_ANTHROPIC_MODEL
	_model_edit.text = model if model != default_model else ""


func _on_confirmed() -> void:
	if not _config:
		return

	var fmt := "openai" if _format_select.selected == 0 else "anthropic"
	_config.set_api_format(fmt)

	var url := _base_url_edit.text.strip_edges()
	if url.is_empty():
		url = CreativElixirConstants.DEFAULT_OPENAI_BASE_URL if fmt == "openai" \
			else CreativElixirConstants.DEFAULT_ANTHROPIC_BASE_URL
	_config.set_base_url(fmt, url)

	if not _api_key_edit.text.strip_edges().is_empty():
		_config.set_api_key(fmt, _api_key_edit.text.strip_edges())

	var model := _model_edit.text.strip_edges()
	if model.is_empty():
		model = CreativElixirConstants.DEFAULT_OPENAI_MODEL if fmt == "openai" \
			else CreativElixirConstants.DEFAULT_ANTHROPIC_MODEL
	_config.set_model_name(fmt, model)

	settings_saved.emit()
	if _event_bus:
		_event_bus.settings_changed.emit()


func _on_test_pressed() -> void:
	if not _config:
		return

	var fmt := "openai" if _format_select.selected == 0 else "anthropic"

	var url := _base_url_edit.text.strip_edges()
	if url.is_empty():
		url = CreativElixirConstants.DEFAULT_OPENAI_BASE_URL if fmt == "openai" \
			else CreativElixirConstants.DEFAULT_ANTHROPIC_BASE_URL

	var key := _api_key_edit.text.strip_edges()
	if key.is_empty():
		_test_label.text = "请先输入 API 密钥。"
		_test_label.add_theme_color_override("font_color", Color.ORANGE)
		return

	var model := _model_edit.text.strip_edges()
	if model.is_empty():
		model = CreativElixirConstants.DEFAULT_OPENAI_MODEL if fmt == "openai" \
			else CreativElixirConstants.DEFAULT_ANTHROPIC_MODEL

	_test_btn.disabled = true
	_test_label.text = "测试中..."
	_test_label.add_theme_color_override("font_color", Color.YELLOW)

	if not _api_manager:
		_test_label.text = "内部错误：未找到 API 管理器。"
		_test_label.add_theme_color_override("font_color", Color.RED)
		_test_btn.disabled = false
		return

	_api_manager.test_connection(fmt, url, key, model,
		func(success: bool, message: String) -> void:
			_test_btn.disabled = false
			_test_label.text = message
			if success:
				_test_label.add_theme_color_override("font_color", Color.GREEN)
			else:
				_test_label.add_theme_color_override("font_color", Color.RED)
	)
