shader_type spatial;
render_mode specular_schlick_ggx, cull_disabled;
// Prism Breaker shards: glowing crystal splinters, coloured per instance (multimesh COLOR; alpha = heat).
varying vec4 col;

void vertex() {
	col = COLOR;
}

void fragment() {
	float nv = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	ALBEDO = col.rgb * 0.25;
	ROUGHNESS = 0.08;
	METALLIC = 0.3;
	EMISSION = col.rgb * (0.8 + col.a * 3.5) + col.rgb * pow(1.0 - nv, 2.0) * 1.5;
}
