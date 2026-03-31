@tool
class_name CreativElixirOpenAIProvider
extends CreativElixirLLMProvider

## OpenAI-compatible API provider.
## Works with OpenAI, DeepSeek, Together, OpenRouter, etc. via custom base_url.


func get_endpoint_url() -> String:
	var url := base_url.rstrip("/")
	# If user already included /v1 in the base URL, don't duplicate it
	if url.ends_with("/v1"):
		return url + "/chat/completions"
	return url + "/v1/chat/completions"


func build_request_headers() -> PackedStringArray:
	return PackedStringArray([
		"Content-Type: application/json",
		"Authorization: Bearer " + api_key,
	])


func build_request_body(messages: Array, system_prompt: String) -> Dictionary:
	var api_messages: Array = []

	# System message
	if not system_prompt.is_empty():
		api_messages.append({
			"role": "system",
			"content": system_prompt,
		})

	# Conversation messages
	for msg in messages:
		api_messages.append(_format_message(msg))

	return {
		"model": model_name,
		"messages": api_messages,
		"temperature": 0.7,
		"max_tokens": 4096,
	}


func parse_response(response_body: PackedByteArray) -> Dictionary:
	var text := response_body.get_string_from_utf8()
	var parsed = JSON.parse_string(text)

	if not parsed is Dictionary:
		return {"content": "", "error": "无效的 JSON 响应", "usage": {}}

	# Check for API error
	if parsed.has("error"):
		var err_msg: String = ""
		if parsed["error"] is Dictionary:
			err_msg = parsed["error"].get("message", str(parsed["error"]))
		else:
			err_msg = str(parsed["error"])
		return {"content": "", "error": err_msg, "usage": {}}

	# Extract content
	var content := ""
	var choices: Array = parsed.get("choices", [])
	if choices.size() > 0:
		var message: Dictionary = choices[0].get("message", {})
		content = message.get("content", "")

	var usage: Dictionary = parsed.get("usage", {})

	return {"content": content, "error": "", "usage": usage}


## Format a message dict for the OpenAI API.
## Input msg format: {"role": String, "content": String, "images": Array[Image] (optional)}
func _format_message(msg: Dictionary) -> Dictionary:
	var role: String = msg.get("role", "user")
	var text: String = msg.get("content", "")
	var images: Array = msg.get("images", [])

	# If no images, simple text message
	if images.is_empty():
		return {"role": role, "content": text}

	# Multi-modal: content is an array of parts
	var content_parts: Array = []

	if not text.is_empty():
		content_parts.append({
			"type": "text",
			"text": text,
		})

	for image in images:
		if image is Image:
			var b64 := CreativElixirLLMProvider.image_to_base64(image)
			content_parts.append({
				"type": "image_url",
				"image_url": {
					"url": "data:image/png;base64," + b64,
					"detail": "auto",
				},
			})

	return {"role": role, "content": content_parts}
