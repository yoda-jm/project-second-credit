shader_type spatial;
// Light shafts from the low sun: a full-screen pass that marches from each pixel towards the sun on screen and
// gathers the bright sky it sees (ridges, towers and trees block it), so beams fan out past whatever stands in
// front of the sun. Forward+ only (reads the depth buffer, reversed: the sky is at 0).
render_mode unshaded, blend_add, depth_test_disabled, depth_draw_never, cull_disabled, fog_disabled, shadows_disabled;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform vec2 sun_uv = vec2(0.5, 0.2);
uniform float strength = 0.0;
uniform vec3 tint : source_color = vec3(1.0, 0.86, 0.62);

void vertex() {
	POSITION = vec4(VERTEX.xy * 2.0, 0.5, 1.0);
}

void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 to_sun = sun_uv - uv;
	const int N = 48;
	vec2 stp = to_sun / float(N);
	// a per-pixel jitter of the start hides the steps between samples
	float jitter = fract(52.9829189 * fract(dot(FRAGCOORD.xy, vec2(0.06711056, 0.00583715))));
	vec2 p = uv + stp * jitter;
	float acc = 0.0;
	float w = 1.0;
	for (int i = 0; i < N; i++) {
		p += stp;
		float lit;
		if (p.x < 0.0 || p.x > 1.0 || p.y < 0.0 || p.y > 1.0) {
			lit = 0.35;  // off screen, towards the sun: open sky
		} else {
			float z = textureLod(depth_tex, p, 0.0).r;
			float sky = 1.0 - step(0.000001, z);
			vec3 c = textureLod(screen_tex, p, 0.0).rgb;
			lit = max(dot(c, vec3(0.3, 0.5, 0.2)) - 0.72, 0.0) * sky;
		}
		acc += lit * w;
		w *= 0.975;
	}
	acc /= float(N);
	float fall = exp(-length(to_sun * vec2(1.6, 1.0)) * 1.8);
	ALBEDO = tint * acc * strength * fall * 3.0;
}
