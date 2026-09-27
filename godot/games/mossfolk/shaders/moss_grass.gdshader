shader_type spatial;
// Mossfolk grass tufts on the ledges (MossSlab's MultiMesh): dark at the root, bright at the tip, lit through from
// behind, swaying in a slow draught that rolls along the cave.

render_mode cull_disabled;

uniform vec3 base_col : source_color = vec3(0.12, 0.25, 0.08);
uniform vec3 tip_col : source_color = vec3(0.5, 0.85, 0.3);
uniform vec3 glow : source_color = vec3(0.55, 0.85, 1.0);

varying float tip;

void vertex() {
	tip = UV.y;
	vec3 wp = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float sway = sin(TIME * 1.4 + wp.x * 1.7 + wp.z * 0.9) * 0.6 + sin(TIME * 2.9 + wp.x * 4.1) * 0.25;
	VERTEX.x += sway * 0.025 * tip * tip;
	VERTEX.z += sway * 0.012 * tip * tip;
}

void fragment() {
	ALBEDO = mix(base_col, tip_col, smoothstep(0.0, 1.0, tip));
	ROUGHNESS = 0.6;
	SPECULAR = 0.3;
	BACKLIGHT = tip_col * 0.5 * tip;
	EMISSION = glow * 0.03 * tip * tip;
}
