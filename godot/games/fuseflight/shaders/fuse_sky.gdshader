// Fuseflight night sky: a dome round the camera. A three-stop gradient with the last of the dusk low on one side,
// stars that twinkle (and a faint band of dust), the moon with its halo, a comet with a curved dust tail and a
// straight blue ion tail, thin clouds lit from below by the festival, and the haze each firework lights round itself
// (glow_dir / glow_col, set every frame by FuseBackdrop). Below the horizon: the far sea or land, with the sky's
// glow mirrored in it. Unshaded and unfogged: it is the horizon the fog fades into. Runs on `clock`.
shader_type spatial;
render_mode unshaded, cull_front, fog_disabled, shadows_disabled;

uniform float clock = 0.0;
uniform vec3 top_col : source_color = vec3(0.02, 0.03, 0.09);
uniform vec3 mid_col : source_color = vec3(0.06, 0.08, 0.2);
uniform vec3 horizon_col : source_color = vec3(0.16, 0.16, 0.32);
uniform vec3 below_col : source_color = vec3(0.04, 0.05, 0.1);
uniform float sea = 0.0;            // 1: the sky is mirrored below the horizon (open water)
uniform float mid_height = 0.22;
uniform vec3 dusk_dir = vec3(-0.8, 0.0, -0.6);
uniform vec3 dusk_col : source_color = vec3(0.9, 0.4, 0.3);
uniform float dusk = 0.0;
uniform float stars = 1.0;
uniform float moon = 0.0;
uniform vec3 moon_dir = vec3(0.5, 0.45, -0.75);
uniform vec3 moon_col : source_color = vec3(0.95, 0.93, 0.85);
uniform float moon_size = 0.5;
uniform float comet = 0.0;
uniform vec3 comet_dir = vec3(-0.45, 0.42, -0.79);
uniform vec3 comet_tail = vec3(-0.7, 0.35, 0.0);  // the way the tail streams on the sky
uniform float clouds = 0.0;
uniform vec3 cloud_col : source_color = vec3(0.12, 0.1, 0.18);
uniform vec3 cloud_lit : source_color = vec3(0.5, 0.3, 0.3);
uniform vec4 glow_dir[6];           // xyz direction, w angular size
uniform vec4 glow_col[6];           // rgb (already scaled by strength)

varying vec3 dir;

void vertex() {
	dir = VERTEX;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float hash3(vec3 p) {
	return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

float fbm(vec2 p) {
	float v = 0.0, a = 0.5;
	for (int i = 0; i < 5; i++) {
		v += a * vnoise(p);
		p = p * 2.03 + vec2(1.7, 9.2);
		a *= 0.5;
	}
	return v;
}

vec3 sky(vec3 d, bool detail) {
	float e = d.y;
	float k = clamp(e / mid_height, 0.0, 1.0);
	vec3 c = mix(horizon_col, mid_col, smoothstep(0.0, 1.0, k));
	c = mix(c, top_col, smoothstep(mid_height, 0.9, e));
	// the last of the dusk: a warm band low towards dusk_dir
	vec3 dd = normalize(vec3(dusk_dir.x, 0.0, dusk_dir.z));
	float az = max(dot(normalize(vec3(d.x, 0.0, d.z)), dd), 0.0);
	float band = pow(az, 3.0) * exp(-max(e, 0.0) * 9.0);
	c = mix(c, dusk_col, clamp(dusk * band, 0.0, 1.0));
	c += dusk_col * dusk * 0.18 * pow(az, 2.0) * exp(-max(e, 0.0) * 3.0);
	// firework haze
	for (int i = 0; i < 6; i++) {
		float s = glow_dir[i].w;
		if (s > 0.0) {
			float an = acos(clamp(dot(d, glow_dir[i].xyz), -1.0, 1.0));
			c += glow_col[i].rgb * (exp(-an * an / (s * s)) + 0.25 * exp(-an * an / (s * s * 9.0)));
		}
	}
	if (!detail) {
		return c;
	}
	float above = smoothstep(0.0, 0.06, e);
	if (stars > 0.0) {
		vec3 p = d * 300.0;
		vec3 cell = floor(p);
		float h = hash3(cell);
		vec3 f = fract(p) - 0.5;
		float star = step(1.0 - 0.07 * stars, h) * smoothstep(0.32, 0.0, length(f));
		float big = step(0.996, h);
		float tw = 0.55 + 0.45 * sin(clock * (1.3 + h * 4.0) + h * 60.0);
		vec3 sc = mix(vec3(0.7, 0.82, 1.0), vec3(1.0, 0.88, 0.7), fract(h * 13.0));
		c += sc * star * tw * (1.1 + big * 2.0) * smoothstep(0.04, 0.3, e) * stars;
		// the band of dust
		vec3 bn = normalize(vec3(0.35, 0.25, 1.0));
		float bd = exp(-pow(dot(d, bn) * 3.2, 2.0));
		if (bd > 0.03) {
			float dust = fbm(d.xy * 7.0 + d.z * 3.0) * fbm(d.yz * 13.0 + 2.0);
			c += vec3(0.22, 0.24, 0.4) * bd * dust * 0.45 * stars * smoothstep(0.06, 0.35, e);
		}
	}
	if (moon > 0.0) {
		vec3 md = normalize(moon_dir);
		float m = max(dot(d, md), 0.0);
		float r0 = 1.0 - 0.00028 * moon_size;
		if (m > r0 - 0.0001) {
			float disc = smoothstep(r0, r0 + 0.00008, m);
			float craters = 0.82 + 0.18 * fbm(d.xy * 380.0 + d.z * 90.0);
			c = mix(c, moon_col * craters * 1.25, disc * moon);
		}
		c += moon_col * moon * (pow(m, 1500.0) * 0.18 + pow(m, 90.0) * 0.05 + pow(m, 10.0) * 0.02);
	}
	if (comet > 0.0) {
		vec3 cd = normalize(comet_dir);
		vec3 tu = normalize(comet_tail - cd * dot(comet_tail, cd));
		vec3 tv = cross(cd, tu);
		float u = dot(d, tu);
		float v = dot(d, tv);
		float w = dot(d, cd);
		if (w > 0.55) {
			float r2 = u * u + v * v;
			c += vec3(0.85, 0.95, 1.0) * comet * (exp(-r2 * 120000.0) * 1.3 + exp(-r2 * 8000.0) * 0.25);
			float uu = max(u, 0.0);
			// the dust tail: broad, curving, pale gold, with streamers
			float vc = 0.55 * uu * uu;
			float wd = 0.005 + uu * 0.3;
			float dust = exp(-pow((v - vc) / wd, 2.0)) * exp(-uu * 1.4) * smoothstep(0.0, 0.015, uu);
			float str = 0.85 + 0.15 * sin((v - vc) / wd * 7.0 + uu * 6.0);
			dust *= str * (0.85 + 0.15 * sin(clock * 0.3 + uu * 20.0));
			c += vec3(1.0, 0.86, 0.66) * comet * dust * 0.24;
			// the ion tail: straight, narrow, blue
			float ion = exp(-pow(v / (0.002 + uu * 0.035), 2.0)) * exp(-uu * 1.1) * smoothstep(0.0, 0.015, uu);
			ion *= 0.75 + 0.25 * vnoise(vec2(uu * 40.0 - clock * 0.6, v * 300.0));
			c += vec3(0.45, 0.7, 1.0) * comet * ion * 0.2;
		}
	}
	if (clouds > 0.0 && e > 0.0) {
		vec2 uv = d.xz / (e + 0.06) * 0.7 + vec2(clock * 0.003, clock * 0.001);
		float n = fbm(uv * vec2(1.0, 2.6));
		float dens = smoothstep(1.0 - clouds * 0.8, 1.25 - clouds * 0.6, n) * smoothstep(0.0, 0.12, e) * 0.85;
		float under = smoothstep(0.5, 0.0, e);
		vec3 cc = mix(cloud_col, cloud_lit, under * 0.8);
		c = mix(c, cc + (c - horizon_col) * 0.25, dens);
	}
	return c * mix(0.6, 1.0, above);
}

void fragment() {
	vec3 d = normalize(dir);
	vec3 c;
	if (d.y >= 0.0) {
		c = sky(d, true);
	} else {
		float k = smoothstep(0.0, 0.1, -d.y);
		vec3 m = sky(vec3(d.x, -d.y, d.z), false);
		vec3 refl = m * mix(0.55, 0.15, k) * (0.85 + 0.15 * vnoise(vec2(d.x * 300.0, d.y * 2000.0 + clock * 2.0)));
		c = mix(below_col + refl * sea, below_col, k * (1.0 - sea * 0.4));
		c = mix(c, sky(vec3(d.x, 0.0, d.z), false), (1.0 - smoothstep(0.0, 0.01, -d.y)) * 0.5);
	}
	ALBEDO = c;
}
