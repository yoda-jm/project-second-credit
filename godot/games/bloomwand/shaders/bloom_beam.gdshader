// Bloomwand shafts of light (our own, CC BY-SA 4.0): sunbeams through the canopy, pale light through a crack in a
// cave. Additive; UV.x across the shaft, UV.y from its source (0) to its foot (1); soft at both ends and edges, slowly
// shimmering as leaves stir in the light's path. `color` times the vertex colour. Runs on `clock`.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

#include "res://games/bloomwand/shaders/bloom_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 color : source_color = vec3(1.0, 0.92, 0.7);
uniform float strength = 0.25;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float across = sin(UV.x * 3.14159);
	float ends = smoothstep(0.0, 0.15, UV.y) * pow(clamp(1.0 - UV.y, 0.0, 1.0), 1.3);
	float stir = 0.55 + 0.45 * bw_noise(vec2(wpos.x * 0.15 + clock * 0.13, wpos.z * 0.2 - clock * 0.07));
	float streak = 0.75 + 0.25 * bw_noise(vec2(UV.x * 6.0, UV.y * 0.8 - clock * 0.05));
	ALBEDO = color * COLOR.rgb * strength * across * across * ends * stir * streak;
}
