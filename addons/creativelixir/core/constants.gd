@tool
class_name CreativElixirConstants
extends RefCounted

enum ContextMode { SMART, FULL_SCAN }
enum ActionType {
	CREATE_NODE,
	DELETE_NODE,
	MODIFY_PROPERTY,
	WRITE_SCRIPT,
	SAVE_SCENE,
	GENERATE_RESOURCE,
}

const PLUGIN_NAME := "CreativElixir"
const PLUGIN_VERSION := "0.1.0"

# Paths
const CHAT_HISTORY_DIR := "res://addons/creativelixir/.chat_history/"
const PROJECT_STYLE_PATH := "res://addons/creativelixir/.project_style.json"
const KEYS_CONFIG_PATH := "user://creativelixir_keys.cfg"

# Settings keys (stored in ProjectSettings) — unified, not per-provider
const SETTING_PREFIX := "addons/creativelixir/"
const SETTING_API_FORMAT := SETTING_PREFIX + "api_format"
const SETTING_BASE_URL := SETTING_PREFIX + "base_url"
const SETTING_MODEL := SETTING_PREFIX + "model"

# API format values
const FORMAT_OPENAI := "openai"
const FORMAT_ANTHROPIC := "anthropic"

# Defaults
const DEFAULT_OPENAI_BASE_URL := "https://api.openai.com"
const DEFAULT_OPENAI_MODEL := "gpt-4o"
const DEFAULT_ANTHROPIC_BASE_URL := "https://api.anthropic.com"
const DEFAULT_ANTHROPIC_MODEL := "claude-sonnet-4-20250514"
const DEFAULT_API_FORMAT := FORMAT_OPENAI

# Limits
const MAX_CONTEXT_TOKENS_SMART := 8000
const MAX_CONTEXT_TOKENS_FULL := 32000
const MAX_CHAT_HISTORY_MESSAGES := 50
const VIEWPORT_CAPTURE_MAX_DIM := 1024

# Encryption password seed (combined with project path for per-project encryption)
const ENCRYPTION_SEED := "CreativElixir_v0.1_KeyStore"
