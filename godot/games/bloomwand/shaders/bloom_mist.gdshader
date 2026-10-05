// Bloomwand mist (our own, CC BY-SA 4.0): soft banks lying in the hollows. A camera-facing card, UV.x across, UV.y up;
// tinted by the vertex colour; it thins at the top and the ends, drifts and curls slowly, and fades where it meets the
// ground (soft against the depth buffer) so it never shows a hard edge. Runs on `clock`.
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;

#include "res://games/bloomwand/shaders/bloom_noise.gdshaderinc"

uniform float clock = 0.0;
uniform float density = 0.45;
uniform float brightness = 1.0;
uniform float softness = 3.0;
uniform sampler2D depth_tex : hint_depth_texture, filter_linear;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float v = UV.y;
	float body = smoothstep(0.0, 0.25, v) * pow(clamp(1.0 - v, 0.0, 1.0), 1.6);
	float ends = smoothstep(0.0, 0.25, UV.x) * smoothstep(1.0, 0.75, UV.x);
	float n = bw_fbm(vec2(wpos.x * 0.06 + clock * 0.02, v * 1.5 + wpos.z * 0.03 - clock * 0.01), 4);
	float a = body * ends * smoothstep(0.25, 0.75, n) * density;
	float depth = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 vp = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
	float scene_z = -vp.z / vp.w;
	a *= clamp((scene_z + VERTEX.z) / softness, 0.0, 1.0);
	ALBEDO = COLOR.rgb * brightness;
	ALPHA = clamp(a, 0.0, 1.0);
}
