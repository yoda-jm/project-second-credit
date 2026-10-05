// Ridgefire lava: rivers that flow (UV.x across 0..1, UV.y along the flow in metres, written by
// tools/blender/ridgefire_backdrops.py), a crater's lake that churns (pool = 1: world space), and cracks glowing in
// the ash (cracks = 1). Plates of dark crust drift on it with bright seams, hottest along the middle of the flow,
// the whole glow breathing slowly. Unshaded HDR colour.
shader_type spatial;
render_mode unshaded, shadows_disabled, cull_disabled;

uniform float energy = 3.0;
uniform float speed = 1.0;      // m/s along the flow
uniform float pool = 0.0;
uniform float cracks = 0.0;
uniform float crust = 0.55;     // share of the surface under crust
uniform float plate = 6.0;      // plate size, m
uniform vec3 hot : source_color = vec3(1.0, 0.8, 0.35);
uniform vec3 warm : source_color = vec3(1.0, 0.32, 0.05);
uniform vec3 dark : source_color = vec3(0.07, 0.025, 0.02);
uniform float pulse = 0.25;
uniform float flare = 0.0;      // set by the backdrop when the cone erupts harder

varying vec3 wpos;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

vec2 hash2(vec2 p) {
	return vec2(hash(p), hash(p + vec2(17.3, 41.9)));
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

float fbm(vec2 p) {
	float v = 0.0, a = 0.5;
	for (int i = 0; i < 4; i++) {
		v += a * vnoise(p);
		p = p * 2.03 + vec2(1.7, 9.2);
		a *= 0.5;
	}
	return v;
}

// distance to the nearest plate edge
float seams(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	float d1 = 8.0, d2 = 8.0;
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 o = vec2(float(x), float(y));
			vec2 c = o + hash2(i + o) * 0.8 + 0.1 - f;
			float d = dot(c, c);
			if (d < d1) {
				d2 = d1;
				d1 = d;
			} else if (d < d2) {
				d2 = d;
			}
		}
	}
	return sqrt(d2) - sqrt(d1);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float t = TIME;
	vec2 p;
	float core;
	if (pool > 0.5) {
		vec2 q = wpos.xz / plate;
		q += 0.6 * vec2(sin(t * 0.13 + q.y * 0.4), cos(t * 0.11 + q.x * 0.4));
		p = q;
		core = 0.6 + 0.4 * fbm(wpos.xz * 0.05 + t * 0.05);
	} else if (cracks > 0.5) {
		p = vec2(UV.x * 2.0, UV.y / plate);
		core = smoothstep(0.5, 0.0, abs(UV.x - 0.5)) ;
	} else {
		p = vec2(UV.x * 3.0, (UV.y - t * speed) / plate);
		core = smoothstep(0.55, 0.05, abs(UV.x - 0.5));
	}
	float s = seams(p);
	float n = fbm(p * 2.0 + vec2(0.0, t * 0.05));
	float crusted = smoothstep(0.05, 0.2, s) * smoothstep(crust - 0.25, crust + 0.25, n + (1.0 - core) * 0.5);
	float heat = (1.0 - crusted) * (0.55 + 0.45 * core);
	heat *= 1.0 + pulse * sin(t * 0.7 + wpos.x * 0.02 + wpos.z * 0.015) + flare;
	vec3 col = mix(dark, warm, smoothstep(0.0, 0.5, heat));
	col = mix(col, hot, smoothstep(0.55, 1.1, heat));
	col += warm * 0.08 * crusted * core;   // the crust still glows a little
	ALBEDO = col * energy * (0.35 + 0.65 * smoothstep(0.0, 0.3, heat) + 0.25 * crusted);
}
