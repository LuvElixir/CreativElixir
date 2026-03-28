@tool
class_name CreativElixirApiManager
extends Node

## Manages HTTP requests to LLM APIs.
## Selects the appropriate provider based on config and handles request lifecycle.

var _config: CreativElixirConfigManager
var _event_bus: CreativElixirEventBus
var _http_request: HTTPRequest
var _current_provider: CreativElixirLLMProvider
var _is_requesting := false


func _init(config: CreativElixirConfigManager = null, event_bus: CreativElixirEventBus = null) -> void:
	_config = config
	_event_bus = event_bus


func _ready() -> void:
	_http_request = HTTPRequest.new()
	_http_request.timeout = 120.0  # 2 minutes
	_http_request.use_threads = true
	add_child(_http_request)
	_http_request.request_completed.connect(_on_request_completed)


## Send a message to the active LLM provider.
## messages: Array of {"role": String, "content": String, "images": Array[Image]}
## system_prompt: The system prompt string
func send_message(messages: Array, system_prompt: String) -> void:
	if _is_requesting:
		if _event_bus:
			_event_bus.api_error.emit("A request is already in progress.")
		return

	# Build provider
	_current_provider = _create_provider()
	if not _current_provider:
		if _event_bus:
			_event_bus.api_error.emit("Failed to create LLM provider. Check your settings.")
		return

	# Check API key
	if _current_provider.api_key.is_empty():
		if _event_bus:
			_event_bus.api_error.emit("API key not set. Please configure it in Settings.")
		return

	# Build request
	var url := _current_provider.get_endpoint_url()
	var headers := _current_provider.build_request_headers()
	var body := _current_provider.build_request_body(messages, system_prompt)
	var body_json := JSON.stringify(body)

	_is_requesting = true
	if _event_bus:
		_event_bus.request_started.emit()

	var err := _http_request.request(url, headers, HTTPClient.METHOD_POST, body_json)
	if err != OK:
		_is_requesting = false
		if _event_bus:
			_event_bus.request_finished.emit()
			_event_bus.api_error.emit("HTTP request failed to start (err=%d)." % err)


func cancel_request() -> void:
	if _is_requesting:
		_http_request.cancel_request()
		_is_requesting = false
		if _event_bus:
			_event_bus.request_finished.emit()


func is_requesting() -> bool:
	return _is_requesting


## Test connection with a minimal request.
func test_connection(provider_name: String, base_url: String, api_key: String,
		model: String, callback: Callable) -> void:
	var provider := _create_provider_with(provider_name, base_url, api_key, model)
	if not provider:
		callback.call(false, "Invalid provider configuration.")
		return

	var test_messages := [{"role": "user", "content": "Hi. Reply with just 'OK'."}]
	var url := provider.get_endpoint_url()
	var headers := provider.build_request_headers()
	var body := provider.build_request_body(test_messages, "")
	var body_json := JSON.stringify(body)

	# Use a separate HTTPRequest for testing
	var test_http := HTTPRequest.new()
	test_http.timeout = 30.0
	test_http.use_threads = true
	add_child(test_http)

	test_http.request_completed.connect(
		func(result: int, code: int, _headers: PackedStringArray, body_bytes: PackedByteArray) -> void:
			test_http.queue_free()
			if result != HTTPRequest.RESULT_SUCCESS:
				callback.call(false, "Connection failed (result=%d)." % result)
				return
			if code < 200 or code >= 300:
				var parsed := provider.parse_response(body_bytes)
				callback.call(false, "HTTP %d: %s" % [code, parsed.get("error", "Unknown error")])
				return
			callback.call(true, "Connection successful!")
	)

	var err := test_http.request(url, headers, HTTPClient.METHOD_POST, body_json)
	if err != OK:
		test_http.queue_free()
		callback.call(false, "Failed to start request (err=%d)." % err)


# ── Private ───────────────────────────────────────────────────────

func _create_provider() -> CreativElixirLLMProvider:
	if not _config:
		return null
	var provider_name := _config.get_active_provider()
	var url := _config.get_base_url(provider_name)
	var key := _config.get_api_key(provider_name)
	var model := _config.get_model_name(provider_name)
	return _create_provider_with(provider_name, url, key, model)


func _create_provider_with(provider_name: String, url: String, key: String,
		model: String) -> CreativElixirLLMProvider:
	var provider: CreativElixirLLMProvider
	match provider_name:
		"openai":
			provider = CreativElixirOpenAIProvider.new()
		"anthropic":
			provider = CreativElixirAnthropicProvider.new()
		_:
			push_error("CreativElixir: Unknown provider '%s'" % provider_name)
			return null

	provider.base_url = url
	provider.api_key = key
	provider.model_name = model
	return provider


func _on_request_completed(result: int, response_code: int,
		_headers: PackedStringArray, body: PackedByteArray) -> void:
	_is_requesting = false

	if _event_bus:
		_event_bus.request_finished.emit()

	if result != HTTPRequest.RESULT_SUCCESS:
		var err_msg := "HTTP request failed (result=%d)." % result
		match result:
			HTTPRequest.RESULT_CANT_CONNECT:
				err_msg = "Cannot connect to server. Check your Base URL and network."
			HTTPRequest.RESULT_CANT_RESOLVE:
				err_msg = "Cannot resolve hostname. Check your Base URL."
			HTTPRequest.RESULT_CONNECTION_ERROR:
				err_msg = "Connection error. The server may be down."
			HTTPRequest.RESULT_TLS_HANDSHAKE_ERROR:
				err_msg = "TLS handshake failed. Check your Base URL protocol."
			HTTPRequest.RESULT_TIMEOUT:
				err_msg = "Request timed out. The model may be slow or the server is unresponsive."
		if _event_bus:
			_event_bus.api_error.emit(err_msg)
		return

	if not _current_provider:
		if _event_bus:
			_event_bus.api_error.emit("No active provider for response parsing.")
		return

	var parsed := _current_provider.parse_response(body)

	if not parsed.get("error", "").is_empty():
		if _event_bus:
			_event_bus.api_error.emit("API Error: " + parsed["error"])
		return

	if _event_bus:
		_event_bus.response_received.emit(parsed)
