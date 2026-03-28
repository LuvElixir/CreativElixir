@tool
class_name CreativElixirStyleAnalyzer
extends RefCounted

## Analyzes the project's existing art assets to determine visual style.
## Extracts dominant colors, detects pixel art vs other styles, and builds a style profile.

const SAMPLE_SIZE := 5
const DOWNSAMPLE_DIM := 32
const COLOR_CLUSTER_COUNT := 5

## Image extensions to scan for.
const IMAGE_EXTENSIONS := ["png", "jpg", "jpeg", "svg", "webp"]


## Analyze project art and return a style profile dictionary.
## Keys: colors (Array[String]), style (String), resolution_range (String),
## pixel_art (bool), description (String), sample_count (int)
static func analyze_project() -> Dictionary:
	var image_paths := _find_project_images()
	if image_paths.is_empty():
		return {
			"colors": [],
			"style": "unknown",
			"pixel_art": false,
			"resolution_range": "",
			"description": "No image assets found in project.",
			"sample_count": 0,
		}

	# Sample up to SAMPLE_SIZE images
	var samples := _load_sample_images(image_paths, SAMPLE_SIZE)
	if samples.is_empty():
		return {
			"colors": [],
			"style": "unknown",
			"pixel_art": false,
			"resolution_range": "",
			"description": "Could not load any project images.",
			"sample_count": 0,
		}

	# Extract dominant colors across all samples
	var all_colors: Array[Color] = []
	var widths: Array[int] = []
	var heights: Array[int] = []
	var is_pixel_art := false
	var pixel_art_votes := 0

	for entry in samples:
		var img: Image = entry["image"]
		widths.append(img.get_width())
		heights.append(img.get_height())

		# Detect pixel art
		if _is_likely_pixel_art(entry["path"], img):
			pixel_art_votes += 1

		# Extract colors
		var colors := _extract_dominant_colors(img)
		all_colors.append_array(colors)

	is_pixel_art = pixel_art_votes > samples.size() / 2

	# Cluster all collected colors down to final palette
	var palette := _cluster_colors(all_colors, COLOR_CLUSTER_COUNT)

	# Build resolution range string
	var min_w: int = widths.min()
	var max_w: int = widths.max()
	var min_h: int = heights.min()
	var max_h: int = heights.max()
	var res_range := "%dx%d ~ %dx%d" % [min_w, min_h, max_w, max_h]

	# Determine style label
	var style := "pixel art" if is_pixel_art else _guess_style(palette, max_w)

	# Convert palette to hex strings
	var color_hex: Array = []
	for c in palette:
		color_hex.append("#" + c.to_html(false))

	var description := "Detected %s style with %d sample images. " % [style, samples.size()]
	description += "Resolution range: %s. " % res_range
	description += "Dominant colors: %s." % ", ".join(PackedStringArray(color_hex))

	return {
		"colors": color_hex,
		"style": style,
		"pixel_art": is_pixel_art,
		"resolution_range": res_range,
		"description": description,
		"sample_count": samples.size(),
		"total_images": image_paths.size(),
	}


## Analyze a single reference image.
static func analyze_reference_image(image: Image) -> Dictionary:
	if not image:
		return {"colors": [], "style": "unknown", "description": "No image provided."}

	var colors := _extract_dominant_colors(image)
	var palette := _cluster_colors(colors, COLOR_CLUSTER_COUNT)
	var is_pixel := _is_likely_pixel_art("", image)
	var style := "pixel art" if is_pixel else _guess_style(palette, image.get_width())

	var color_hex: Array = []
	for c in palette:
		color_hex.append("#" + c.to_html(false))

	return {
		"colors": color_hex,
		"style": style,
		"pixel_art": is_pixel,
		"resolution": "%dx%d" % [image.get_width(), image.get_height()],
		"description": "%s style, %dx%d, colors: %s" % [
			style, image.get_width(), image.get_height(),
			", ".join(PackedStringArray(color_hex))
		],
	}


# ── Private ───────────────────────────────────────────────────────

static func _find_project_images() -> PackedStringArray:
	var paths: PackedStringArray = []
	_scan_dir("res://", paths)
	return paths


static func _scan_dir(path: String, results: PackedStringArray) -> void:
	var dir := DirAccess.open(path)
	if not dir:
		return
	dir.list_dir_begin()
	var fname := dir.get_next()
	while not fname.is_empty():
		var full := path.path_join(fname)
		if dir.current_is_dir():
			if not fname.begins_with(".") and fname != ".godot" \
					and full != "res://addons/creativelixir":
				_scan_dir(full, results)
		else:
			var ext := fname.get_extension().to_lower()
			if ext in IMAGE_EXTENSIONS:
				results.append(full)
		fname = dir.get_next()
	dir.list_dir_end()


static func _load_sample_images(paths: PackedStringArray, count: int) -> Array:
	var samples: Array = []
	# Spread samples evenly across the file list
	var step := maxi(1, paths.size() / count)
	var i := 0
	while samples.size() < count and i < paths.size():
		var img := Image.load_from_file(paths[i])
		if img:
			samples.append({"image": img, "path": paths[i]})
		i += step
	return samples


static func _is_likely_pixel_art(path: String, image: Image) -> bool:
	# Small dimensions strongly suggest pixel art
	if image.get_width() <= 128 and image.get_height() <= 128:
		return true
	if image.get_width() <= 256 and image.get_height() <= 256:
		# Check if import settings use NEAREST filter
		if not path.is_empty():
			var import_path := path + ".import"
			if FileAccess.file_exists(import_path):
				var file := FileAccess.open(import_path, FileAccess.READ)
				if file:
					var text := file.get_as_text()
					if "filter=false" in text or "NEAREST" in text.to_upper():
						return true
	return false


static func _extract_dominant_colors(image: Image) -> Array[Color]:
	# Downsample for faster processing
	var small := image.duplicate()
	small.resize(DOWNSAMPLE_DIM, DOWNSAMPLE_DIM, Image.INTERPOLATE_BILINEAR)

	var colors: Array[Color] = []
	for y in range(small.get_height()):
		for x in range(small.get_width()):
			var c := small.get_pixel(x, y)
			if c.a > 0.5:  # Ignore transparent pixels
				colors.append(c)
	return colors


## Simple color clustering: sort by hue, divide into buckets, average each.
static func _cluster_colors(colors: Array[Color], count: int) -> Array[Color]:
	if colors.is_empty():
		return []

	# Sort by hue
	var sorted := colors.duplicate()
	sorted.sort_custom(func(a: Color, b: Color) -> bool:
		return a.h < b.h
	)

	var bucket_size := maxi(1, sorted.size() / count)
	var clusters: Array[Color] = []

	for i in range(count):
		var start := i * bucket_size
		var end := mini(start + bucket_size, sorted.size())
		if start >= sorted.size():
			break

		var r_sum := 0.0
		var g_sum := 0.0
		var b_sum := 0.0
		var n := 0
		for j in range(start, end):
			r_sum += sorted[j].r
			g_sum += sorted[j].g
			b_sum += sorted[j].b
			n += 1

		if n > 0:
			clusters.append(Color(r_sum / n, g_sum / n, b_sum / n))

	return clusters


static func _guess_style(palette: Array[Color], max_dimension: int) -> String:
	# Heuristic guesses based on color saturation and image size
	if max_dimension <= 512:
		return "small-scale / icon"

	var avg_saturation := 0.0
	for c in palette:
		avg_saturation += c.s
	if not palette.is_empty():
		avg_saturation /= palette.size()

	if avg_saturation > 0.7:
		return "cartoon / vibrant"
	elif avg_saturation > 0.4:
		return "stylized"
	elif avg_saturation > 0.15:
		return "semi-realistic"
	else:
		return "realistic / muted"
