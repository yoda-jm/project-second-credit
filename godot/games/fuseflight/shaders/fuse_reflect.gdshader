// Fuseflight night reflections: streaks of light lying on the water under the lanterns, lamps and windows; they
// shimmer and break up with the ripples. Additive. UV.y runs from the light's foot (0) towards the viewer (1);
// the colour is the vertex colour times `color`.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec3 color : source_color = vec3(1.0, 1.0, 1.0);
uniform float strength = 0.8;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float across = 1.0 - abs(UV.x * 2.0 - 1.0);
	float wob = vnoise(vec2(wpos.x * 1.5, wpos.z * 3.0 + TIME * 1.2));
	float bands = 0.3 + 0.7 * smoothstep(0.3, 0.8, vnoise(vec2(wpos.x * 0.8 + TIME * 0.3, wpos.z * 5.0 - TIME * 1.6)));
	float a = smoothstep(0.0, 0.7, across) * bands * (0.4 + 0.6 * wob) * pow(1.0 - UV.y, 1.2);
	ALBEDO = COLOR.rgb * color * strength * a;
}
