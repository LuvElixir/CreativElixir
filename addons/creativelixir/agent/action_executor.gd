@tool
class_name CreativElixirActionExecutor
extends Node

## Executes parsed agent actions sequentially with UndoRedo support.

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

	if _event_bus and not results.is_empty():
		_event_bus.actions_completed.emit(results)

	return results


## Execute a single action with error handling.
func _execute_single(action: CreativElixirActionBase) -> Dictionary:
	# Safety checks
	if action.type in ["create_node", "delete_node", "modify_property", "save_scene"]:
		var scene_root := EditorInterface.get_edited_scene_root()
		if not scene_root:
			return {
				"success": false,
				"message": "No scene open. Cannot execute '%s'." % action.type,
			}

	var result := action.execute(_undo_redo)
	return result
