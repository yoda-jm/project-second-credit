// Pop Voyage backdrop particles (petals, embers, snow, smoke, spray): camera-facing quads turned by the particle's
// angle. shape 0 soft dot, 1 petal, 2 smoke puff, 3 snowflake. Colour and alpha come from the particle colour.
shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled, depth_draw_never, shadows_disabled;

uniform int shape = 0;
uniform float emit = 1.0;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

varying float seed;

void vertex() {
	seed = INSTANCE_CUSTOM.y;
	mat4 w = mat4(normalize(INV_VIEW_MATRIX[0]), normalize(INV_VIEW_MATRIX[1]), normalize(INV_VIEW_MATRIX[2]), MODEL_MATRIX[3]);
	float a = INSTANCE_CUSTOM.x;
	w = w * mat4(vec4(cos(a), -sin(a), 0.0, 0.0), vec4(sin(a), cos(a), 0.0, 0.0), vec4(0.0, 0.0, 1.0, 0.0), vec4(0.0, 0.0, 0.0, 1.0));
	MODELVIEW_MATRIX = VIEW_MATRIX * w;
	float sx = length(MODEL_MATRIX[0].xyz);
	float flutter = shape == 1 ? 0.35 + 0.65 * abs(sin(TIME * 5.0 + float(INSTANCE_ID) * 1.7)) : 1.0;
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(sx * flutter, 0.0, 0.0, 0.0), vec4(0.0, sx, 0.0, 0.0), vec4(0.0, 0.0, sx, 0.0), vec4(0.0, 0.0, 0.0, 1.0));
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float a;
	vec3 c = COLOR.rgb;
	if (shape == 1) {
		vec2 q = p * vec2(1.0, 0.62);
		a = smoothstep(1.0, 0.8, length(q + vec2(0.0, 0.25 * p.x * p.x)));
		c = mix(c, vec3(1.0), 0.35 * (1.0 - length(p)));
	} else if (shape == 2) {
		float n = vnoise(p * 2.5 + seed * 17.0 + TIME * 0.1) * 0.6 + vnoise(p * 5.0 - seed * 9.0) * 0.4;
		a = smoothstep(1.0, 0.2, length(p)) * smoothstep(0.2, 0.7, n + 0.3 * (1.0 - length(p)));
	} else if (shape == 3) {
		a = smoothstep(1.0, 0.3, length(p));
	} else {
		a = smoothstep(1.0, 0.0, length(p));
		a *= a;
	}
	ALBEDO = c * emit;
	ALPHA = a * COLOR.a;
}
