@tool
class_name CreativElixirCodeApplier
extends RefCounted

## Applies code blocks from chat to project files.
## Handles writing code to files and triggering editor reloads.


## Apply code to a file. If file_path is empty, try the currently open script.
static func apply(code: String, file_path: String = "") -> Dictionary:
	if code.strip_edges().is_empty():
		return {"success": false, "message": "No code to apply."}

	# If no path, try to get the current script path
	if file_path.is_empty():
		var script_editor := EditorInterface.get_script_editor()
		if script_editor:
			var current_script := script_editor.get_current_script()
			if current_script and not current_script.resource_path.is_empty():
				file_path = current_script.resource_path

	if file_path.is_empty():
		return {"success": false, "message": "No target file. Open a script first or specify a path."}

	# Ensure path starts with res://
	if not file_path.begins_with("res://"):
		file_path = "res://" + file_path

	# Ensure directory exists
	var dir_path := file_path.get_base_dir()
	if not DirAccess.dir_exists_absolute(dir_path):
		var err := DirAccess.make_dir_recursive_absolute(dir_path)
		if err != OK:
			return {"success": false, "message": "Cannot create directory: %s" % dir_path}

	# Write the file
	var file := FileAccess.open(file_path, FileAccess.WRITE)
	if not file:
		return {"success": false, "message": "Cannot open %s for writing." % file_path}

	file.store_string(code)
	file.close()

	# Trigger rescan
	EditorInterface.get_resource_filesystem().scan()

	return {"success": true, "message": "Code applied to %s" % file_path}
