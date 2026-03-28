@tool
class_name CreativElixirPromptGenerator
extends RefCounted

## Generates optimized prompts for external AI image generation tools.
## Combines user description, project style profile, platform templates, and variant axes.


## Generate prompts for a single description.
## Returns: Array of {"prompt": String, "platform": String, "variant_label": String}
static func generate(description: String, platform: int,
		style_profile: Dictionary, variant_axes: Array = [],
		options: Dictionary = {}) -> Array:
	if description.strip_edges().is_empty():
		return []

	# Build the base prompt using platform template
	var base_prompt := CreativElixirPromptTemplates.build_prompt(
		platform, description, style_profile, options
	)

	# If no variant axes, return single prompt
	if variant_axes.is_empty():
		return [{
			"prompt": base_prompt,
			"platform": CreativElixirPromptTemplates.get_platform_name(platform),
			"variant_label": "original",
		}]

	# Generate variants
	var variants := CreativElixirBatchVariant.generate_variants(base_prompt, variant_axes)

	var results: Array = []
	for v in variants:
		results.append({
			"prompt": v["prompt"],
			"platform": CreativElixirPromptTemplates.get_platform_name(platform),
			"variant_label": v["variant_label"],
		})

	return results


## Generate prompts for ALL platforms at once.
static func generate_all_platforms(description: String,
		style_profile: Dictionary, variant_axes: Array = [],
		options: Dictionary = {}) -> Array:
	var all_results: Array = []

	for platform in [
		CreativElixirPromptTemplates.Platform.MIDJOURNEY,
		CreativElixirPromptTemplates.Platform.SEEDREAM,
		CreativElixirPromptTemplates.Platform.NANO_BANANA,
	]:
		var results := generate(description, platform, style_profile, variant_axes, options)
		all_results.append_array(results)

	return all_results


## Generate the Godot import workflow text for a given style.
static func generate_import_guide(style_profile: Dictionary) -> String:
	var guide := "## Godot Import Workflow\n\n"

	if style_profile.get("pixel_art", false):
		guide += "### Pixel Art Import Settings\n"
		guide += "1. Select your image in the FileSystem dock\n"
		guide += "2. Go to Import tab:\n"
		guide += "   - Filter: **Off** (Nearest neighbor)\n"
		guide += "   - Mipmaps: **Off**\n"
		guide += "   - Compress Mode: **Lossless**\n"
		guide += "3. Click **Reimport**\n\n"
	else:
		guide += "### Standard Import Settings\n"
		guide += "1. Select your image in the FileSystem dock\n"
		guide += "2. Go to Import tab:\n"
		guide += "   - Filter: **On** (Linear)\n"
		guide += "   - Mipmaps: **On** (for 3D or zooming)\n"
		guide += "   - Compress Mode: **VRAM Compressed** (for best performance)\n"
		guide += "3. Click **Reimport**\n\n"

	guide += "### SpriteFrames Setup (for animation)\n"
	guide += "```gdscript\n"
	guide += "# Create SpriteFrames programmatically\n"
	guide += "var frames = SpriteFrames.new()\n"
	guide += "frames.add_animation(\"idle\")\n"
	guide += "frames.set_animation_speed(\"idle\", 8.0)\n"
	guide += "frames.set_animation_loop(\"idle\", true)\n\n"
	guide += "# Add frames from spritesheet\n"
	guide += "var texture = load(\"res://sprites/character.png\")\n"
	guide += "var atlas = AtlasTexture.new()\n"
	guide += "atlas.atlas = texture\n"
	guide += "atlas.region = Rect2(0, 0, 32, 32)  # Adjust to frame size\n"
	guide += "frames.add_frame(\"idle\", atlas)\n\n"
	guide += "# Assign to AnimatedSprite2D\n"
	guide += "$AnimatedSprite2D.sprite_frames = frames\n"
	guide += "$AnimatedSprite2D.play(\"idle\")\n"
	guide += "```\n\n"

	guide += "### AnimationPlayer Integration\n"
	guide += "```gdscript\n"
	guide += "# Use AnimationPlayer for more complex animations\n"
	guide += "var anim = $AnimationPlayer\n"
	guide += "var animation = Animation.new()\n"
	guide += "animation.length = 1.0\n"
	guide += "animation.loop_mode = Animation.LOOP_LINEAR\n\n"
	guide += "var track_idx = animation.add_track(Animation.TYPE_VALUE)\n"
	guide += "animation.track_set_path(track_idx, \"Sprite2D:frame\")\n"
	guide += "animation.track_insert_key(track_idx, 0.0, 0)\n"
	guide += "animation.track_insert_key(track_idx, 0.5, 1)\n\n"
	guide += "var lib = anim.get_animation_library(\"\")\n"
	guide += "lib.add_animation(\"walk\", animation)\n"
	guide += "```\n"

	return guide
