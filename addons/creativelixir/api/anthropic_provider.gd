@tool
class_name CreativElixirAnthropicProvider
extends CreativElixirLLMProvider

## Anthropic Messages API provider.
## Supports custom base_url for proxy/mirror services.

const ANTHROPIC_VERSION := "2023-06-01"


func get_endpoint_url() -> String:
	var url := base_url.rstrip("/")
	return url + "/v1/messages"


func build_request_headers() -> PackedStringArray:
	return PackedStringArray([
		"Content-Type: application/json",
		"x-api-key: " + api_key,
		"anthropic-version: " + ANTHROPIC_VERSION,
	])


func build_request_body(messages: Array, system_prompt: String) -> Dictionary:
	var api_messages: Array = []

	for msg in messages:
		api_messages.append(_format_message(msg))

	var body: Dictionary = {
		"model": model_name,
		"messages": api_messages,
		"max_tokens": 4096,
	}

	# Anthropic uses a separate "system" field, not a system message
	if not system_prompt.is_empty():
		body["system"] = system_prompt

	return body


func parse_response(response_body: PackedByteArray) -> Dictionary:
	var text := response_body.get_string_from_utf8()
	var parsed = JSON.parse_string(text)

	if not parsed is Dictionary:
		return {"content": "", "error": "Invalid JSON response", "usage": {}}

	# Check for API error
	if parsed.has("error"):
		var err_obj = parsed["error"]
		var err_msg: String = ""
		if err_obj is Dictionary:
			err_msg = err_obj.get("message", str(err_obj))
		else:
			err_msg = str(err_obj)
		return {"content": "", "error": err_msg, "usage": {}}

	# Extract content from content blocks
	var content := ""
	var content_blocks: Array = parsed.get("content", [])
	for block in content_blocks:
		if block is Dictionary and block.get("type") == "text":
			content += block.get("text", "")

	var usage: Dictionary = parsed.get("usage", {})

	return {"content": content, "error": "", "usage": usage}


## Format a message for Anthropic's API.
## Input msg format: {"role": String, "content": String, "images": Array[Image] (optional)}
func _format_message(msg: Dictionary) -> Dictionary:
	var role: String = msg.get("role", "user")
	var text: String = msg.get("content", "")
	var images: Array = msg.get("images", [])

	# Anthropic only supports "user" and "assistant" roles
	if role == "system":
		role = "user"

	# Simple text message
	if images.is_empty():
		return {"role": role, "content": text}

	# Multi-modal content blocks
	var content_parts: Array = []

	for image in images:
		if image is Image:
			var b64 := CreativElixirLLMProvider.image_to_base64(image)
			content_parts.append({
				"type": "image",
				"source": {
					"type": "base64",
					"media_type": "image/png",
					"data": b64,
				},
			})

	if not text.is_empty():
		content_parts.append({
			"type": "text",
			"text": text,
		})

	return {"role": role, "content": content_parts}
