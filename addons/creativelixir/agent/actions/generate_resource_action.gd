@tool
class_name CreativElixirGenerateResourceAction
extends CreativElixirActionBase

## Generates Godot resources (ShaderMaterial, GradientTexture2D, SpriteFrames, etc.)
## and optionally saves them as .tres files or assigns to nodes.
## params: {
##   resource_type: String,
##   save_path: String (optional),
##   node_path: String (optional — assign to this node),
##   node_property: String (optional — which property to assign to),
##   properties: Dictionary
## }


func execute(_undo_redo: EditorUndoRedoManager) -> Dictionary:
	var resource_type: String = params.get("resource_type", "")
	var save_path: String = params.get("save_path", "")
	var node_path: String = params.get("node_path", "")
	var node_property: String = params.get("node_property", "")
	var properties: Dictionary = params.get("properties", {})

	if resource_type.is_empty():
		return {"success": false, "message": "No resource_type specified."}

	# Validate the class exists and is a Resource
	if not ClassDB.class_exists(resource_type):
		return {"success": false, "message": "Unknown class: %s" % resource_type}
	if not ClassDB.is_parent_class(resource_type, "Resource"):
		return {"success": false, "message": "%s is not a Resource subclass." % resource_type}

	# Create the resource
	var resource: Resource = ClassDB.instantiate(resource_type)
	if not resource:
		return {"success": false, "message": "Failed to instantiate %s." % resource_type}

	# Apply properties
	for key in properties:
		if key in resource:
			var value = _convert_property(resource, key, properties[key])
			resource.set(key, value)

	# Save to file if path specified
	if not save_path.is_empty():
		if not save_path.begins_with("res://"):
			save_path = "res://" + save_path

		var dir_path := save_path.get_base_dir()
		if not DirAccess.dir_exists_absolute(dir_path):
			DirAccess.make_dir_recursive_absolute(dir_path)

		var err := ResourceSaver.save(resource, save_path)
		if err != OK:
			return {"success": false, "message": "Failed to save resource to %s (err=%d)." % [save_path, err]}
		EditorInterface.get_resource_filesystem().scan()

	# Assign to node if specified
	if not node_path.is_empty() and not node_property.is_empty():
		var target := CreativElixirActionBase.find_node_by_path(node_path)
		if target and node_property in target:
			target.set(node_property, resource)

	var msg := "Generated %s" % resource_type
	if not save_path.is_empty():
		msg += " → %s" % save_path
	if not node_path.is_empty():
		msg += " (assigned to %s.%s)" % [node_path, node_property]

	return {"success": true, "message": msg}


func _convert_property(resource: Resource, key: String, value) -> Variant:
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
