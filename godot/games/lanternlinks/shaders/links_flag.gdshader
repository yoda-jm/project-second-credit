// Lantern Links: the pin's pennant waves in the evening breeze (more towards its free end) and glows a little.
shader_type spatial;
render_mode cull_disabled;

uniform vec3 cloth : source_color = vec3(1.0, 0.78, 0.2);
uniform float glow = 0.0;

void vertex() {
	float along = clamp(VERTEX.x / 0.32, 0.0, 1.0);
	float w = sin(TIME * 5.0 - VERTEX.x * 18.0) * 0.035 + sin(TIME * 8.3 - VERTEX.x * 31.0) * 0.012;
	VERTEX.z += w * along;
	VERTEX.y -= along * along * 0.02;
}

void fragment() {
	ALBEDO = cloth * (0.85 + 0.15 * sin(UV.x * 40.0));
	ROUGHNESS = 0.8;
	EMISSION = cloth * glow;
	BACKLIGHT = cloth * 0.5;
}
