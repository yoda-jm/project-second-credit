shader_type spatial;
render_mode specular_schlick_ggx;
// Gems: saturated body, bright fresnel rim and a travelling sparkle; emission feeds the glow.
uniform vec3 gem_color : source_color = vec3(0.2, 0.85, 1.0);
uniform float glow = 1.4;
varying vec3 world_pos;
void vertex() { world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	float sparkle = pow(max(0.0, sin(TIME * 3.0 + world_pos.x * 1.7 + world_pos.y * 2.3)), 24.0);
	ALBEDO = gem_color * 0.35;
	METALLIC = 0.2;
	ROUGHNESS = 0.08;
	SPECULAR = 1.0;
	EMISSION = gem_color * (glow * (0.35 + fres)) + vec3(1.0) * sparkle * 2.5;
}
