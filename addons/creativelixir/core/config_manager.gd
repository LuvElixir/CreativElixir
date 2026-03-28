@tool
class_name CreativElixirConfigManager
extends Node

## Manages plugin settings and API key storage.
## Non-sensitive settings → ProjectSettings
## API keys → encrypted ConfigFile in user://

var _keys_config := ConfigFile.new()
var _encryption_password: String


func _ready() -> void:
	# Derive per-project encryption password
	var project_path := ProjectSettings.globalize_path("res://")
	_encryption_password = (CreativElixirConstants.ENCRYPTION_SEED + project_path).md5_text()
	_load_keys()
	_register_project_settings()


# ── Project Settings ──────────────────────────────────────────────

func _register_project_settings() -> void:
	_register_setting(
		CreativElixirConstants.SETTING_PROVIDER,
		CreativElixirConstants.DEFAULT_PROVIDER,
		TYPE_STRING,
		PROPERTY_HINT_ENUM,
		"openai,anthropic"
	)
	_register_setting(
		CreativElixirConstants.SETTING_OPENAI_BASE_URL,
		CreativElixirConstants.DEFAULT_OPENAI_BASE_URL,
		TYPE_STRING
	)
	_register_setting(
		CreativElixirConstants.SETTING_OPENAI_MODEL,
		CreativElixirConstants.DEFAULT_OPENAI_MODEL,
		TYPE_STRING
	)
	_register_setting(
		CreativElixirConstants.SETTING_ANTHROPIC_BASE_URL,
		CreativElixirConstants.DEFAULT_ANTHROPIC_BASE_URL,
		TYPE_STRING
	)
	_register_setting(
		CreativElixirConstants.SETTING_ANTHROPIC_MODEL,
		CreativElixirConstants.DEFAULT_ANTHROPIC_MODEL,
		TYPE_STRING
	)


func _register_setting(key: String, default_value: Variant, type: int,
		hint: int = PROPERTY_HINT_NONE, hint_string: String = "") -> void:
	if not ProjectSettings.has_setting(key):
		ProjectSettings.set_setting(key, default_value)
	ProjectSettings.set_initial_value(key, default_value)
	if hint != PROPERTY_HINT_NONE:
		ProjectSettings.add_property_info({
			"name": key,
			"type": type,
			"hint": hint,
			"hint_string": hint_string,
		})


# ── Getters ───────────────────────────────────────────────────────

func get_active_provider() -> String:
	return ProjectSettings.get_setting(
		CreativElixirConstants.SETTING_PROVIDER,
		CreativElixirConstants.DEFAULT_PROVIDER
	)


func get_base_url(provider: String = "") -> String:
	if provider.is_empty():
		provider = get_active_provider()
	match provider:
		"openai":
			return ProjectSettings.get_setting(
				CreativElixirConstants.SETTING_OPENAI_BASE_URL,
				CreativElixirConstants.DEFAULT_OPENAI_BASE_URL
			)
		"anthropic":
			return ProjectSettings.get_setting(
				CreativElixirConstants.SETTING_ANTHROPIC_BASE_URL,
				CreativElixirConstants.DEFAULT_ANTHROPIC_BASE_URL
			)
	return ""


func get_model_name(provider: String = "") -> String:
	if provider.is_empty():
		provider = get_active_provider()
	match provider:
		"openai":
			return ProjectSettings.get_setting(
				CreativElixirConstants.SETTING_OPENAI_MODEL,
				CreativElixirConstants.DEFAULT_OPENAI_MODEL
			)
		"anthropic":
			return ProjectSettings.get_setting(
				CreativElixirConstants.SETTING_ANTHROPIC_MODEL,
				CreativElixirConstants.DEFAULT_ANTHROPIC_MODEL
			)
	return ""


func get_api_key(provider: String = "") -> String:
	if provider.is_empty():
		provider = get_active_provider()
	return _keys_config.get_value("keys", provider, "")


# ── Setters ───────────────────────────────────────────────────────

func set_provider(provider: String) -> void:
	ProjectSettings.set_setting(CreativElixirConstants.SETTING_PROVIDER, provider)


func set_base_url(provider: String, url: String) -> void:
	match provider:
		"openai":
			ProjectSettings.set_setting(CreativElixirConstants.SETTING_OPENAI_BASE_URL, url)
		"anthropic":
			ProjectSettings.set_setting(CreativElixirConstants.SETTING_ANTHROPIC_BASE_URL, url)


func set_model_name(provider: String, model: String) -> void:
	match provider:
		"openai":
			ProjectSettings.set_setting(CreativElixirConstants.SETTING_OPENAI_MODEL, model)
		"anthropic":
			ProjectSettings.set_setting(CreativElixirConstants.SETTING_ANTHROPIC_MODEL, model)


func set_api_key(provider: String, key: String) -> void:
	_keys_config.set_value("keys", provider, key)
	_save_keys()


# ── Encrypted Key Storage ─────────────────────────────────────────

func _load_keys() -> void:
	var path := CreativElixirConstants.KEYS_CONFIG_PATH
	if FileAccess.file_exists(path):
		var err := _keys_config.load_encrypted_pass(path, _encryption_password)
		if err != OK:
			push_warning("CreativElixir: Failed to load encrypted keys (err=%d). Starting fresh." % err)
			_keys_config = ConfigFile.new()


func _save_keys() -> void:
	var path := CreativElixirConstants.KEYS_CONFIG_PATH
	var err := _keys_config.save_encrypted_pass(path, _encryption_password)
	if err != OK:
		push_error("CreativElixir: Failed to save encrypted keys (err=%d)." % err)


# ── Project Style Memory ──────────────────────────────────────────

func get_project_style() -> Dictionary:
	var path := CreativElixirConstants.PROJECT_STYLE_PATH
	if not FileAccess.file_exists(path):
		return {}
	var file := FileAccess.open(path, FileAccess.READ)
	if not file:
		return {}
	var json_str := file.get_as_text()
	var parsed = JSON.parse_string(json_str)
	if parsed is Dictionary:
		return parsed
	return {}


func save_project_style(style: Dictionary) -> void:
	var path := CreativElixirConstants.PROJECT_STYLE_PATH
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(style, "\t"))
