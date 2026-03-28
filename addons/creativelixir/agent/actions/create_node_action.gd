@tool
class_name CreativElixirCreateNodeAction
extends CreativElixirActionBase

## Creates a new node in the scene tree.
## params: {parent_path: String, node_class: String, name: String, properties: Dictionary}


func execute(undo_redo: EditorUndoRedoManager) -> Dictionary:
	var parent_path: String = params.get("parent_path", ".")
	var node_class: String = params.get("node_class", "")
	var node_name: String = params.get("name", node_class)
	var properties: Dictionary = params.get("properties", {})

	if node_class.is_empty():
		return {"success": false, "message": "No node_class specified."}

	# Validate the class exists
	if not ClassDB.class_exists(node_class):
		return {"success": false, "message": "Unknown class: %s" % node_class}

	# Ensure it's a Node subclass
	if not ClassDB.is_parent_class(node_class, "Node"):
		return {"success": false, "message": "%s is not a Node subclass." % node_class}

	var parent := CreativElixirActionBase.find_node_by_path(parent_path)
	if not parent:
		return {"success": false, "message": "Parent node not found: %s" % parent_path}

	var scene_root := EditorInterface.get_edited_scene_root()
	if not scene_root:
		return {"success": false, "message": "No scene is open."}

	# Create the node
	var new_node: Node = ClassDB.instantiate(node_class)
	if not new_node:
		return {"success": false, "message": "Failed to instantiate %s." % node_class}
	new_node.name = node_name

	# Use UndoRedo for reversibility
	undo_redo.create_action("CreativElixir: Create %s" % node_name)
	undo_redo.add_do_method(parent, "add_child", new_node, true)
	undo_redo.add_do_method(new_node, "set_owner", scene_root)
	undo_redo.add_do_reference(new_node)
	undo_redo.add_undo_method(parent, "remove_child", new_node)
	undo_redo.commit_action()

	# Apply properties after the node is in the tree
	_apply_properties(new_node, properties, undo_redo)

	return {"success": true, "message": "Created %s (%s)" % [node_name, node_class]}


func _apply_properties(node: Node, properties: Dictionary,
		undo_redo: EditorUndoRedoManager) -> void:
	if properties.is_empty():
		return

	for key in properties:
		var value = properties[key]
		value = _convert_value(node, key, value)

		if node.has_method("set") and key in node:
			undo_redo.create_action("CreativElixir: Set %s.%s" % [node.name, key])
			undo_redo.add_do_property(node, key, value)
			undo_redo.add_undo_property(node, key, node.get(key))
			undo_redo.commit_action()


## Convert JSON values to Godot types.
func _convert_value(node: Node, property: String, value) -> Variant:
	if value is Dictionary:
		# Try to convert {"x": ..., "y": ...} to Vector2
		if value.has("x") and value.has("y"):
			if value.has("z"):
				return Vector3(value["x"], value["y"], value["z"])
			return Vector2(value["x"], value["y"])
		# Try {"r": ..., "g": ..., "b": ...} to Color
		if value.has("r") and value.has("g") and value.has("b"):
			return Color(value["r"], value["g"], value["b"], value.get("a", 1.0))

	if value is String:
		# Check if it's a resource path
		if value.begins_with("res://"):
			var res := ResourceLoader.load(value)
			if res:
				return res

	return value
