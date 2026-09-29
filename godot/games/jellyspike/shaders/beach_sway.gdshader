// Jelly Spike beach plants and cloth, vertex-coloured, moving in the sea breeze. kind 0: plants bending by UV.y (the
// height above the plant's foot); 1: palms, the same plus fronds that flutter by UV.x (along the frond); 2: flags
// rippling along UV.x (distance from the pole); 3: bunting swinging by UV.y (depth below the rope). Gusts roll across.
// 4: palm trunks, bending like palms, with ring bark drawn from UV.y (rings, grooves and a bump). rim lights the edges
// against a low sun.
shader_type spatial;
render_mode cull_disabled;

uniform int kind = 0;
uniform float amp = 0.03;
uniform float speed = 1.1;
uniform float rough : hint_range(0.0, 1.0) = 0.8;
uniform float translucency = 0.25;
uniform vec3 tint : source_color = vec3(1.0);
uniform float rim = 0.0;       // a lit edge against a low sun (golden hour)
uniform float rim_tint = 0.5;

varying float hgt_v;
varying vec3 wpos;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() {
	hgt_v = UV.y;
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wpos = w;
	float gust = 0.6 + 0.4 * sin(TIME * 0.33 + w.x * 0.05);
	if (kind <= 1 || kind == 4) {
		float hgt = max(UV.y, 0.0);
		float s = sin(TIME * speed + w.x * 0.21 + w.z * 0.13) + 0.35 * sin(TIME * speed * 2.3 + w.x * 0.9 + w.z * 0.5);
		float d = amp * pow(hgt, 1.3) * s * gust;
		VERTEX.x += d;
		VERTEX.z += d * 0.3;
		if (kind == 1) {
			float f = UV.x;
			float fl = sin(TIME * 3.1 + w.x * 1.7 + w.z * 1.3 + f * 4.0) + 0.5 * sin(TIME * 5.3 + w.z * 2.1 + f * 7.0);
			VERTEX.y += fl * f * f * 0.12 * gust;
			VERTEX.x += fl * f * 0.05;
		}
	} else if (kind == 2) {
		float u = max(UV.x, 0.0);
		float s = sin(TIME * 5.0 - u * 4.5 + UV.y * 0.7) + 0.4 * sin(TIME * 8.3 - u * 8.0);
		VERTEX.z += s * u * 0.16 * gust;
		VERTEX.x -= abs(s) * u * 0.03;
	} else {
		float dep = max(UV.y, 0.0);
		float s = sin(TIME * 2.4 + w.x * 1.9) + 0.5 * sin(TIME * 4.1 + w.x * 3.7);
		VERTEX.z += s * dep * 0.35 * gust;
		VERTEX.x += s * dep * 0.08;
	}
	COLOR.rgb *= tint;
}

void fragment() {
	ALBEDO = COLOR.rgb;
	if (kind == 4) {
		// ring bark: a groove every ~12 cm, wobbling round the trunk, fibres between; bumped with the same height
		float wob = vnoise(wpos.xz * 9.0 + hgt_v) * 0.35;
		float ring = fract(hgt_v * 8.0 + wob);
		float groove = smoothstep(0.0, 0.12, ring) * smoothstep(1.0, 0.8, ring);
		float fibre = vnoise(vec2((wpos.x + wpos.z) * 14.0, hgt_v * 30.0));
		float h = groove * 0.8 + fibre * 0.2;
		ALBEDO *= 0.7 + 0.38 * h;
		vec3 dpdx = dFdx(VERTEX), dpdy = dFdy(VERTEX);
		float dhx = dFdx(h), dhy = dFdy(h);
		vec3 n = normalize(NORMAL);
		vec3 r1 = cross(dpdy, n), r2 = cross(n, dpdx);
		float det = dot(dpdx, r1);
		NORMAL = normalize(abs(det) * n - sign(det) * (dhx * r1 + dhy * r2) * 0.012);
	}
	ROUGHNESS = rough;
	SPECULAR = 0.3;
	BACKLIGHT = COLOR.rgb * translucency;
	RIM = rim;
	RIM_TINT = rim_tint;
}
