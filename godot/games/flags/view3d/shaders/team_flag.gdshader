shader_type spatial;
render_mode cull_disabled;
// A territory flag in its owner's colour, with a pale chevron, waving in the wind; the pole side (UV x = 0) stays still.
uniform vec3 color : source_color = vec3(0.6);

void vertex() {
	float w = UV.x;
	VERTEX.z += sin(TIME * 5.0 + VERTEX.x * 5.0) * 0.08 * w + sin(TIME * 8.3 + VERTEX.y * 6.0) * 0.02 * w;
	VERTEX.y -= w * w * 0.05;
}

void fragment() {
	vec2 uv = UV;
	float chevron = step(abs(uv.y - 0.5) * 0.9 + 0.35, uv.x) * step(uv.x, abs(uv.y - 0.5) * 0.9 + 0.55);
	vec3 c = mix(color, vec3(0.95, 0.93, 0.85), chevron * 0.85);
	float fold = 0.8 + 0.2 * sin(TIME * 5.0 + UV.x * 10.0);
	ALBEDO = c * fold;
	EMISSION = color * 0.15;
	ROUGHNESS = 0.75;
}
