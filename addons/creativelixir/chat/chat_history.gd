@tool
class_name CreativElixirChatHistory
extends RefCounted

## Persists chat history to disk as JSON files.
## Each session gets its own file in .chat_history/ directory.

var _messages: Array = []  # Array of {"role", "content", "timestamp"}
var _session_file_path: String = ""
var _max_messages: int = CreativElixirConstants.MAX_CHAT_HISTORY_MESSAGES


func _init() -> void:
	_start_new_session()


## Start a new session (new file).
func _start_new_session() -> void:
	_ensure_history_dir()
	var time := Time.get_datetime_dict_from_system()
	var filename := "session_%04d%02d%02d_%02d%02d%02d.json" % [
		time["year"], time["month"], time["day"],
		time["hour"], time["minute"], time["second"],
	]
	_session_file_path = CreativElixirConstants.CHAT_HISTORY_DIR + filename


## Append a message and auto-save.
func append(role: String, content: String) -> void:
	var msg := {
		"role": role,
		"content": content,
		"timestamp": Time.get_datetime_string_from_system(),
	}
	_messages.append(msg)

	# Trim if over limit
	if _messages.size() > _max_messages * 2:
		_messages = _messages.slice(_messages.size() - _max_messages)

	_save()


## Get recent messages for API context.
func get_recent(count: int) -> Array:
	if _messages.size() <= count:
		return _messages.duplicate()
	return _messages.slice(_messages.size() - count)


## Get all messages.
func get_all() -> Array:
	return _messages.duplicate()


## Clear the current session.
func clear() -> void:
	_messages.clear()
	_save()


## Load the most recent session from disk.
func load_latest() -> void:
	_ensure_history_dir()

	var dir := DirAccess.open(CreativElixirConstants.CHAT_HISTORY_DIR)
	if not dir:
		return

	# Find all session files
	var files: PackedStringArray = []
	dir.list_dir_begin()
	var fname := dir.get_next()
	while not fname.is_empty():
		if fname.begins_with("session_") and fname.ends_with(".json"):
			files.append(fname)
		fname = dir.get_next()
	dir.list_dir_end()

	if files.is_empty():
		return

	# Sort and pick latest
	files.sort()
	var latest := files[files.size() - 1]
	var path := CreativElixirConstants.CHAT_HISTORY_DIR + latest

	var file := FileAccess.open(path, FileAccess.READ)
	if not file:
		return

	var json_str := file.get_as_text()
	var parsed = JSON.parse_string(json_str)
	if parsed is Array:
		_messages = parsed
		_session_file_path = path


## List all available session files.
func list_sessions() -> Array:
	_ensure_history_dir()
	var sessions: Array = []

	var dir := DirAccess.open(CreativElixirConstants.CHAT_HISTORY_DIR)
	if not dir:
		return sessions

	dir.list_dir_begin()
	var fname := dir.get_next()
	while not fname.is_empty():
		if fname.begins_with("session_") and fname.ends_with(".json"):
			sessions.append({
				"filename": fname,
				"path": CreativElixirConstants.CHAT_HISTORY_DIR + fname,
			})
		fname = dir.get_next()
	dir.list_dir_end()

	sessions.sort_custom(func(a, b): return a["filename"] > b["filename"])
	return sessions


## Load a specific session by file path.
func load_session(path: String) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if not file:
		return
	var json_str := file.get_as_text()
	var parsed = JSON.parse_string(json_str)
	if parsed is Array:
		_messages = parsed
		_session_file_path = path


# ── Private ───────────────────────────────────────────────────────

func _save() -> void:
	if _session_file_path.is_empty():
		return

	_ensure_history_dir()

	var file := FileAccess.open(_session_file_path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(_messages, "\t"))


func _ensure_history_dir() -> void:
	var dir_path := CreativElixirConstants.CHAT_HISTORY_DIR
	if not DirAccess.dir_exists_absolute(dir_path):
		DirAccess.make_dir_recursive_absolute(dir_path)
