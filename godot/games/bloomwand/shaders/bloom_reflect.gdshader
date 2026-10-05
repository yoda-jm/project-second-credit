// Bloomwand reflections (our own, CC BY-SA 4.0): streaks of lantern light lying on water or ice under each lamp.
// Additive; UV.y from the light's foot (0) towards the viewer (1); `color` times the vertex colour. On ice
// (`ripple` low) they lie still and smooth; on water they shimmer and break up. Runs on `clock`.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

#include "res://games/bloomwand/shaders/bloom_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 color : source_color = vec3(1.0);
uniform float strength = 0.8;
uniform float ripple = 1.0;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float across = 1.0 - abs(UV.x * 2.0 - 1.0);
	float bands = 0.3 + 0.7 * smoothstep(0.3, 0.8, bw_noise(vec2(wpos.x * 0.8 + clock * 0.3, wpos.z * 5.0 - clock * 1.6)));
	float a = smoothstep(0.0, 0.7, across) * mix(1.0, bands, ripple) * pow(clamp(1.0 - UV.y, 0.0, 1.0), 1.4);
	ALBEDO = color * COLOR.rgb * a * strength;
}
