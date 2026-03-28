@tool
class_name CreativElixirPlaceholderGenerator
extends RefCounted

## Generates procedural Godot resources as placeholder art.
## Creates ShaderMaterial, GradientTexture2D, Polygon2D shapes etc.
## that match the project's color palette.


## Generate a colored rectangle GradientTexture2D placeholder.
static func generate_gradient_texture(colors: Array, size: Vector2i = Vector2i(64, 64),
		save_path: String = "") -> GradientTexture2D:
	var gradient := Gradient.new()

	if colors.is_empty():
		gradient.set_color(0, Color.GRAY)
	elif colors.size() == 1:
		gradient.set_color(0, _parse_color(colors[0]))
	else:
		gradient.remove_point(0)
		for i in range(colors.size()):
			var offset := float(i) / float(colors.size() - 1)
			gradient.add_point(offset, _parse_color(colors[i]))

	var tex := GradientTexture2D.new()
	tex.gradient = gradient
	tex.width = size.x
	tex.height = size.y

	if not save_path.is_empty():
		_save_resource(tex, save_path)

	return tex


## Generate a solid color placeholder image and save as .png.
static func generate_solid_texture(color: Color, size: Vector2i = Vector2i(64, 64),
		save_path: String = "") -> ImageTexture:
	var image := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
	image.fill(color)

	var tex := ImageTexture.create_from_image(image)

	if not save_path.is_empty():
		# Save the image as PNG
		var png_path := save_path
		if not png_path.ends_with(".png"):
			png_path += ".png"
		image.save_png(png_path)
		EditorInterface.get_resource_filesystem().scan()

	return tex


## Generate a simple ShaderMaterial with a color fill.
static func generate_color_shader(color: Color,
		save_path: String = "") -> ShaderMaterial:
	var shader := Shader.new()
	shader.code = """
shader_type canvas_item;
uniform vec4 fill_color : source_color = vec4(%.3f, %.3f, %.3f, %.3f);

void fragment() {
	COLOR = fill_color;
}
""" % [color.r, color.g, color.b, color.a]

	var material := ShaderMaterial.new()
	material.shader = shader

	if not save_path.is_empty():
		_save_resource(material, save_path)

	return material


## Generate a simple Polygon2D shape as a placeholder silhouette.
## Returns the polygon points for a basic character shape.
static func generate_character_polygon(width: float = 32.0,
		height: float = 48.0) -> PackedVector2Array:
	# Simple humanoid silhouette
	var hw := width / 2.0
	var hh := height / 2.0
	return PackedVector2Array([
		# Head
		Vector2(-hw * 0.3, -hh),
		Vector2(hw * 0.3, -hh),
		Vector2(hw * 0.35, -hh * 0.7),
		# Shoulders
		Vector2(hw * 0.7, -hh * 0.5),
		Vector2(hw * 0.7, -hh * 0.2),
		# Right arm/side
		Vector2(hw * 0.4, -hh * 0.2),
		Vector2(hw * 0.4, hh * 0.3),
		# Right leg
		Vector2(hw * 0.35, hh * 0.3),
		Vector2(hw * 0.35, hh),
		Vector2(hw * 0.05, hh),
		# Left leg
		Vector2(hw * 0.05, hh * 0.3),
		Vector2(-hw * 0.05, hh * 0.3),
		Vector2(-hw * 0.05, hh),
		Vector2(-hw * 0.35, hh),
		Vector2(-hw * 0.35, hh * 0.3),
		# Left arm/side
		Vector2(-hw * 0.4, hh * 0.3),
		Vector2(-hw * 0.4, -hh * 0.2),
		Vector2(-hw * 0.7, -hh * 0.2),
		Vector2(-hw * 0.7, -hh * 0.5),
		# Back to head
		Vector2(-hw * 0.35, -hh * 0.7),
	])


## Generate a SpriteFrames resource with colored placeholder frames.
static func generate_sprite_frames(animation_name: String,
		frame_count: int, colors: Array, frame_size: Vector2i = Vector2i(32, 32),
		fps: float = 8.0, save_path: String = "") -> SpriteFrames:
	var frames := SpriteFrames.new()

	# Remove default animation and create our own
	if frames.has_animation("default"):
		frames.remove_animation("default")
	frames.add_animation(animation_name)
	frames.set_animation_speed(animation_name, fps)
	frames.set_animation_loop(animation_name, true)

	for i in range(frame_count):
		var color := _parse_color(colors[i % colors.size()]) if not colors.is_empty() else Color.GRAY
		# Slightly vary the color for each frame
		color = color.lightened(0.1 * sin(i * 0.5))

		var image := Image.create(frame_size.x, frame_size.y, false, Image.FORMAT_RGBA8)
		image.fill(color)

		# Add a simple frame indicator (darker border)
		var dark := color.darkened(0.3)
		for x in range(frame_size.x):
			image.set_pixel(x, 0, dark)
			image.set_pixel(x, frame_size.y - 1, dark)
		for y in range(frame_size.y):
			image.set_pixel(0, y, dark)
			image.set_pixel(frame_size.x - 1, y, dark)

		var tex := ImageTexture.create_from_image(image)
		frames.add_frame(animation_name, tex)

	if not save_path.is_empty():
		_save_resource(frames, save_path)

	return frames


# ── Helpers ───────────────────────────────────────────────────────

static func _parse_color(value) -> Color:
	if value is Color:
		return value
	if value is String:
		return Color.from_string(value, Color.GRAY)
	return Color.GRAY


static func _save_resource(resource: Resource, path: String) -> void:
	if not path.begins_with("res://"):
		path = "res://" + path

	var dir_path := path.get_base_dir()
	if not DirAccess.dir_exists_absolute(dir_path):
		DirAccess.make_dir_recursive_absolute(dir_path)

	var err := ResourceSaver.save(resource, path)
	if err != OK:
		push_error("CreativElixir: Failed to save resource to %s (err=%d)" % [path, err])
	else:
		EditorInterface.get_resource_filesystem().scan()
