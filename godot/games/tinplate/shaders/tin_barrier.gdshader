// Tinplate Turbo barrier: a pressed-tin wall in alternating stripes, a rolled top edge catching the light. UV.y is
// metres along. Our own shader (CC BY-SA 4.0).
shader_type spatial;

uniform vec4 col_a : source_color = vec4(0.9, 0.9, 0.88, 1.0);
uniform vec4 col_b : source_color = vec4(0.85, 0.18, 0.15, 1.0);
uniform float glow = 0.0;

void fragment() {
	float s = step(0.5, fract(UV.y * 0.5));
	vec3 col = mix(col_a.rgb, col_b.rgb, s);
	col *= 0.85 + 0.15 * smoothstep(0.6, 1.0, UV.x);
	ALBEDO = col;
	ROUGHNESS = 0.3;
	METALLIC = 0.45;
	EMISSION = col_b.rgb * s * glow;
}
