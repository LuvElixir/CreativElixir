@tool
class_name CreativElixirContextGatherer
extends Node

## Orchestrates context collection based on the selected mode (Smart or Full Scan).

var _log_reader: CreativElixirLogReader


func _ready() -> void:
	_log_reader = CreativElixirLogReader.new()
	_log_reader.name = "LogReader"
	add_child(_log_reader)


## Gather context based on mode.
func gather(mode: int) -> Dictionary:
	match mode:
		CreativElixirConstants.ContextMode.SMART:
			return CreativElixirSmartContext.gather(_log_reader)
		CreativElixirConstants.ContextMode.FULL_SCAN:
			return CreativElixirFullScanContext.gather(_log_reader)
		_:
			return CreativElixirSmartContext.gather(_log_reader)


## Get recent errors from the log reader (for auto-error detection).
func get_recent_errors() -> String:
	if _log_reader:
		return _log_reader.get_recent_errors()
	return ""
