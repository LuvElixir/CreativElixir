@tool
class_name CreativElixirPromptTemplates
extends RefCounted

## Platform-specific prompt templates for AI image generation tools.

enum Platform { MIDJOURNEY, SEEDREAM, NANO_BANANA, GENERIC }


## Get the display name for a platform.
static func get_platform_name(platform: int) -> String:
	match platform:
		Platform.MIDJOURNEY: return "Midjourney"
		Platform.SEEDREAM: return "即梦 Seedream"
		Platform.NANO_BANANA: return "Nano Banana"
		Platform.GENERIC: return "Generic"
	return "Unknown"


## Get all platform names as an array.
static func get_all_platform_names() -> PackedStringArray:
	return PackedStringArray([
		"Midjourney",
		"即梦 Seedream",
		"Nano Banana",
		"Generic",
	])


## Build a platform-specific prompt.
static func build_prompt(platform: int, description: String,
		style_profile: Dictionary, options: Dictionary = {}) -> String:
	match platform:
		Platform.MIDJOURNEY:
			return _build_midjourney(description, style_profile, options)
		Platform.SEEDREAM:
			return _build_seedream(description, style_profile, options)
		Platform.NANO_BANANA:
			return _build_nano_banana(description, style_profile, options)
		Platform.GENERIC:
			return _build_generic(description, style_profile, options)
	return description


# ── Midjourney ────────────────────────────────────────────────────

static func _build_midjourney(desc: String, style: Dictionary, opts: Dictionary) -> String:
	var parts: PackedStringArray = []

	parts.append(desc)

	# Style keywords
	var style_type: String = style.get("style", "")
	if not style_type.is_empty():
		parts.append(style_type + " style")

	if style.get("pixel_art", false):
		parts.append("pixel art")

	# Color palette
	var colors: Array = style.get("colors", [])
	if not colors.is_empty():
		parts.append("color palette: " + ", ".join(PackedStringArray(colors)))

	# Game asset defaults
	parts.append("game asset")

	var transparent: bool = opts.get("transparent_bg", true)
	if transparent:
		parts.append("transparent background")

	# Midjourney parameters
	var ar: String = opts.get("aspect_ratio", "1:1")
	var result := ", ".join(parts)
	result += " --ar %s" % ar

	if style.get("pixel_art", false):
		result += " --style raw"

	result += " --v 6.1"

	var quality: String = opts.get("quality", "")
	if not quality.is_empty():
		result += " --q %s" % quality

	return result


# ── 即梦 Seedream ─────────────────────────────────────────────────

static func _build_seedream(desc: String, style: Dictionary, opts: Dictionary) -> String:
	var parts: PackedStringArray = []

	parts.append(desc)

	var style_type: String = style.get("style", "")
	if not style_type.is_empty():
		parts.append(style_type + "风格")

	if style.get("pixel_art", false):
		parts.append("像素风")

	var colors: Array = style.get("colors", [])
	if not colors.is_empty():
		parts.append("配色方案: " + ", ".join(PackedStringArray(colors)))

	parts.append("游戏素材")
	parts.append("高质量")
	parts.append("细节丰富")

	var transparent: bool = opts.get("transparent_bg", true)
	if transparent:
		parts.append("透明背景")

	return ", ".join(parts)


# ── Nano Banana ───────────────────────────────────────────────────

static func _build_nano_banana(desc: String, style: Dictionary, opts: Dictionary) -> String:
	var parts: PackedStringArray = []

	parts.append(desc)

	var style_type: String = style.get("style", "")
	if not style_type.is_empty():
		parts.append(style_type)

	if style.get("pixel_art", false):
		parts.append("pixel art style")

	var colors: Array = style.get("colors", [])
	if not colors.is_empty():
		parts.append("using colors: " + ", ".join(PackedStringArray(colors)))

	parts.append("game sprite")
	parts.append("clean design")

	var transparent: bool = opts.get("transparent_bg", true)
	if transparent:
		parts.append("transparent background")

	return ", ".join(parts)


# ── Generic ───────────────────────────────────────────────────────

static func _build_generic(desc: String, style: Dictionary, _opts: Dictionary) -> String:
	var parts: PackedStringArray = []

	parts.append(desc)

	var style_type: String = style.get("style", "")
	if not style_type.is_empty():
		parts.append("in %s style" % style_type)

	if style.get("pixel_art", false):
		parts.append("pixel art")

	var colors: Array = style.get("colors", [])
	if not colors.is_empty():
		parts.append("color palette: " + ", ".join(PackedStringArray(colors)))

	parts.append("game asset, high quality")

	return ", ".join(parts)
