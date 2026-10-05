// Ridgefire frozen sea: plates of sea ice with dark cracks between them, pressure ridges along some seams, drifts of
// snow on the plates, the ice glossy where it is bare (it mirrors the sky's colour, the aurora, by fresnel). Lit by the
// scene, with the same aerial haze as the land.
shader_type spatial;

uniform vec3 ice_col : source_color = vec3(0.55, 0.68, 0.8);
uniform vec3 snow_col : source_color = vec3(0.85, 0.9, 0.97);
uniform vec3 crack_col : source_color = vec3(0.04, 0.08, 0.14);
uniform vec3 sky_col : source_color = vec3(0.2, 0.6, 0.45);
uniform float plate = 40.0;
uniform float sky_pulse = 0.0;
uniform vec3 haze_col : source_color = vec3(0.6, 0.65, 0.75);
uniform vec3 haze_sun_col : source_color = vec3(1.0, 0.8, 0.6);
uniform vec3 sun_dir = vec3(0.5, 0.5, 0.5);
uniform float haze_start = 80.0;
uniform float haze_scale = 600.0;
uniform float haze_max = 0.8;
uniform float haze_sun_pow = 6.0;

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

vec3 cells(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	float d1 = 8.0, d2 = 8.0;
	vec2 id = vec2(0.0);
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 o = vec2(float(x), float(y));
			vec2 c = o + hash2(i + o) * 0.85 + 0.07 - f;
			float d = dot(c, c);
			if (d < d1) {
				d2 = d1;
				d1 = d;
				id = i + o;
			} else if (d < d2) {
				d2 = d;
			}
		}
	}
	return vec3(sqrt(d2) - sqrt(d1), hash(id), 0.0);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 to = wpos - CAMERA_POSITION_WORLD;
	float dist = length(to);
	vec3 vd = to / dist;
	vec2 p = wpos.xz / plate * vec2(1.0, 1.6);
	vec3 c = cells(p + 0.3 * vec2(fbm(p * 0.7), fbm(p * 0.7 + 4.0)));
	float far = smoothstep(80.0, 400.0, dist);
	float seam = smoothstep(0.03, 0.0, c.x) * (1.0 - far);
	float ridge = smoothstep(0.12, 0.0, c.x) * step(0.6, c.y);
	float drift = smoothstep(0.45, 0.65, fbm(wpos.xz * 0.04 + c.y * 3.0) + c.y * 0.25);
	vec3 col = mix(ice_col * (0.85 + 0.3 * c.y), snow_col, max(drift, ridge * 0.8));
	col = mix(col, crack_col, seam * (1.0 - ridge) * (1.0 - far * 0.7));
	float fr = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	float f = haze_max * (1.0 - exp(-max(dist - haze_start, 0.0) / haze_scale));
	float s = pow(max(dot(vd, normalize(sun_dir)), 0.0), haze_sun_pow);
	ALBEDO = col * (1.0 - f);
	EMISSION = sky_col * fr * 0.35 * (1.0 - drift) * (1.0 - seam) * (0.6 + 0.4 * sky_pulse) * (1.0 - f) + mix(haze_col, haze_sun_col, s) * f;
	ROUGHNESS = mix(0.18, 0.75, max(drift, seam));
	SPECULAR = 0.6;
}
