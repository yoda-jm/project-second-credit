shader_type spatial;
// Marble Drift: an aurora curtain (our own design, CC BY-SA 4.0). On a long ribbon (UV.x along it, UV.y 0 at the
// bottom edge .. 1 at the top): additive light, a bright green hem fading up to violet, fine vertical rays that
// shimmer and drift along the curtain, folds of brightness, soft ends.
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, fog_disabled, shadows_disabled;

#include "res://games/marbledrift/shaders/drift_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 low : source_color = vec3(0.25, 1.0, 0.55);
uniform vec3 high : source_color = vec3(0.6, 0.25, 1.0);
uniform float energy = 1.2;
uniform float seed = 0.0;

void fragment() {
	float u = UV.x;
	float v = UV.y;
	float rays = md_noise(vec2(u * 90.0 + clock * 0.4 + seed * 13.0, clock * 0.05)) * 0.6
			+ md_noise(vec2(u * 260.0 - clock * 0.7, seed)) * 0.4;
	float fold = 0.35 + 0.65 * md_fbm(vec2(u * 6.0 - clock * 0.03 + seed, clock * 0.02), 3);
	float hem = exp(-v * 7.0) * 1.5 + exp(-v * 2.2) * 0.6;
	float top = smoothstep(1.0, 0.45, v);
	float bottom = smoothstep(0.0, 0.04, v);
	float ends = smoothstep(0.0, 0.12, u) * smoothstep(1.0, 0.88, u);
	vec3 col = mix(low, high, smoothstep(0.1, 0.8, v));
	float a = (hem + 0.25) * top * bottom * ends * fold * (0.35 + 0.9 * rays * rays);
	ALBEDO = col * a * energy;
}
