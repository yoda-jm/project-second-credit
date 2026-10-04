// Fuseflight risers: sky lanterns drifting up into the night, sparks flying from the bonfire, petals adrift. One
// MultiMesh instance each, worked out from the backdrop's clock: the transform's origin is where it starts, its
// basis X length its size; INSTANCE_CUSTOM = (phase 0..1, period s, rise m (negative falls), kind); COLOR its tint.
// Kinds: 0 sky lantern, 1 spark, 2 petal. Additive, camera-facing.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

uniform float clock = 0.0;
uniform float energy = 2.0;
uniform vec3 wind = vec3(0.6, 0.0, 0.0);   // drift in m per period

varying vec2 v_uv;
varying float v_alpha;
varying vec3 v_col;
varying float v_kind;
varying float v_seed;

void vertex() {
	vec3 base = MODEL_MATRIX[3].xyz;
	float size = length(MODEL_MATRIX[0].xyz);
	float phase = INSTANCE_CUSTOM.x;
	float period = max(INSTANCE_CUSTOM.y, 0.1);
	float rise = INSTANCE_CUSTOM.z;
	float kind = INSTANCE_CUSTOM.w;
	float u = fract(clock / period + phase);
	float cyc = floor(clock / period + phase);
	float s = fract(sin((phase * 91.7 + cyc * 13.1)) * 43758.5);
	vec3 p = base;
	float alpha = smoothstep(0.0, 0.08, u) * (1.0 - smoothstep(0.7, 1.0, u));
	if (kind < 0.5) {
		// a sky lantern: slow, sways a little, shrinks into the distance as it climbs away
		p += vec3((s - 0.5) * 4.0, 0.0, (s - 0.5) * 6.0) + wind * u + vec3(sin(clock * 0.5 + phase * 30.0) * 0.4, rise * u, -rise * u * 0.4);
		size *= 1.0 - 0.35 * u;
		alpha = smoothstep(0.0, 0.05, u) * (1.0 - smoothstep(0.6, 1.0, u));
	} else if (kind < 1.5) {
		// a spark: quick, twisting, fading from white-gold to red
		float sw = sin(u * 9.0 + phase * 40.0) * 0.5 + sin(u * 17.0 + s * 20.0) * 0.25;
		p += vec3(sw * u * 1.5 + (s - 0.5) * 1.2, rise * (u - 0.25 * u * u), (fract(s * 7.0) - 0.5) * 1.2) + wind * u;
		size *= 1.0 - 0.6 * u;
		alpha *= step(0.25, fract(sin(phase * 300.0 + floor(clock * 20.0)) * 4375.5)) * 0.6 + 0.4;
	} else {
		// a petal: falls fluttering
		p += vec3(sin(u * 6.0 + phase * 20.0) * 0.8 + (s - 0.5) * 3.0, rise * u, cos(u * 4.0 + phase * 10.0) * 0.5) + wind * u;
		size *= 0.6 + 0.4 * abs(sin(clock * 4.0 + phase * 30.0));
	}
	vec3 right = INV_VIEW_MATRIX[0].xyz;
	vec3 up = INV_VIEW_MATRIX[1].xyz;
	vec3 wp = p + (right * VERTEX.x + up * VERTEX.y * (kind < 0.5 ? 1.3 : 1.0)) * size;
	v_uv = UV;
	v_alpha = alpha;
	v_kind = kind;
	v_seed = s;
	v_col = COLOR.rgb;
	if (kind > 0.5 && kind < 1.5) {
		v_col = mix(vec3(1.0, 0.85, 0.5), vec3(1.0, 0.25, 0.08), u);
	}
	VERTEX = (inverse(MODEL_MATRIX) * vec4(wp, 1.0)).xyz;
}

void fragment() {
	vec2 p = v_uv * 2.0 - 1.0;
	float a;
	vec3 col = v_col;
	if (v_kind < 0.5) {
		// paper glowing from the flame inside: a soft rounded body, brighter low down, and a halo
		float body = smoothstep(1.0, 0.75, max(abs(p.x) * 1.35, abs(p.y + 0.05) * 1.15));
		float heart = exp(-dot(p - vec2(0.0, 0.35), p - vec2(0.0, 0.35)) * 3.0);
		a = body * (0.55 + 0.6 * heart) + exp(-dot(p, p) * 1.2) * 0.25;
		col = mix(col, vec3(1.0, 0.9, 0.6), heart * 0.5);
	} else if (v_kind < 1.5) {
		a = exp(-dot(p, p) * 4.0);
	} else {
		a = smoothstep(1.0, 0.6, length(p * vec2(1.0, 1.6))) * 0.5;
	}
	ALBEDO = col * a * v_alpha * energy;
}
