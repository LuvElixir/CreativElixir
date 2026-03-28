@tool
class_name CreativElixirLLMProvider
extends RefCounted

## Abstract base class for LLM API providers.
## Subclasses implement specific API formats (OpenAI, Anthropic).

var base_url: String
var api_key: String
var model_name: String


func build_request_headers() -> PackedStringArray:
	push_error("CreativElixir: build_request_headers() not implemented")
	return PackedStringArray()


func build_request_body(messages: Array, system_prompt: String) -> Dictionary:
	push_error("CreativElixir: build_request_body() not implemented")
	return {}


func parse_response(response_body: PackedByteArray) -> Dictionary:
	## Returns: {"content": String, "error": String, "usage": Dictionary}
	push_error("CreativElixir: parse_response() not implemented")
	return {"content": "", "error": "Not implemented", "usage": {}}


func get_endpoint_url() -> String:
	push_error("CreativElixir: get_endpoint_url() not implemented")
	return ""


## Helper: encode an Image to base64 PNG string.
static func image_to_base64(image: Image) -> String:
	if not image:
		return ""
	var png_data := image.save_png_to_buffer()
	return Marshalls.raw_to_base64(png_data)
