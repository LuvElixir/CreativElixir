@tool
class_name CreativElixirSaveSceneAction
extends CreativElixirActionBase

## Saves the current scene.
## params: {path: String (optional — if empty, saves to current scene path)}


func execute(_undo_redo: EditorUndoRedoManager) -> Dictionary:
	var scene_root := EditorInterface.get_edited_scene_root()
	if not scene_root:
		return {"success": false, "message": "No scene is open."}

	var save_path: String = params.get("path", "")
	if save_path.is_empty():
		save_path = scene_root.scene_file_path
	if save_path.is_empty():
		return {"success": false, "message": "Scene has no file path. Specify a path."}

	# Pack the scene
	var packed := PackedScene.new()
	var err := packed.pack(scene_root)
	if err != OK:
		return {"success": false, "message": "Failed to pack scene (err=%d)." % err}

	# Save
	err = ResourceSaver.save(packed, save_path)
	if err != OK:
		return {"success": false, "message": "Failed to save scene to %s (err=%d)." % [save_path, err]}

	EditorInterface.get_resource_filesystem().scan()

	return {"success": true, "message": "Scene saved to %s" % save_path}
