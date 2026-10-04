// Lantern Links glass pipe: clear glass with light pulses running from its mouth to its exit (UV.x 0 at the mouth),
// so which way it goes reads at a glance. Our own shader (CC BY-SA 4.0).
shader_type spatial;
render_mode blend_mix, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec3 pulse_col : source_color = vec3(0.45, 0.9, 1.0);

void fragment() {
	float band = fract(UV.x * 4.0 - TIME * 0.9);
	float pulse = smoothstep(0.0, 0.08, band) * smoothstep(0.22, 0.08, band);
	ALBEDO = vec3(0.75, 0.9, 1.0);
	ROUGHNESS = 0.05;
	SPECULAR = 0.6;
	RIM = 0.25;
	EMISSION = pulse_col * pulse * 1.8;
	ALPHA = 0.1 + pulse * 0.35;
}
