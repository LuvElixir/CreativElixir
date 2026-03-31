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
func send_message(messages: Array, system_prompt: String) -> void:
	if _is_requesting:
		if _event_bus:
			_event_bus.api_error.emit("已有请求正在进行中。")
		return

	_current_provider = _create_provider()
	if not _current_provider:
		if _event_bus:
			_event_bus.api_error.emit("无法创建 LLM 提供者，请检查设置。")
		return

	if _current_provider.api_key.is_empty():
		if _event_bus:
			_event_bus.api_error.emit("未设置 API 密钥，请在设置中配置。")
		return

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
			_event_bus.api_error.emit("HTTP 请求启动失败 (err=%d)。" % err)


func cancel_request() -> void:
	if _is_requesting:
		_http_request.cancel_request()
		_is_requesting = false
		if _event_bus:
			_event_bus.request_finished.emit()


func is_requesting() -> bool:
	return _is_requesting


## Test connection with a minimal request.
func test_connection(api_format: String, base_url: String, api_key: String,
		model: String, callback: Callable) -> void:
	var provider := _create_provider_with(api_format, base_url, api_key, model)
	if not provider:
		callback.call(false, "无效的提供者配置。")
		return

	var test_messages := [{"role": "user", "content": "Hi. Reply with just 'OK'."}]
	var url := provider.get_endpoint_url()
	var headers := provider.build_request_headers()
	var body := provider.build_request_body(test_messages, "")
	var body_json := JSON.stringify(body)

	var test_http := HTTPRequest.new()
	test_http.timeout = 30.0
	test_http.use_threads = true
	add_child(test_http)

	test_http.request_completed.connect(
		func(result: int, code: int, _headers: PackedStringArray, body_bytes: PackedByteArray) -> void:
			test_http.queue_free()
			if result != HTTPRequest.RESULT_SUCCESS:
				callback.call(false, "连接失败 (result=%d)。" % result)
				return
			if code < 200 or code >= 300:
				var parsed := provider.parse_response(body_bytes)
				callback.call(false, "HTTP %d: %s" % [code, parsed.get("error", "未知错误")])
				return
			callback.call(true, "连接成功！")
	)

	var err := test_http.request(url, headers, HTTPClient.METHOD_POST, body_json)
	if err != OK:
		test_http.queue_free()
		callback.call(false, "请求启动失败 (err=%d)。" % err)


# ── Private ───────────────────────────────────────────────────────

func _create_provider() -> CreativElixirLLMProvider:
	if not _config:
		return null
	var api_format := _config.get_api_format()
	var url := _config.get_base_url()
	var key := _config.get_api_key()
	var model := _config.get_model_name()
	return _create_provider_with(api_format, url, key, model)


func _create_provider_with(api_format: String, url: String, key: String,
		model: String) -> CreativElixirLLMProvider:
	var provider: CreativElixirLLMProvider
	match api_format:
		"openai":
			provider = CreativElixirOpenAIProvider.new()
		"anthropic":
			provider = CreativElixirAnthropicProvider.new()
		_:
			push_error("CreativElixir: 未知的 API 格式 '%s'" % api_format)
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
		var err_msg := "HTTP 请求失败 (result=%d)。" % result
		match result:
			HTTPRequest.RESULT_CANT_CONNECT:
				err_msg = "无法连接到服务器，请检查接口地址和网络连接。"
			HTTPRequest.RESULT_CANT_RESOLVE:
				err_msg = "无法解析主机名，请检查接口地址。"
			HTTPRequest.RESULT_CONNECTION_ERROR:
				err_msg = "连接错误，服务器可能已关闭。"
			HTTPRequest.RESULT_TLS_HANDSHAKE_ERROR:
				err_msg = "TLS 握手失败，请检查接口地址协议。"
			HTTPRequest.RESULT_TIMEOUT:
				err_msg = "请求超时，模型可能响应较慢或服务器无响应。"
		if _event_bus:
			_event_bus.api_error.emit(err_msg)
		return

	if not _current_provider:
		if _event_bus:
			_event_bus.api_error.emit("没有活动的提供者用于解析响应。")
		return

	var parsed := _current_provider.parse_response(body)

	if not parsed.get("error", "").is_empty():
		if _event_bus:
			_event_bus.api_error.emit("API 错误: " + parsed["error"])
		return

	if _event_bus:
		_event_bus.response_received.emit(parsed)
