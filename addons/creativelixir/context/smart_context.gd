@tool
class_name CreativElixirSmartContext
extends RefCounted

## Gathers context from the current editing session:
## - Scene tree structure
## - Currently open script
## - Selected node(s)
## - Recent output logs


## Gather smart context (current scene focus).
## Returns Dictionary with keys: scene_tree, current_script, selected_nodes, recent_logs
static func gather(log_reader = null) -> Dictionary:
	var context := {}

	# Scene tree
	var scene_root := EditorInterface.get_edited_scene_root()
	if scene_root:
		context["scene_tree"] = _serialize_scene_tree(scene_root, 0)
	else:
		context["scene_tree"] = "(no scene open)"

	# Current script
	var script_editor := EditorInterface.get_script_editor()
	if script_editor:
		var current_script := script_editor.get_current_script()
		if current_script:
			context["current_script"] = {
				"path": current_script.resource_path,
				"content": current_script.source_code,
			}

	# Selected nodes
	var selection := EditorInterface.get_selection()
	if selection:
		var selected := selection.get_selected_nodes()
		if not selected.is_empty():
			var node_descriptions: PackedStringArray = []
			for node in selected:
				node_descriptions.append(_describe_node(node))
			context["selected_nodes"] = "\n".join(node_descriptions)

	# Recent logs
	if log_reader and log_reader.has_method("get_recent_logs"):
		var logs: String = log_reader.get_recent_logs()
		if not logs.is_empty():
			context["recent_logs"] = logs

	return context


## Serialize the scene tree into a readable string.
static func _serialize_scene_tree(node: Node, depth: int) -> String:
	var indent := "  ".repeat(depth)
	var line := indent + node.name + " (" + node.get_class() + ")"

	# Add key properties for common node types
	var extras := _get_key_properties(node)
	if not extras.is_empty():
		line += " [" + extras + "]"

	var result := line
	for child in node.get_children():
		result += "\n" + _serialize_scene_tree(child, depth + 1)
	return result


## Get a brief description of a node including key properties.
static func _describe_node(node: Node) -> String:
	var desc := "%s (%s) at %s" % [node.name, node.get_class(), str(node.get_path())]

	# Add script info
	var script := node.get_script()
	if script and script is GDScript:
		desc += " — script: " + script.resource_path

	# Add key properties
	var extras := _get_key_properties(node)
	if not extras.is_empty():
		desc += " [" + extras + "]"

	return desc


## Extract key properties based on node type.
static func _get_key_properties(node: Node) -> String:
	var parts: PackedStringArray = []

	if node is Node2D:
		var n2d := node as Node2D
		if n2d.position != Vector2.ZERO:
			parts.append("pos=%s" % str(n2d.position))
		if n2d.scale != Vector2.ONE:
			parts.append("scale=%s" % str(n2d.scale))
		if n2d.rotation != 0.0:
			parts.append("rot=%.1f°" % rad_to_deg(n2d.rotation))

	if node is Node3D:
		var n3d := node as Node3D
		if n3d.position != Vector3.ZERO:
			parts.append("pos=%s" % str(n3d.position))

	if node is Sprite2D:
		var sprite := node as Sprite2D
		if sprite.texture:
			parts.append("tex=%s" % sprite.texture.resource_path)

	if node is AnimatedSprite2D:
		var anim := node as AnimatedSprite2D
		if anim.sprite_frames:
			parts.append("frames=%s" % anim.sprite_frames.resource_path)

	if node is CollisionShape2D:
		var col := node as CollisionShape2D
		if col.shape:
			parts.append("shape=%s" % col.shape.get_class())

	if node is TileMapLayer:
		parts.append("TileMapLayer")

	if node is Camera2D:
		var cam := node as Camera2D
		if cam.is_current():
			parts.append("current")

	if node is CharacterBody2D or node is RigidBody2D or node is StaticBody2D:
		parts.append("physics")

	# Script attached?
	var script := node.get_script()
	if script and script is GDScript:
		var path: String = script.resource_path
		if not path.is_empty():
			parts.append("script=%s" % path.get_file())

	return ", ".join(parts)
