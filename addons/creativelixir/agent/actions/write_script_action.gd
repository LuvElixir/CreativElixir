@tool
class_name CreativElixirWriteScriptAction
extends CreativElixirActionBase

## Writes or overwrites a .gd script file.
## params: {path: String, content: String}


func execute(_undo_redo: EditorUndoRedoManager) -> Dictionary:
	var file_path: String = params.get("path", "")
	var content: String = params.get("content", "")

	if file_path.is_empty():
		return {"success": false, "message": "No file path specified."}
	if content.is_empty():
		return {"success": false, "message": "No content specified."}

	# Ensure the path starts with res://
	if not file_path.begins_with("res://"):
		file_path = "res://" + file_path

	# Ensure directory exists
	var dir_path := file_path.get_base_dir()
	if not DirAccess.dir_exists_absolute(dir_path):
		var err := DirAccess.make_dir_recursive_absolute(dir_path)
		if err != OK:
			return {"success": false, "message": "Failed to create directory: %s" % dir_path}

	# Read existing content for potential undo info
	var old_content := ""
	var existed := FileAccess.file_exists(file_path)
	if existed:
		var old_file := FileAccess.open(file_path, FileAccess.READ)
		if old_file:
			old_content = old_file.get_as_text()

	# Write the file
	var file := FileAccess.open(file_path, FileAccess.WRITE)
	if not file:
		return {"success": false, "message": "Failed to open file for writing: %s (err=%d)" % [
			file_path, FileAccess.get_open_error()]}

	file.store_string(content)
	file.close()

	# Trigger resource filesystem rescan so the editor picks up changes
	EditorInterface.get_resource_filesystem().scan()

	var action := "Updated" if existed else "Created"
	return {"success": true, "message": "%s script: %s" % [action, file_path]}
