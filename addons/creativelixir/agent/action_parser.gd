@tool
class_name CreativElixirActionParser
extends RefCounted

## Parses LLM response text to extract structured actions.
## Actions are enclosed in ```actions ... ``` fenced blocks containing JSON arrays.

var _action_regex: RegEx


func _init() -> void:
	_action_regex = RegEx.new()
	# Match ```actions\n[...]\n``` blocks
	_action_regex.compile("```actions\\s*\\n([\\s\\S]*?)\\n\\s*```")


## Parse a response string into text + actions.
## Returns: {"text": String, "actions": Array[CreativElixirActionBase]}
func parse(response_text: String) -> Dictionary:
	var result := {"text": "", "actions": []}

	var matches := _action_regex.search_all(response_text)
	if matches.is_empty():
		result["text"] = response_text
		return result

	# Extract actions from all matched blocks
	for m in matches:
		var json_str: String = m.get_string(1).strip_edges()
		var actions := _parse_action_block(json_str)
		result["actions"].append_array(actions)

	# Text is everything outside the action blocks
	var clean_text := _action_regex.sub(response_text, "", true).strip_edges()
	result["text"] = clean_text

	return result


## Parse a single JSON action block into an array of actions.
func _parse_action_block(json_str: String) -> Array:
	var actions: Array = []

	var parsed = JSON.parse_string(json_str)
	if parsed == null:
		push_warning("CreativElixir: Failed to parse action JSON: %s" % json_str.substr(0, 200))
		return actions

	# Support both single action dict and array of actions
	var action_list: Array
	if parsed is Array:
		action_list = parsed
	elif parsed is Dictionary:
		action_list = [parsed]
	else:
		push_warning("CreativElixir: Action block is not a JSON array or object.")
		return actions

	for action_data in action_list:
		if not action_data is Dictionary:
			continue
		var action := _create_action(action_data)
		if action:
			actions.append(action)

	return actions


## Create a typed action instance from a data dictionary.
func _create_action(data: Dictionary) -> CreativElixirActionBase:
	var action_type: String = data.get("type", "")
	if action_type.is_empty():
		push_warning("CreativElixir: Action missing 'type' field.")
		return null

	var action: CreativElixirActionBase

	match action_type:
		"create_node":
			action = CreativElixirCreateNodeAction.new(action_type, data)
		"delete_node":
			action = CreativElixirDeleteNodeAction.new(action_type, data)
		"modify_property":
			action = CreativElixirModifyPropertyAction.new(action_type, data)
		"write_script":
			action = CreativElixirWriteScriptAction.new(action_type, data)
		"save_scene":
			action = CreativElixirSaveSceneAction.new(action_type, data)
		"generate_resource":
			action = CreativElixirGenerateResourceAction.new(action_type, data)
		_:
			push_warning("CreativElixir: Unknown action type '%s'." % action_type)
			return null

	return action
