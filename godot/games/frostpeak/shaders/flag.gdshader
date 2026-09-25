shader_type spatial;
render_mode cull_disabled;
// A three-stripe flag waving in the wind; the pole side (UV x = 0) stays still.

uniform vec3 c0 : source_color = vec3(0.8, 0.1, 0.15);
uniform vec3 c1 : source_color = vec3(1.0, 1.0, 1.0);
uniform vec3 c2 : source_color = vec3(0.1, 0.2, 0.6);

void vertex() {
	float w = UV.x;
	VERTEX.z += sin(TIME * 4.0 + VERTEX.x * 3.0) * 0.14 * w + sin(TIME * 7.3 + VERTEX.y * 4.0) * 0.03 * w;
}

void fragment() {
	float u = UV.x;
	vec3 c = u < 1.0 / 3.0 ? c0 : (u < 2.0 / 3.0 ? c1 : c2);
	float fold = 0.85 + 0.15 * sin(TIME * 4.0 + UV.x * 9.0);
	ALBEDO = c * fold;
	ROUGHNESS = 0.8;
}
