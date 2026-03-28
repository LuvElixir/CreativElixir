@tool
class_name CreativElixirModifyPropertyAction
extends CreativElixirActionBase

## Modifies a property on a node.
## params: {node_path: String, property: String, value: Variant}


func execute(undo_redo: EditorUndoRedoManager) -> Dictionary:
	var node_path: String = params.get("node_path", "")
	var property: String = params.get("property", "")
	var value = params.get("value")

	if node_path.is_empty():
		return {"success": false, "message": "No node_path specified."}
	if property.is_empty():
		return {"success": false, "message": "No property specified."}

	var target := CreativElixirActionBase.find_node_by_path(node_path)
	if not target:
		return {"success": false, "message": "Node not found: %s" % node_path}

	if not property in target:
		return {"success": false, "message": "Property '%s' not found on %s." % [property, node_path]}

	# Convert value
	value = _convert_value(target, property, value)

	var old_value = target.get(property)

	undo_redo.create_action("CreativElixir: Set %s.%s" % [target.name, property])
	undo_redo.add_do_property(target, property, value)
	undo_redo.add_undo_property(target, property, old_value)
	undo_redo.commit_action()

	return {"success": true, "message": "Set %s.%s = %s" % [target.name, property, str(value)]}


func _convert_value(node: Node, property: String, value) -> Variant:
	if value is Dictionary:
		if value.has("x") and value.has("y"):
			if value.has("z"):
				return Vector3(value["x"], value["y"], value["z"])
			return Vector2(value["x"], value["y"])
		if value.has("r") and value.has("g") and value.has("b"):
			return Color(value["r"], value["g"], value["b"], value.get("a", 1.0))

	if value is String and value.begins_with("res://"):
		var res := ResourceLoader.load(value)
		if res:
			return res

	return value
