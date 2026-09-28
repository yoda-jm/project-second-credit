// Pop Voyage night reflections: streaks of light lying on the water under each lamp and window row; they shimmer
// and break up with the ripples. Additive. UV.y runs from the shore line (0) towards the viewer (1).
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.7, 0.35);
uniform float strength = 0.9;
uniform float calm = 0.0;     // 1 = a still pool of light (lamp light spilled on snow), no ripples

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
	float bands = 0.35 + 0.65 * smoothstep(0.3, 0.8, vnoise(vec2(wpos.x * 0.8 + TIME * 0.3, wpos.z * 5.0 - TIME * 1.6)));
	float a = smoothstep(0.0, 0.6, across) * bands * (0.4 + 0.6 * wob) * (1.0 - UV.y * 0.8);
	a = mix(a, smoothstep(0.0, 0.8, across) * pow(1.0 - UV.y, 1.5), calm);
	ALBEDO = COLOR.rgb * color * strength * a;
}
