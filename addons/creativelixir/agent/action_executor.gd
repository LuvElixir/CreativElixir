@tool
class_name CreativElixirActionExecutor
extends Node

## Executes parsed agent actions sequentially with UndoRedo support.
## All actions are wrapped in error handling to prevent editor crashes.

var _event_bus: CreativElixirEventBus
var _undo_redo: EditorUndoRedoManager


func _init(event_bus: CreativElixirEventBus = null,
		undo_redo: EditorUndoRedoManager = null) -> void:
	_event_bus = event_bus
	_undo_redo = undo_redo


## Execute all actions in sequence. Returns array of result dicts.
func execute_all(actions: Array) -> Array:
	var results: Array = []

	if not _undo_redo:
		push_error("CreativElixir: No EditorUndoRedoManager available.")
		if _event_bus:
			_event_bus.api_error.emit("Internal error: UndoRedo manager not available.")
		return results

	for action in actions:
		if not action is CreativElixirActionBase:
			continue

		var result := _execute_single(action)
		results.append(result)

		if _event_bus:
			_event_bus.action_executed.emit(
				action.type,
				result.get("success", false),
				result.get("message", "")
			)

		# Small delay between actions to let the editor process changes
		if is_inside_tree():
			await get_tree().process_frame

	if _event_bus and not results.is_empty():
		_event_bus.actions_completed.emit(results)

	return results


## Execute a single action with comprehensive error handling.
func _execute_single(action: CreativElixirActionBase) -> Dictionary:
	# Pre-flight safety checks
	if action.type in ["create_node", "delete_node", "modify_property", "save_scene"]:
		var scene_root := EditorInterface.get_edited_scene_root()
		if not scene_root:
			return {
				"success": false,
				"message": "No scene open. Cannot execute '%s'." % action.type,
			}

	# Validate the action has required params
	if action.type.is_empty():
		return {"success": false, "message": "Action has no type."}

	# Execute with error protection
	var result: Dictionary
	# GDScript doesn't have try/catch, so we rely on the action's own validation
	result = action.execute(_undo_redo)

	if result.is_empty():
		result = {"success": false, "message": "Action '%s' returned empty result." % action.type}

	return result
