@tool
class_name CreativElixirViewportCapture
extends RefCounted

## Captures the current editor viewport as an Image for Vision API.


## Capture the main editor viewport and return a resized Image.
static func capture() -> Image:
	# Try to get the editor's main viewport
	var viewport := EditorInterface.get_editor_viewport_2d()
	if not viewport:
		viewport = EditorInterface.get_editor_viewport_3d()
	if not viewport:
		# Fallback: get the base control's viewport
		var base := EditorInterface.get_base_control()
		if base:
			viewport = base.get_viewport()

	if not viewport:
		push_warning("CreativElixir: Could not capture viewport — no viewport found.")
		return null

	var texture := viewport.get_texture()
	if not texture:
		push_warning("CreativElixir: Viewport has no texture.")
		return null

	var image := texture.get_image()
	if not image:
		push_warning("CreativElixir: Could not get image from viewport texture.")
		return null

	# Resize to save tokens (max 1024px on longest side)
	_resize_to_max(image, CreativElixirConstants.VIEWPORT_CAPTURE_MAX_DIM)
	return image


## Capture a specific SubViewport by reference.
static func capture_subviewport(subviewport: SubViewport) -> Image:
	if not subviewport:
		return null
	var texture := subviewport.get_texture()
	if not texture:
		return null
	var image := texture.get_image()
	if image:
		_resize_to_max(image, CreativElixirConstants.VIEWPORT_CAPTURE_MAX_DIM)
	return image


## Resize image so the longest side does not exceed max_dim.
static func _resize_to_max(image: Image, max_dim: int) -> void:
	var w := image.get_width()
	var h := image.get_height()
	var longest := maxi(w, h)
	if longest <= max_dim:
		return
	var scale := float(max_dim) / float(longest)
	image.resize(int(w * scale), int(h * scale), Image.INTERPOLATE_BILINEAR)
