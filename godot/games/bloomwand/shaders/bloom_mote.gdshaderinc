// Bloomwand motes (our own, CC BY-SA 4.0): the small living things of a scene, one MultiMesh each, worked out on the
// GPU from the backdrop's clock. Each instance's transform origin is its home, its basis X length its size;
// INSTANCE_CUSTOM = (phase 0..1, period s, seed 0..1, -); COLOR its tint. The kind is the material's:
//   0 firefly (wanders round its home, blinking)   1 snowflake (falls `span`, drifting)   2 raindrop (a streak)
//   3 petal (falls fluttering, turning)   4 butterfly (loops round its home, wings beating)
//   5 bird (crosses `span` metres and back out of sight, wings beating)   6 sparkle (twinkles where it is)
//   7 wisp (rises `span` metres, wavering)   8 mote (dust drifting in a sunbeam)

uniform float clock = 0.0;
uniform int kind = 0;
uniform float span = 2.0;
uniform vec3 wind = vec3(0.0);
uniform float energy = 1.0;
uniform float flap_speed = 14.0;

varying vec2 v_uv;
varying float v_alpha;
varying vec3 v_col;
varying float v_flap;
varying float v_seed;

void vertex() {
	vec3 base = MODEL_MATRIX[3].xyz;
	float size = length(MODEL_MATRIX[0].xyz);
	float phase = INSTANCE_CUSTOM.x;
	float period = max(INSTANCE_CUSTOM.y, 0.1);
	float seed = INSTANCE_CUSTOM.z;
	float u = fract(clock / period + phase);
	float t = clock + phase * period;
	vec3 p = base;
	float alpha = 1.0;
	vec3 right = INV_VIEW_MATRIX[0].xyz;
	vec3 up = INV_VIEW_MATRIX[1].xyz;
	vec2 q = VERTEX.xy;
	v_flap = 0.0;
	if (kind == 0) {
		p += vec3(sin(t * 0.37 + seed * 20.0) + 0.5 * sin(t * 0.91 + seed * 7.0), 0.6 * sin(t * 0.53 + seed * 31.0),
				0.8 * cos(t * 0.29 + seed * 13.0)) * span;
		alpha = smoothstep(-0.2, 0.8, sin(t * (0.9 + seed * 1.3) + seed * 40.0));
	} else if (kind == 1) {
		p += vec3(sin(u * 6.0 + seed * 30.0) * 0.6, -span * u, cos(u * 5.0 + seed * 10.0) * 0.4) + wind * u;
		alpha = smoothstep(0.0, 0.06, u) * (1.0 - smoothstep(0.9, 1.0, u));
	} else if (kind == 2) {
		vec3 vel = vec3(0.0, -span, 0.0) + wind;
		p += vel * u;
		vec3 ax = normalize(vel);
		vec3 sd = normalize(cross(ax, normalize(CAMERA_POSITION_WORLD - p)));
		vec3 wp = p + sd * q.x * size * 0.06 + ax * q.y * size;
		v_uv = UV;
		v_alpha = smoothstep(0.0, 0.05, u) * (1.0 - smoothstep(0.92, 1.0, u));
		v_col = COLOR.rgb;
		v_seed = seed;
		VERTEX = (inverse(MODEL_MATRIX) * vec4(wp, 1.0)).xyz;
	} else if (kind == 3) {
		p += vec3(sin(u * 7.0 + seed * 20.0) * 0.9, -span * u, cos(u * 4.0 + seed * 10.0) * 0.6) + wind * u;
		alpha = smoothstep(0.0, 0.08, u) * (1.0 - smoothstep(0.85, 1.0, u));
		float an = t * 2.0 + seed * 10.0;
		q = mat2(vec2(cos(an), sin(an)), vec2(-sin(an), cos(an))) * vec2(q.x * (0.3 + 0.7 * abs(sin(t * 3.0 + seed * 9.0))), q.y);
	} else if (kind == 4) {
		float w = t * (0.35 + 0.2 * seed);
		p += vec3(sin(w) * span + 0.4 * sin(w * 3.1), 0.5 * sin(w * 2.3 + seed * 5.0) * span * 0.4 + 0.25 * sin(t * 5.0),
				cos(w * 0.8) * span * 0.6);
		v_flap = sin(t * flap_speed + seed * 30.0);
		q.x *= 0.15 + 0.85 * abs(v_flap);
	} else if (kind == 5) {
		float dir = seed < 0.5 ? 1.0 : -1.0;
		p += vec3(dir * span * (u - 0.5) * 2.0, sin(u * 12.0 + seed * 9.0) * 0.6 + sin(u * 3.0) * 1.5, 0.0) + wind * u;
		v_flap = sin(t * flap_speed * (0.8 + 0.4 * seed));
		q.x *= dir;
	} else if (kind == 6) {
		p += vec3(0.0, span * 0.2 * sin(t * 0.2 + seed * 7.0), 0.0);
		float s = sin(t * (1.5 + seed * 2.0) + seed * 40.0);
		alpha = smoothstep(0.6, 1.0, s);
	} else if (kind == 7) {
		p += vec3(sin(u * 5.0 + seed * 20.0) * span * 0.15, span * u, cos(u * 4.0 + seed * 7.0) * span * 0.15) + wind * u;
		alpha = smoothstep(0.0, 0.15, u) * (1.0 - smoothstep(0.6, 1.0, u));
	} else {
		p += vec3(sin(t * 0.13 + seed * 20.0), sin(t * 0.09 + seed * 7.0) - 0.3 * u, cos(t * 0.11 + seed * 3.0)) * span;
		alpha = 0.4 + 0.6 * smoothstep(0.2, 1.0, sin(t * 0.8 + seed * 30.0));
	}
	if (kind != 2) {
		vec3 wp = p + (right * q.x + up * q.y * (kind == 5 ? 0.5 : 1.0)) * size;
		v_uv = UV;
		v_alpha = alpha;
		v_col = COLOR.rgb;
		v_seed = seed;
		VERTEX = (inverse(MODEL_MATRIX) * vec4(wp, 1.0)).xyz;
	}
}

float mote_shape(out vec3 col) {
	vec2 p = v_uv * 2.0 - 1.0;
	col = v_col;
	float a = 0.0;
	if (kind == 0 || kind == 7 || kind == 8) {
		a = exp(-dot(p, p) * 5.0) + 0.6 * exp(-dot(p, p) * 30.0);
		col = mix(v_col, vec3(1.0), exp(-dot(p, p) * 30.0) * 0.5);
	} else if (kind == 1) {
		a = smoothstep(1.0, 0.3, length(p));
	} else if (kind == 2) {
		a = smoothstep(1.0, 0.0, abs(p.x)) * smoothstep(1.0, 0.2, abs(p.y)) * 0.5;
	} else if (kind == 3) {
		a = smoothstep(1.0, 0.8, length(p * vec2(1.0, 1.7)));
		col = mix(v_col * 0.8, v_col, p.y * 0.5 + 0.5);
	} else if (kind == 4) {
		vec2 w = vec2(abs(p.x), p.y);
		float upper = smoothstep(0.52, 0.45, length((w - vec2(0.45, 0.22)) * vec2(1.0, 1.15)));
		float lower = smoothstep(0.36, 0.3, length(w - vec2(0.32, -0.38)));
		float body = smoothstep(0.1, 0.05, abs(p.x)) * smoothstep(0.75, 0.6, abs(p.y));
		float wing = max(upper, lower);
		float edge = smoothstep(0.3, 0.48, length((w - vec2(0.45, 0.22)) * vec2(1.0, 1.15))) * upper;
		float spot = smoothstep(0.1, 0.06, length(w - vec2(0.55, 0.3)));
		col = mix(v_col, v_col * 0.35, edge * 0.8);
		col = mix(col, vec3(1.0), spot * 0.7);
		col = mix(col, vec3(0.1, 0.08, 0.06), body);
		a = max(wing, body);
	} else if (kind == 5) {
		float x = p.x;
		float yc = v_flap * abs(x) * 0.7 - 0.15 * x * x;
		float th = 0.22 * (1.0 - x * x) + 0.05;
		a = smoothstep(th, th * 0.6, abs(p.y - yc)) * step(abs(x), 0.98);
		a = max(a, smoothstep(0.2, 0.1, length(p * vec2(1.0, 1.6))));
	} else {
		float star = max(smoothstep(0.12, 0.0, abs(p.x)) * smoothstep(1.0, 0.0, abs(p.y)),
				smoothstep(0.12, 0.0, abs(p.y)) * smoothstep(1.0, 0.0, abs(p.x)));
		a = star + exp(-dot(p, p) * 8.0);
		col = mix(v_col, vec3(1.0), 0.5);
	}
	return a * v_alpha;
}
