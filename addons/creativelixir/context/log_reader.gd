@tool
class_name CreativElixirLogReader
extends Node

## Reads Godot output panel logs for context injection.
## Primary: find the Output panel's RichTextLabel in the editor UI.
## Fallback: read from user://logs/godot.log file.

const MAX_LOG_LINES := 100
const LOG_FILE_PATH := "user://logs/godot.log"

var _output_label: RichTextLabel
var _cached_logs: String = ""
var _last_read_length := 0


func _ready() -> void:
	# Try to find the Output panel's RichTextLabel
	call_deferred("_find_output_panel")


## Get recent log lines.
func get_recent_logs() -> String:
	# Try live reading first
	if is_instance_valid(_output_label):
		var full_text := _output_label.get_parsed_text()
		if full_text.length() > _last_read_length:
			_cached_logs = full_text
			_last_read_length = full_text.length()
		return _trim_to_recent(_cached_logs)

	# Fallback: read log file
	return _read_log_file()


## Get only error/warning lines from recent logs.
func get_recent_errors() -> String:
	var logs := get_recent_logs()
	if logs.is_empty():
		return ""

	var error_lines: PackedStringArray = []
	for line in logs.split("\n"):
		var lower := line.to_lower()
		if "error" in lower or "warning" in lower or "exception" in lower \
				or "traceback" in lower or "failed" in lower:
			error_lines.append(line)

	return "\n".join(error_lines)


## Try to find the Output panel RichTextLabel in the editor UI tree.
func _find_output_panel() -> void:
	var base := EditorInterface.get_base_control()
	if not base:
		return

	_output_label = _find_output_rich_text_label(base)
	if _output_label:
		pass  # Found it
	else:
		push_warning("CreativElixir: Could not find Output panel. Using log file fallback.")


## Recursively search for the Output panel's RichTextLabel.
## Heuristic: look for a RichTextLabel inside a VBoxContainer whose parent
## is likely named something with "Output" or "Log".
func _find_output_rich_text_label(node: Node, depth: int = 0) -> RichTextLabel:
	if depth > 15:
		return null

	# Check if this node looks like the output panel
	if node is RichTextLabel:
		var parent := node.get_parent()
		if parent:
			var parent_name := parent.name.to_lower()
			var grandparent := parent.get_parent()
			var gp_name := grandparent.name.to_lower() if grandparent else ""

			if "output" in parent_name or "log" in parent_name \
					or "output" in gp_name or "log" in gp_name:
				return node as RichTextLabel

	for child in node.get_children():
		var result := _find_output_rich_text_label(child, depth + 1)
		if result:
			return result

	return null


## Read the last N lines from the Godot log file.
func _read_log_file() -> String:
	if not FileAccess.file_exists(LOG_FILE_PATH):
		return ""

	var file := FileAccess.open(LOG_FILE_PATH, FileAccess.READ)
	if not file:
		return ""

	var content := file.get_as_text()
	return _trim_to_recent(content)


## Keep only the last MAX_LOG_LINES lines.
func _trim_to_recent(text: String) -> String:
	if text.is_empty():
		return ""

	var lines := text.split("\n")
	if lines.size() <= MAX_LOG_LINES:
		return text

	var start := lines.size() - MAX_LOG_LINES
	var recent := lines.slice(start)
	return "\n".join(recent)
