// Tinplate Turbo trackside board: a printed tin banner in two colours with a chequered border. Our own (CC BY-SA 4.0).
shader_type spatial;

uniform vec4 col_a : source_color = vec4(0.95, 0.85, 0.2, 1.0);
uniform vec4 col_b : source_color = vec4(0.15, 0.35, 0.85, 1.0);

void fragment() {
	vec2 uv = UV;
	float band = step(0.5, fract(uv.x * 3.0 + uv.y * 0.6));
	vec3 col = mix(col_a.rgb, col_b.rgb, band);
	float edge = step(uv.y, 0.12) + step(0.88, uv.y);
	float chk = mod(floor(uv.x * 40.0) + floor(uv.y * 8.0), 2.0);
	col = mix(col, vec3(chk * 0.9 + 0.05), edge);
	ALBEDO = col;
	ROUGHNESS = 0.35;
	METALLIC = 0.3;
}
