@tool
class_name CreativElixirFullScanContext
extends RefCounted

## Full project scan context for debugging hard problems.
## Includes everything from smart context plus all scripts, scenes, and file listings.


## Gather full project context.
static func gather(log_reader = null) -> Dictionary:
	# Start with smart context
	var context := CreativElixirSmartContext.gather(log_reader)

	# Add project file listing
	var all_files := _scan_project_files("res://")
	context["project_files"] = "\n".join(all_files)

	# Add all GDScript file contents (up to token limit)
	var scripts := _read_all_scripts(all_files)
	if not scripts.is_empty():
		context["all_scripts"] = scripts

	return context


## Recursively scan the project for relevant files.
static func _scan_project_files(path: String) -> PackedStringArray:
	var files: PackedStringArray = []
	var dir := DirAccess.open(path)
	if not dir:
		return files

	dir.list_dir_begin()
	var file_name := dir.get_next()
	while not file_name.is_empty():
		var full_path := path.path_join(file_name)

		if dir.current_is_dir():
			# Skip hidden dirs, .godot, and addons/creativelixir internals
			if not file_name.begins_with(".") and file_name != ".godot":
				if full_path != "res://addons/creativelixir/.chat_history":
					files.append_array(_scan_project_files(full_path))
		else:
			# Include relevant file types
			var ext := file_name.get_extension().to_lower()
			if ext in ["gd", "tscn", "tres", "cfg", "json", "shader", "gdshader"]:
				files.append(full_path)
			elif ext in ["png", "jpg", "jpeg", "svg", "webp", "ogg", "wav", "mp3"]:
				# Just list asset files (don't read content)
				files.append(full_path + " (asset)")

		file_name = dir.get_next()
	dir.list_dir_end()

	return files


## Read all GDScript files, sorted by relevance, truncated to token limit.
static func _read_all_scripts(all_files: PackedStringArray) -> Array:
	var scripts: Array = []
	var char_count := 0
	var max_chars: int = CreativElixirConstants.MAX_CONTEXT_TOKENS_FULL * 4  # Rough token-to-char ratio

	# Collect .gd files
	var gd_files: PackedStringArray = []
	for f in all_files:
		if f.ends_with(".gd"):
			gd_files.append(f)

	# Sort: prioritize non-addon scripts, then by path length (shorter = more important)
	var sorted_files := Array(gd_files)
	sorted_files.sort_custom(func(a: String, b: String) -> bool:
		var a_addon := a.begins_with("res://addons/")
		var b_addon := b.begins_with("res://addons/")
		if a_addon != b_addon:
			return not a_addon  # Non-addon first
		return a.length() < b.length()
	)

	for file_path in sorted_files:
		var file := FileAccess.open(file_path, FileAccess.READ)
		if not file:
			continue
		var content := file.get_as_text()

		# Check token budget
		if char_count + content.length() > max_chars:
			# Truncate this file
			var remaining := max_chars - char_count
			if remaining > 200:
				scripts.append({
					"path": file_path,
					"content": content.substr(0, remaining) + "\n... (truncated)",
				})
			break

		scripts.append({
			"path": file_path,
			"content": content,
		})
		char_count += content.length()

	return scripts
