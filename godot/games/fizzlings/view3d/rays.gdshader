shader_type spatial;
// Fizzlings: god rays slanting down from the surface, slowly swaying and breathing. Additive, on a big quad.

render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform float time_s = 0.0;
uniform vec3 color : source_color = vec3(0.55, 0.85, 1.0);
uniform float strength = 0.22;
uniform float seed = 0.0;

float hash(float n) { return fract(sin(n) * 43758.5453); }

void fragment() {
	vec2 uv = UV;
	float down = uv.y;
	float x = uv.x + down * 0.22;  // slanted
	float acc = 0.0;
	for (int i = 0; i < 7; i++) {
		float fi = float(i) + seed;
		float cx = 0.08 + float(i) * 0.14 + sin(time_s * 0.13 + fi * 2.1) * 0.035;
		float w = 0.012 + hash(fi * 3.7) * 0.03 + down * 0.03;
		float beam = smoothstep(w, 0.0, abs(x - cx));
		float breathe = 0.55 + 0.45 * sin(time_s * (0.35 + hash(fi) * 0.4) + fi * 4.0);
		acc += beam * breathe * (0.5 + hash(fi * 1.3));
	}
	float fade = pow(1.0 - down, 1.6) * smoothstep(0.0, 0.06, down);
	ALBEDO = color * acc * fade * strength;
}
