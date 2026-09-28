// Pop Voyage mist bank: a soft band of drifting haze on a vertical plane (UV.y 0 at its foot), faded where it meets
// the ground and near the camera so it never shows an edge.
shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec3 color : source_color = vec3(0.95, 0.93, 0.95);
uniform float density = 0.5;
uniform float speed = 0.01;
uniform float soft = 3.0;
uniform sampler2D depth_tex : hint_depth_texture, filter_linear;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	float v = 1.0 - UV.y;  // 0 at the foot of the bank
	vec2 p = vec2(UV.x * 7.0 + TIME * speed * 7.0, v * 1.6);
	float n = vnoise(p) * 0.55 + vnoise(p * 2.3 + 3.1) * 0.3 + vnoise(p * 5.1 - TIME * speed * 9.0) * 0.15;
	float band = smoothstep(0.0, 0.2, v) * (1.0 - smoothstep(0.25, 0.95, v));
	float a = density * band * smoothstep(0.25, 0.75, n) * smoothstep(0.0, 0.1, UV.x) * smoothstep(1.0, 0.9, UV.x);
	float depth = texture(depth_tex, SCREEN_UV).r;
	vec4 up = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
	up.xyz /= up.w;
	a *= clamp(1.0 - smoothstep(up.z + soft, up.z, VERTEX.z), 0.0, 1.0);
	ALBEDO = color;
	ALPHA = clamp(a, 0.0, 1.0);
}
