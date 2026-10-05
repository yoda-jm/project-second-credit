// Ridgefire risers: embers flying from the crater, lava bombs thrown out of it, blowing snow. One MultiMesh instance
// each, worked out from the backdrop's clock: the transform's origin is where it starts, its basis X length its size;
// INSTANCE_CUSTOM = (phase 0..1, period s, rise m (negative falls), kind); COLOR its tint. Kinds: 0 ember (drifts up on
// the wind, twinkling, fading from gold to red), 1 lava bomb (a ballistic arc, leaving a short trail), 2 snow (blown
// along the wind, swirling). Additive, camera-facing.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform float clock = 0.0;
uniform float energy = 2.0;
uniform vec3 wind = vec3(6.0, 0.0, 0.0);   // drift in m per period
uniform float burst = 0.0;                  // a harder eruption: more speed and light

varying vec2 v_uv;
varying float v_alpha;
varying vec3 v_col;
varying float v_kind;

void vertex() {
	vec3 base = MODEL_MATRIX[3].xyz;
	float size = length(MODEL_MATRIX[0].xyz);
	float phase = INSTANCE_CUSTOM.x;
	float period = max(INSTANCE_CUSTOM.y, 0.1);
	float rise = INSTANCE_CUSTOM.z;
	float kind = INSTANCE_CUSTOM.w;
	float u = fract(clock / period + phase);
	float cyc = floor(clock / period + phase);
	float s = fract(sin(phase * 91.7 + cyc * 13.1) * 43758.5);
	float s2 = fract(sin(phase * 31.3 + cyc * 7.7) * 13758.5);
	vec3 p = base;
	float alpha = smoothstep(0.0, 0.06, u) * (1.0 - smoothstep(0.6, 1.0, u));
	vec3 col = COLOR.rgb;
	vec3 stretch = vec3(0.0);
	if (kind < 0.5) {
		float sw = sin(u * 7.0 + phase * 40.0) * 0.5 + sin(u * 13.0 + s * 20.0) * 0.3;
		p += vec3((s - 0.5) * 2.0 * rise * 0.2 + sw * rise * 0.06, rise * (u - 0.2 * u * u) * (1.0 + burst * 0.6),
				(s2 - 0.5) * rise * 0.25) + wind * u;
		size *= 1.0 - 0.5 * u;
		alpha *= 0.6 + 0.4 * step(0.3, fract(sin(phase * 300.0 + floor(clock * 14.0)) * 4375.5));
		col = mix(vec3(1.0, 0.85, 0.45), vec3(1.0, 0.25, 0.05), u);
	} else if (kind < 1.5) {
		float an = s * 6.2831;
		float sp = rise * (0.35 + 0.65 * s2) * (1.0 + burst * 0.5);
		vec3 v0 = vec3(cos(an) * sp * 0.35, sp, sin(an) * sp * 0.2);
		float tt = u * period;
		vec3 vel = v0 + vec3(0.0, -9.8, 0.0) * tt;
		p += v0 * tt + vec3(0.0, -4.9, 0.0) * tt * tt + wind * u * 0.3;
		stretch = vel * 0.06;
		alpha = smoothstep(0.0, 0.03, u) * (1.0 - smoothstep(0.5, 1.0, u)) * step(base.y - 20.0, p.y);
		col = mix(vec3(1.0, 0.8, 0.4), vec3(1.0, 0.3, 0.05), smoothstep(0.0, 0.7, u));
	} else {
		float sw = sin(u * 9.0 + phase * 30.0) * 0.6 + sin(u * 21.0 + s * 11.0) * 0.25;
		p += vec3((s - 0.5) * 30.0, sw * 1.5 + rise * u, (s2 - 0.5) * 20.0) + wind * u;
		alpha = smoothstep(0.0, 0.1, u) * (1.0 - smoothstep(0.75, 1.0, u)) * 0.55;
	}
	vec3 right = INV_VIEW_MATRIX[0].xyz;
	vec3 up = INV_VIEW_MATRIX[1].xyz;
	vec3 wp = p + (right * VERTEX.x + up * VERTEX.y) * size;
	if (length(stretch) > 0.0) {
		wp += stretch * (VERTEX.y + 0.5) * 2.0;
	}
	v_uv = UV;
	v_alpha = alpha;
	v_kind = kind;
	v_col = col;
	VERTEX = (inverse(MODEL_MATRIX) * vec4(wp, 1.0)).xyz;
}

void fragment() {
	vec2 p = v_uv * 2.0 - 1.0;
	float a = exp(-dot(p, p) * 3.5);
	if (v_kind > 1.5) {
		a = smoothstep(1.0, 0.2, length(p));
	}
	ALBEDO = v_col * a * v_alpha * energy * (1.0 + burst * 0.5);
}
