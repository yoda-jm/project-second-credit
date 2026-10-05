// Bloomwand waterfall (our own, CC BY-SA 4.0): a sheet of falling water, streaks racing down (UV.y runs down the
// fall), thinning to spray at its foot. Alpha-blended, lit by its own glow. Runs on `clock`.
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;

#include "res://games/bloomwand/shaders/bloom_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 color : source_color = vec3(0.95, 0.9, 1.0);
uniform vec3 shade : source_color = vec3(0.7, 0.75, 0.95);
uniform float speed = 0.35;

void fragment() {
	float across = smoothstep(0.0, 0.2, UV.x) * smoothstep(1.0, 0.8, UV.x);
	float s = bw_noise(vec2(UV.x * 18.0, UV.y * 3.0 - clock * speed * 4.0));
	float s2 = bw_noise(vec2(UV.x * 40.0 + 3.0, UV.y * 6.0 - clock * speed * 7.0));
	float streak = smoothstep(0.35, 0.8, s * 0.6 + s2 * 0.5);
	float foot = 1.0 - smoothstep(0.45, 1.0, UV.y);
	float spray = smoothstep(0.3, 0.9, UV.y) * bw_noise(vec2(UV.x * 8.0, UV.y * 10.0 - clock * 2.0)) * 0.5;
	ALBEDO = mix(shade, color, streak);
	ALPHA = clamp((0.35 + 0.6 * streak) * across * foot + spray * across, 0.0, 1.0) * 0.9;
}
