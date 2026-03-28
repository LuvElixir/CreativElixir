@tool
class_name CreativElixirActionBase
extends RefCounted

## Base class for all agent actions.
## Each action represents an editor operation the AI can perform.

var type: String
var params: Dictionary


func _init(p_type: String = "", p_params: Dictionary = {}) -> void:
	type = p_type
	params = p_params


## Execute this action. Override in subclasses.
## Returns {"success": bool, "message": String}
func execute(undo_redo: EditorUndoRedoManager) -> Dictionary:
	return {"success": false, "message": "Action '%s' not implemented." % type}


## Helper: find a node by path relative to the scene root.
static func find_node_by_path(path: String) -> Node:
	var root := EditorInterface.get_edited_scene_root()
	if not root:
		return null
	if path == "." or path == root.name or path.is_empty():
		return root
	# Try as relative path from root
	var node := root.get_node_or_null(NodePath(path))
	if node:
		return node
	# Try matching by name in the tree
	return _find_by_name(root, path)


static func _find_by_name(node: Node, target_name: String) -> Node:
	if node.name == target_name:
		return node
	for child in node.get_children():
		var result := _find_by_name(child, target_name)
		if result:
			return result
	return null
