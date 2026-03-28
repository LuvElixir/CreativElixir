@tool
class_name CreativElixirDeleteNodeAction
extends CreativElixirActionBase

## Deletes a node from the scene tree.
## params: {node_path: String}


func execute(undo_redo: EditorUndoRedoManager) -> Dictionary:
	var node_path: String = params.get("node_path", "")
	if node_path.is_empty():
		return {"success": false, "message": "No node_path specified."}

	var target := CreativElixirActionBase.find_node_by_path(node_path)
	if not target:
		return {"success": false, "message": "Node not found: %s" % node_path}

	var scene_root := EditorInterface.get_edited_scene_root()
	if target == scene_root:
		return {"success": false, "message": "Cannot delete the scene root node."}

	var parent := target.get_parent()
	if not parent:
		return {"success": false, "message": "Node has no parent."}

	var idx := target.get_index()

	undo_redo.create_action("CreativElixir: Delete %s" % target.name)
	undo_redo.add_do_method(parent, "remove_child", target)
	undo_redo.add_undo_method(parent, "add_child", target, true)
	undo_redo.add_undo_method(parent, "move_child", target, idx)
	undo_redo.add_undo_method(target, "set_owner", scene_root)
	undo_redo.add_undo_reference(target)
	undo_redo.commit_action()

	return {"success": true, "message": "Deleted %s" % node_path}
