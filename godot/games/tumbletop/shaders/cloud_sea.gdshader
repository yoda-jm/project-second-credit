shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;
// The sea of clouds far below the pyramid: layered drifting noise, lit on top by the sky's colour, fading out with
// distance into the horizon.

uniform vec4 top_color : source_color = vec4(1.0, 0.9, 0.85, 1.0);
uniform vec4 low_color : source_color = vec4(0.55, 0.55, 0.75, 1.0);
uniform vec4 horizon : source_color = vec4(0.9, 0.8, 0.9, 1.0);
uniform float speed = 0.02;

varying vec3 wp;

float h2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(h2(i), h2(i + vec2(1, 0)), u.x), mix(h2(i + vec2(0, 1)), h2(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) {
	float v = 0.0, a = 0.5;
	for (int i = 0; i < 5; i++) { v += a * noise(p); p = p * 2.03 + vec2(1.7, 9.2); a *= 0.5; }
	return v;
}

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wp.xz * 0.045 + vec2(TIME * speed, TIME * speed * 0.4);
	float n = fbm(p);
	float n2 = fbm(p * 2.5 - vec2(TIME * speed * 1.7, 0.0));
	float puff = smoothstep(0.35, 0.75, n * 0.7 + n2 * 0.4);
	vec3 c = mix(low_color.rgb, top_color.rgb, puff);
	float d = length(wp.xz - CAMERA_POSITION_WORLD.xz);
	float far = smoothstep(40.0, 150.0, d);
	ALBEDO = mix(c, horizon.rgb, far);
	ALPHA = mix(0.55 + 0.45 * puff, 1.0, far) * (1.0 - smoothstep(170.0, 220.0, d));
}
