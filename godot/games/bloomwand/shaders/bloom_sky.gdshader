// Bloomwand sky: a dome round the camera (our own, CC BY-SA 4.0). A three-stop gradient with the sun's warmth low
// towards it, the sun (or none), a big storybook moon with its halo, twinkling stars, soft clouds lit by the sun,
// a rainbow, an aurora's curtains, a storm's heavy roof with lightning bolts and flashes, the glow of a celebration.
// Unshaded and unfogged: it is the horizon the fog fades into. Runs on `clock` (set by BloomBackdrop).
shader_type spatial;
render_mode unshaded, cull_front, fog_disabled, shadows_disabled, depth_draw_never;

#include "res://games/bloomwand/shaders/bloom_noise.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 top_col : source_color = vec3(0.3, 0.5, 0.85);
uniform vec3 mid_col : source_color = vec3(0.55, 0.7, 0.9);
uniform vec3 horizon_col : source_color = vec3(0.85, 0.9, 0.85);
uniform vec3 below_col : source_color = vec3(0.3, 0.4, 0.3);
uniform float mid_height = 0.22;
uniform vec3 sun_dir = vec3(-0.5, 0.3, -0.8);
uniform vec3 sun_col : source_color = vec3(1.0, 0.9, 0.7);
uniform float sun_disc = 0.0;
uniform float sun_size = 0.03;       // angular radius (rad)
uniform float sun_glow = 0.3;
uniform float moon = 0.0;
uniform vec3 moon_dir = vec3(0.4, 0.15, -0.9);
uniform vec3 moon_col : source_color = vec3(1.0, 0.96, 0.85);
uniform float moon_size = 0.06;      // angular radius (rad)
uniform float stars = 0.0;
uniform float clouds = 0.0;
uniform vec3 cloud_col : source_color = vec3(0.9, 0.9, 0.95);
uniform vec3 cloud_lit : source_color = vec3(1.0, 0.85, 0.6);
uniform float cloud_scale = 1.0;
uniform float storm = 0.0;
uniform vec3 storm_col : source_color = vec3(0.12, 0.1, 0.16);
uniform vec3 storm_lit : source_color = vec3(0.6, 0.3, 0.3);
uniform float aurora = 0.0;
uniform vec3 aurora_low : source_color = vec3(0.3, 1.0, 0.6);
uniform vec3 aurora_high : source_color = vec3(0.6, 0.3, 1.0);
uniform float rainbow = 0.0;
uniform vec3 rainbow_dir = vec3(0.4, -0.2, -0.9);
uniform float rainbow_radius = 0.6;
uniform float eye = 0.0;           // a glowing break in the storm round eye_dir
uniform vec3 eye_dir = vec3(0.2, 0.3, -0.9);
uniform vec3 eye_col : source_color = vec3(1.0, 0.4, 0.5);
uniform float eye_size = 0.3;
uniform vec4 bolt = vec4(0.3, 0.4, -0.9, -100.0);   // xyz the bolt's top direction, w its start time
uniform float bolt_seed = 0.0;
uniform float flash = 0.0;           // the storm's sheet lightning (0..1)
uniform vec3 flash_col : source_color = vec3(0.75, 0.75, 1.0);
uniform vec4 glow = vec4(0.0, 0.4, -0.9, 0.0);      // a celebration's glow: xyz direction, w strength
uniform vec3 glow_col : source_color = vec3(1.0, 0.8, 0.5);

varying vec3 dir;

void vertex() {
	dir = VERTEX;
}

float bolt_path(float e, float s) {
	return 0.05 * (bw_noise(vec2(e * 14.0, s * 31.0)) - 0.5) + 0.018 * (bw_noise(vec2(e * 70.0, s * 7.0)) - 0.5);
}

vec3 sky(vec3 d) {
	float e = d.y;
	vec3 c = mix(horizon_col, mid_col, smoothstep(0.0, 1.0, clamp(e / mid_height, 0.0, 1.0)));
	c = mix(c, top_col, smoothstep(mid_height, 0.95, e));
	vec3 sd = normalize(sun_dir);
	float sa = max(dot(d, sd), 0.0);
	// the sun's warmth along the horizon and round the sun
	vec3 shz = normalize(vec3(sd.x, 0.0, sd.z));
	float az = max(dot(normalize(vec3(d.x, 0.0, d.z)), shz), 0.0);
	c += sun_col * sun_glow * (pow(az, 4.0) * exp(-max(e, 0.0) * 6.0) * 0.6 + pow(sa, 12.0) * 0.5 + pow(sa, 200.0) * 0.8);
	float above = smoothstep(-0.02, 0.05, e);
	if (stars > 0.0) {
		vec3 p = d * 280.0;
		float h = bw_hash3(floor(p));
		vec3 f = fract(p) - 0.5;
		float star = step(1.0 - 0.08 * stars, h) * smoothstep(0.32, 0.0, length(f));
		float tw = 0.5 + 0.5 * sin(clock * (1.1 + h * 4.0) + h * 60.0);
		vec3 sc = mix(vec3(0.75, 0.85, 1.0), vec3(1.0, 0.9, 0.75), fract(h * 13.0));
		c += sc * star * tw * (1.0 + step(0.996, h) * 2.0) * smoothstep(0.05, 0.35, e) * stars;
	}
	if (moon > 0.0) {
		vec3 md = normalize(moon_dir);
		float an = acos(clamp(dot(d, md), -1.0, 1.0));
		float disc = smoothstep(moon_size, moon_size * 0.97, an);
		if (disc > 0.0) {
			vec3 up = vec3(0.0, 1.0, 0.0);
			vec3 mr = normalize(cross(up, md));
			vec3 mu = cross(md, mr);
			vec2 q = vec2(dot(d, mr), dot(d, mu)) / moon_size;
			float maria = smoothstep(0.45, 0.65, bw_fbm(q * 2.2 + 3.0, 4));
			float craters = 0.88 + 0.12 * bw_fbm(q * 9.0, 3);
			float limb = 0.85 + 0.15 * sqrt(max(0.0, 1.0 - dot(q, q)));
			vec3 mc = moon_col * craters * limb * mix(1.0, 0.78, maria);
			c = mix(c, mc * 1.5, disc * moon);
		}
		c += moon_col * moon * (exp(-an / (moon_size * 0.6)) * 0.35 + exp(-an / (moon_size * 4.0)) * 0.12);
	}
	if (sun_disc > 0.0) {
		float an = acos(clamp(sa, -1.0, 1.0));
		c = mix(c, sun_col * 4.0, smoothstep(sun_size, sun_size * 0.85, an) * sun_disc * smoothstep(-0.01, 0.01, e));
	}
	if (aurora > 0.0 && e > 0.0) {
		float a = atan(d.x, -d.z);
		for (int k = 0; k < 2; k++) {
			float fk = float(k);
			float b = 0.09 + 0.05 * fk + 0.05 * sin(a * (2.1 + fk) + clock * 0.04 + fk * 2.0) + 0.025 * sin(a * 5.3 - clock * 0.07);
			float v = (e - b) / (0.28 - fk * 0.06);
			if (v > -0.05 && v < 1.0) {
				float rays = bw_noise(vec2(a * (70.0 + fk * 30.0) + clock * 0.25, clock * 0.05 + fk * 9.0));
				float fold = 0.35 + 0.65 * bw_fbm(vec2(a * 4.0 - clock * 0.03 + fk * 5.0, clock * 0.02), 3);
				float hem = exp(-max(v, 0.0) * 6.0) * 1.3 + exp(-max(v, 0.0) * 1.8) * 0.45;
				float side = smoothstep(1.5, 0.6, abs(a - 0.2 + fk * 0.5));
				float i = hem * fold * (0.35 + 0.9 * rays * rays) * smoothstep(-0.05, 0.02, v) * side;
				c += mix(aurora_low, aurora_high, smoothstep(0.1, 0.9, v)) * i * aurora * (0.6 - fk * 0.25);
			}
		}
	}
	if (rainbow > 0.0 && e > -0.01) {
		float an = acos(clamp(dot(d, normalize(rainbow_dir)), -1.0, 1.0));
		float x = (an - rainbow_radius) / 0.045;
		float band = clamp(1.0 - x * x, 0.0, 1.0);
		vec3 hue = bw_hue(clamp((1.0 - x) * 0.39, 0.0, 0.8));
		float fade = smoothstep(-0.01, 0.08, e) * (0.6 + 0.4 * bw_noise(vec2(an * 3.0, e * 4.0)));
		c += hue * band * band * rainbow * fade * 0.35;
		c += vec3(0.06) * rainbow * smoothstep(-1.0, -3.0, x) * smoothstep(-14.0, -3.0, x) * fade;
	}
	if (clouds > 0.0 && e > -0.02) {
		vec2 uv = d.xz / (max(e, 0.0) + 0.08) * 0.6 * cloud_scale + vec2(clock * 0.004, clock * 0.0015);
		float n = bw_fbm(uv * vec2(1.0, 2.4), 5);
		float dens = smoothstep(1.0 - clouds * 0.75, 1.2 - clouds * 0.55, n) * smoothstep(-0.02, 0.1, e) * 0.9;
		float lit = pow(sa, 3.0) * 0.8 + 0.2 * smoothstep(0.4, 0.8, n);
		float edge = smoothstep(0.0, 0.5, dens) * (1.0 - smoothstep(0.5, 1.0, dens));
		vec3 cc = mix(cloud_col, cloud_lit, clamp(lit + edge * pow(sa, 2.0), 0.0, 1.0));
		c = mix(c, cc, dens);
	}
	if (storm > 0.0) {
		vec2 uv = d.xz / (max(e, 0.0) + 0.25) * 0.45 + vec2(clock * 0.012, clock * 0.004);
		uv += 0.8 * vec2(bw_fbm(uv * 1.3 + 3.1, 3), bw_fbm(uv * 1.3 + 8.7, 3));
		float n = bw_fbm(uv * vec2(1.0, 1.4), 5);
		float n2 = bw_fbm(uv * 3.1 + 7.0 - clock * 0.01, 4);
		float dens = smoothstep(0.25, 0.6, n + 0.15) * smoothstep(0.03, 0.14, e) * storm;
		if (eye > 0.0) {
			float ea = acos(clamp(dot(d, normalize(eye_dir)), -1.0, 1.0));
			float open = smoothstep(eye_size, eye_size * 0.35, ea + (n - 0.5) * eye_size * 0.6);
			dens *= 1.0 - open * eye * 0.85;
			c += eye_col * eye * (exp(-ea * ea / (eye_size * eye_size)) * 0.9 + exp(-ea * ea / (eye_size * eye_size * 6.0)) * 0.3);
		}
		vec3 sc = storm_col * (0.65 + 0.7 * n2);
		sc = mix(sc, storm_lit, smoothstep(0.2, 0.0, e) * (1.0 - n) * 0.8);
		if (eye > 0.0) {
			float ea = acos(clamp(dot(d, normalize(eye_dir)), -1.0, 1.0));
			sc = mix(sc, eye_col * (0.4 + 0.6 * n2), smoothstep(eye_size * 2.2, eye_size * 0.6, ea) * eye * 0.6);
		}
		sc += flash_col * flash * (0.4 + 1.2 * n2);
		c = mix(c, sc, dens);
		// lightning
		float age = clock - bolt.w;
		if (age >= 0.0 && age < 0.8) {
			float env = exp(-age * 14.0) + 0.8 * step(0.13, age) * exp(-max(age - 0.13, 0.0) * 10.0)
					+ 0.5 * step(0.32, age) * exp(-max(age - 0.32, 0.0) * 12.0);
			vec3 bd = normalize(bolt.xyz);
			float a0 = atan(bd.x, -bd.z);
			float a = atan(d.x, -d.z);
			float top = bd.y;
			if (e < top && e > -0.01) {
				float x = a0 + bolt_path(e, bolt_seed);
				float w = abs(a - x) * cos(e);
				float core = exp(-w * w / 0.000004) + 0.35 * exp(-w * w / 0.00008);
				float br = a0 + bolt_path(e, bolt_seed + 3.0) + (top * 0.6 - e) * 0.25;
				float wb = abs(a - br) * cos(e);
				core += (0.6 * exp(-wb * wb / 0.000003) + 0.2 * exp(-wb * wb / 0.00005)) * step(e, top * 0.6) * step(top * 0.25, e);
				c += vec3(0.85, 0.85, 1.0) * core * env * 3.0;
			}
			float an = acos(clamp(dot(d, bd), -1.0, 1.0));
			c += flash_col * env * 0.35 * exp(-an * an * 6.0) * (0.5 + n2);
		}
	}
	if (glow.w > 0.0) {
		float an = acos(clamp(dot(d, normalize(glow.xyz)), -1.0, 1.0));
		c += glow_col * glow.w * exp(-an * an * 4.0);
	}
	return mix(below_col, c, above);
}

void fragment() {
	vec3 d = normalize(dir);
	ALBEDO = sky(d);
}
