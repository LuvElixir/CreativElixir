@tool
class_name CreativElixirBatchVariant
extends RefCounted

## Generates batch variant prompts by combining a base prompt with variation axes.
## E.g., base="warrior character" + colors=[red,blue] + poses=[idle,attack]
## → 4 variants: red idle, red attack, blue idle, blue attack


## Generate all variant prompts from axes.
## base_prompt: The original prompt string
## axes: Array of {"name": String, "values": Array[String]}
## Returns: Array of {"prompt": String, "variant_label": String}
static func generate_variants(base_prompt: String, axes: Array) -> Array:
	if axes.is_empty():
		return [{"prompt": base_prompt, "variant_label": "original"}]

	# Build the Cartesian product of all axis values
	var combinations := _cartesian_product(axes)

	var results: Array = []
	for combo in combinations:
		# combo is Array of {"axis_name": String, "value": String}
		var modified_prompt := base_prompt
		var label_parts: PackedStringArray = []

		for entry in combo:
			var axis_name: String = entry["axis_name"]
			var value: String = entry["value"]
			label_parts.append("%s=%s" % [axis_name, value])

			# Insert the variant into the prompt
			modified_prompt += ", %s: %s" % [axis_name, value]

		results.append({
			"prompt": modified_prompt,
			"variant_label": ", ".join(label_parts),
		})

	return results


## Compute Cartesian product of axis values.
## Input: [{"name": "color", "values": ["red", "blue"]}, {"name": "pose", "values": ["idle", "run"]}]
## Output: [[{axis_name, value}, {axis_name, value}], ...]
static func _cartesian_product(axes: Array) -> Array:
	if axes.is_empty():
		return [[]]

	var first_axis: Dictionary = axes[0]
	var rest := axes.slice(1)
	var rest_combos := _cartesian_product(rest)

	var result: Array = []
	var axis_name: String = first_axis.get("name", "variant")
	var values: Array = first_axis.get("values", [])

	for value in values:
		for rest_combo in rest_combos:
			var new_combo: Array = [{"axis_name": axis_name, "value": str(value)}]
			new_combo.append_array(rest_combo)
			result.append(new_combo)

	return result
