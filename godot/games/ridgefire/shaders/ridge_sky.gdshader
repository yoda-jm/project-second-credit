// Ridgefire sky: a dome round the camera. A three-stop gradient with a warm glow low on one side (the sunset, the
// volcano), the pink belt of the evening on the other, an optional sun disc, cumulus or streaky clouds lit from the
// light's side, stars with a band of dust, the moon, a huge planet (oceans, continents, swirling clouds, its night
// side's cities, the thin blue air on its rim), the aurora (curtains that ripple and drift, green low and violet
// high), a spreading ash cloud lit from below, lightning in it, and the brief haze of the explosions (boom_dir /
// boom_col, set by RidgeBackdrop). Unshaded and unfogged: the horizon is where the haze of the land ends. Runs on
// `clock`.
shader_type spatial;
render_mode unshaded, cull_front, fog_disabled, shadows_disabled;

uniform float clock = 0.0;
uniform vec3 top_col : source_color = vec3(0.1, 0.2, 0.5);
uniform vec3 mid_col : source_color = vec3(0.3, 0.5, 0.8);
uniform vec3 horizon_col : source_color = vec3(0.7, 0.8, 0.9);
uniform vec3 below_col : source_color = vec3(0.2, 0.2, 0.2);
uniform float mid_height = 0.25;
// the warm side (sunset, volcano) and the belt opposite
uniform vec3 glow_dir = vec3(1.0, 0.0, -0.3);
uniform vec3 glow_col : source_color = vec3(1.0, 0.5, 0.2);
uniform float glow = 0.0;
uniform float glow_spread = 2.0;      // power on the azimuth (higher: narrower)
uniform float glow_rise = 6.0;        // falloff with elevation
uniform vec3 belt_col : source_color = vec3(0.8, 0.5, 0.6);
uniform float belt = 0.0;
// the sun
uniform float sun_disc = 0.0;
uniform vec3 sun_dir = vec3(0.3, 0.1, -0.9);
uniform vec3 sun_col : source_color = vec3(1.0, 0.9, 0.7);
uniform float sun_size = 0.02;        // angular radius, radians
uniform float sun_halo = 0.0;
// night
uniform float stars = 0.0;
uniform float dust = 0.0;              // the band of the galaxy
uniform vec3 dust_axis = vec3(0.35, 0.25, 1.0);
uniform float moon = 0.0;
uniform vec3 moon_dir = vec3(-0.4, 0.3, -0.85);
uniform vec3 moon_col : source_color = vec3(0.95, 0.93, 0.88);
uniform float moon_size = 0.012;
// clouds
uniform float clouds = 0.0;
uniform float cloud_streak = 0.0;      // 0 cumulus, 1 long streaks
uniform float cloud_scale = 1.0;
uniform vec3 cloud_col : source_color = vec3(1.0);
uniform vec3 cloud_shade : source_color = vec3(0.6, 0.65, 0.75);
uniform vec3 cloud_lit : source_color = vec3(1.0, 0.8, 0.6);   // the underside on the light's side
uniform vec3 cloud_light = vec3(-0.5, 0.6, 0.6);
// the planet
uniform float planet = 0.0;
uniform vec3 planet_dir = vec3(-0.35, 0.12, -0.93);
uniform float planet_size = 0.15;      // angular radius, radians
uniform vec3 planet_light = vec3(0.8, 0.2, 0.55);
uniform float planet_spin = 0.004;
// the aurora
uniform float aurora = 0.0;
uniform vec3 aurora_low : source_color = vec3(0.2, 1.0, 0.5);
uniform vec3 aurora_high : source_color = vec3(0.6, 0.2, 1.0);
uniform vec3 aurora_dir = vec3(0.2, 0.0, -1.0);
// the ash cloud and its lightning
uniform float ash = 0.0;
uniform vec3 ash_dir = vec3(0.3, 0.15, -0.95);
uniform vec3 ash_col : source_color = vec3(0.05, 0.04, 0.04);
uniform vec3 ash_lit : source_color = vec3(0.6, 0.15, 0.05);
uniform float bolt = 0.0;
uniform vec3 bolt_dir = vec3(0.3, 0.2, -0.95);
// explosions
uniform vec4 boom_dir[4];
uniform vec4 boom_col[4];

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

float vnoise3(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	float a = mix(mix(hash3(i), hash3(i + vec3(1, 0, 0)), u.x), mix(hash3(i + vec3(0, 1, 0)), hash3(i + vec3(1, 1, 0)), u.x), u.y);
	float b = mix(mix(hash3(i + vec3(0, 0, 1)), hash3(i + vec3(1, 0, 1)), u.x), mix(hash3(i + vec3(0, 1, 1)), hash3(i + vec3(1, 1, 1)), u.x), u.y);
	return mix(a, b, u.z);
}

float fbm3(vec3 p) {
	float v = 0.0, a = 0.5;
	for (int i = 0; i < 5; i++) {
		v += a * vnoise3(p);
		p = p * 2.07 + vec3(1.7, 9.2, 4.1);
		a *= 0.5;
	}
	return v;
}

vec3 rotate(vec3 v, vec3 k, float a) {
	return v * cos(a) + cross(k, v) * sin(a) + k * dot(k, v) * (1.0 - cos(a));
}

vec3 gradient(vec3 d) {
	float e = d.y;
	vec3 c = mix(horizon_col, mid_col, smoothstep(0.0, mid_height, e));
	c = mix(c, top_col, smoothstep(mid_height, 1.0, e));
	vec2 hd = normalize(d.xz + vec2(1e-5));
	if (glow > 0.0) {
		float az = max(dot(hd, normalize(glow_dir.xz)), 0.0);
		float g = pow(az, glow_spread) * exp(-max(e, 0.0) * glow_rise);
		c = mix(c, glow_col, clamp(glow * g, 0.0, 1.0));
		c += glow_col * glow * 0.25 * pow(az, glow_spread * 0.5) * exp(-max(e, 0.0) * glow_rise * 0.4);
	}
	if (belt > 0.0) {
		float az = max(-dot(hd, normalize(glow_dir.xz)), 0.0) * 0.6 + 0.4;
		float b = exp(-pow((e - 0.07) / 0.06, 2.0)) * az;
		c = mix(c, belt_col, clamp(belt * b, 0.0, 1.0));
	}
	return c;
}

vec3 planet_at(vec3 d, vec3 c) {
	vec3 pd = normalize(planet_dir);
	float ang = acos(clamp(dot(d, pd), -1.0, 1.0));
	float R = planet_size;
	vec3 L = normalize(planet_light);
	if (ang > R * 1.35) {
		return c;
	}
	vec3 tu = normalize(cross(vec3(0.0, 1.0, 0.0), pd));
	vec3 tv = cross(pd, tu);
	vec2 p = vec2(dot(d, tu), dot(d, tv)) / sin(R);
	float r2 = dot(p, p);
	// the air round the rim, on the lit side
	vec3 rimn = normalize(p.x * tu + p.y * tv);
	float day = smoothstep(-0.35, 0.5, dot(rimn, L));
	if (r2 >= 1.0) {
		float o = sqrt(r2) - 1.0;
		c += vec3(0.25, 0.5, 1.0) * exp(-o * 26.0) * day * 0.9 * planet;
		return c;
	}
	vec3 n = normalize(p.x * tu + p.y * tv - sqrt(1.0 - r2) * pd);
	vec3 axis = normalize(tv * 0.92 + tu * 0.35);
	vec3 q = rotate(n, axis, clock * planet_spin);
	float lat = dot(q, axis);
	float land = fbm3(q * 2.2 + vec3(3.1, 1.7, 0.4)) + 0.12 * fbm3(q * 9.0);
	float ocean_k = smoothstep(0.53, 0.5, land);
	vec3 ocean = mix(vec3(0.02, 0.08, 0.22), vec3(0.04, 0.16, 0.36), smoothstep(0.5, 0.42, land));
	float dry = fbm3(q * 3.5 + 7.0);
	vec3 ground = mix(vec3(0.12, 0.2, 0.08), vec3(0.42, 0.33, 0.2), smoothstep(0.45, 0.6, dry));
	ground = mix(ground, vec3(0.32, 0.3, 0.26), smoothstep(0.62, 0.72, land));
	vec3 surf = mix(ground, ocean, ocean_k);
	float ice = smoothstep(0.78, 0.86, abs(lat) + 0.05 * fbm3(q * 6.0));
	surf = mix(surf, vec3(0.85, 0.9, 0.95), ice);
	// clouds: bands and swirls drifting slowly over the ground
	vec3 qc = rotate(n, axis, clock * planet_spin * 1.3 + 0.7);
	float sw = fbm3(qc * 3.0 + vec3(0.0, lat * 4.0, 0.0));
	float cl = smoothstep(0.48, 0.68, fbm3(qc * vec3(4.0, 9.0, 4.0) * 0.6 + sw * 1.6));
	surf = mix(surf, vec3(0.95), cl * 0.85);
	float ndl = dot(n, L);
	float lit = smoothstep(-0.08, 0.3, ndl);
	vec3 col = surf * (0.015 + 1.35 * max(ndl, 0.0));
	// a glint of the sun on the oceans
	vec3 h = normalize(L - d);
	col += vec3(1.0, 0.9, 0.75) * pow(max(dot(n, h), 0.0), 60.0) * ocean_k * (1.0 - cl) * 0.6 * lit;
	// cities on the night side
	float city = step(0.86, vnoise3(q * 60.0)) * (1.0 - ocean_k) * (1.0 - ice) * (1.0 - cl);
	col += vec3(1.0, 0.7, 0.35) * city * (1.0 - smoothstep(-0.2, 0.05, ndl)) * 0.5;
	// the thin air at the limb
	float limb = pow(1.0 - sqrt(1.0 - r2), 3.0);
	col += vec3(0.3, 0.55, 1.0) * limb * (0.15 + 0.85 * day) * 0.9;
	col = mix(c, col, smoothstep(1.0, 0.985, r2) * planet);
	return col;
}

vec3 aurora_at(vec3 d, vec3 c) {
	if (d.y <= 0.0) {
		return c;
	}
	vec3 acc = vec3(0.0);
	vec2 ad = normalize(aurora_dir.xz);
	mat2 rot = mat2(vec2(ad.y, -ad.x), vec2(ad.x, ad.y));
	for (int i = 0; i < 22; i++) {
		float fi = float(i) / 21.0;
		float h = 1.0 + fi * 1.6;
		vec2 p = rot * (d.xz / (d.y + 0.035)) * h * 0.55;
		float t = clock * 0.05;
		// the curtain's line wanders across the sky and ripples
		float line = 5.5 + 2.2 * sin(p.x * 0.45 + t * 2.0) + 1.2 * sin(p.x * 1.1 - t * 1.3 + 1.0)
				+ (fbm(vec2(p.x * 0.2 + t, 3.0)) - 0.5) * 5.0;
		float second = 9.0 + 1.8 * sin(p.x * 0.7 - t * 3.0 + 2.0) + (fbm(vec2(p.x * 0.3 - t, 7.0)) - 0.5) * 3.0;
		float dd = min(abs(p.y - line), abs(p.y - second) * 1.25);
		float band = exp(-dd * 2.6);
		float along = p.x + 0.35 * (p.y - line);
		float rays = pow(vnoise(vec2(along * 6.0 + t * 6.0, t * 4.0)), 2.0) * 0.8 + 0.25;
		rays *= 0.5 + 0.5 * vnoise(vec2(along * 1.7 - t * 3.0, 1.0));
		float patch = smoothstep(0.2, 0.6, fbm(vec2(p.x * 0.06 + t * 0.4, 11.0)));
		vec3 col = mix(aurora_low, aurora_high, smoothstep(0.3, 1.0, fi));
		acc += col * band * rays * patch * (1.0 - fi * 0.7) * 0.2;
	}
	float fade = smoothstep(0.0, 0.08, d.y) * (0.75 + 0.25 * sin(clock * 0.21));
	return c + acc * aurora * fade;
}

vec3 sky(vec3 d) {
	float e = d.y;
	vec3 c = gradient(d);
	float above = smoothstep(-0.005, 0.04, e);
	if (stars > 0.0 && e > 0.0) {
		vec3 p = d * 340.0;
		vec3 cell = floor(p);
		float h = hash3(cell);
		vec3 f = fract(p) - 0.5;
		float star = step(1.0 - 0.06 * stars, h) * smoothstep(0.34, 0.0, length(f));
		float big = step(0.995, h);
		float tw = 0.6 + 0.4 * sin(clock * (1.3 + h * 4.0) + h * 60.0);
		vec3 sc = mix(vec3(0.7, 0.82, 1.0), vec3(1.0, 0.86, 0.7), fract(h * 13.0));
		float day = 1.0 - smoothstep(0.1, 0.5, dot(c, vec3(0.33)));
		c += sc * star * tw * (0.9 + big * 2.2) * smoothstep(0.02, 0.25, e) * stars * day;
		if (dust > 0.0) {
			vec3 bn = normalize(dust_axis);
			float bd = exp(-pow(dot(d, bn) * 3.0, 2.0));
			if (bd > 0.02) {
				float dn = fbm(d.xy * 6.0 + d.z * 3.0) * fbm(d.yz * 11.0 + 2.0);
				float lane = smoothstep(0.35, 0.6, fbm(d.xz * 14.0 + 5.0));
				c += mix(vec3(0.3, 0.3, 0.45), vec3(0.55, 0.45, 0.4), dn) * bd * dn * (1.0 - 0.6 * lane) * 0.6 * dust * smoothstep(0.02, 0.3, e);
				float fine = step(0.985, hash3(floor(d * 900.0))) * bd;
				c += vec3(0.8, 0.85, 1.0) * fine * 0.5 * dust;
			}
		}
	}
	if (sun_disc > 0.0) {
		vec3 sd = normalize(sun_dir);
		float m = dot(d, sd);
		float a = acos(clamp(m, -1.0, 1.0));
		c = mix(c, sun_col * 3.0, smoothstep(sun_size, sun_size * 0.92, a) * sun_disc);
		c += sun_col * sun_halo * (exp(-a * a / (sun_size * sun_size * 9.0)) * 0.6 + exp(-a * 9.0) * 0.25);
	}
	if (moon > 0.0) {
		vec3 md = normalize(moon_dir);
		float a = acos(clamp(dot(d, md), -1.0, 1.0));
		float disc = smoothstep(moon_size, moon_size * 0.94, a);
		float mare = 0.78 + 0.22 * fbm(d.xy * 220.0 + d.z * 60.0);
		c = mix(c, moon_col * mare * 1.4, disc * moon);
		c += moon_col * moon * (exp(-a * a / (moon_size * moon_size * 16.0)) * 0.12 + exp(-a * 6.0) * 0.04);
	}
	if (planet > 0.0) {
		c = planet_at(d, c);
	}
	if (aurora > 0.0) {
		c = aurora_at(d, c);
	}
	if (clouds > 0.0 && e > 0.0) {
		vec2 uv = d.xz / (e + 0.1) * 0.55 * cloud_scale + vec2(clock * 0.004, clock * 0.0015);
		vec2 lu = normalize(cloud_light.xz) * 0.06;
		float n;
		float nl;
		if (cloud_streak > 0.5) {
			uv = uv * vec2(0.35, 2.2);
			n = fbm(uv + vec2(fbm(uv * 0.6) * 0.8, 0.0));
			nl = n;
		} else {
			n = fbm(uv + 0.4 * vec2(fbm(uv * 0.5 + 3.0), fbm(uv * 0.5 + 7.0)));
			nl = fbm(uv + lu * 3.0 + 0.4 * vec2(fbm(uv * 0.5 + lu * 1.5 + 3.0), fbm(uv * 0.5 + lu * 1.5 + 7.0)));
		}
		float th = 1.0 - clouds * 0.6;
		float dens = smoothstep(th, th + 0.18, n) * smoothstep(0.0, 0.1, e);
		float shade = clamp((n - nl) * 6.0 + 0.5, 0.0, 1.0);
		vec2 hd = normalize(d.xz + vec2(1e-5));
		float toward = max(dot(hd, normalize(cloud_light.xz)), 0.0);
		vec3 cc = mix(cloud_shade, cloud_col, shade);
		cc = mix(cc, cloud_lit, (1.0 - shade * 0.5) * pow(toward, 2.0) * smoothstep(0.6, 0.0, e));
		cc += cloud_lit * 0.6 * smoothstep(th + 0.18, th, n) * dens * pow(toward, 3.0);   // silver edges
		cc = mix(cc, horizon_col, smoothstep(0.15, 0.0, e) * 0.7);
		c = mix(c, cc, dens * 0.92);
	}
	if (ash > 0.0) {
		vec3 ad = normalize(ash_dir);
		vec2 hd = normalize(d.xz + vec2(1e-5));
		float az = dot(hd, normalize(ad.xz));
		float spread = smoothstep(0.75, 0.995, az);
		vec2 uv = vec2(atan(d.x, -d.z) * 3.0 + clock * 0.004, e * 9.0 - clock * 0.006);
		uv = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * uv;
		float n = fbm(uv * 1.4 + vec2(fbm(uv * 0.7 + 3.0), fbm(uv * 0.7)) * 1.2);
		float band = smoothstep(ad.y - 0.03, ad.y + 0.08, e) * smoothstep(0.75, 0.3, e);
		float dens = smoothstep(0.3, 0.75, n) * spread * band;
		vec3 ac = mix(ash_lit, ash_col, smoothstep(ad.y, ad.y + 0.25, e));
		ac += vec3(0.9, 0.85, 1.0) * bolt * exp(-pow(acos(clamp(dot(d, normalize(bolt_dir)), -1.0, 1.0)) * 6.0, 2.0)) * 1.2;
		c = mix(c, ac, dens * ash);
	}
	if (bolt > 0.0) {
		float a = acos(clamp(dot(d, normalize(bolt_dir)), -1.0, 1.0));
		c += vec3(0.6, 0.6, 0.9) * bolt * exp(-a * 7.0) * 0.6;
	}
	for (int i = 0; i < 4; i++) {
		float s = boom_dir[i].w;
		if (s > 0.0) {
			float a = acos(clamp(dot(d, boom_dir[i].xyz), -1.0, 1.0));
			c += boom_col[i].rgb * (exp(-a * a / (s * s)) + 0.3 * exp(-a * a / (s * s * 9.0)));
		}
	}
	return c * mix(0.85, 1.0, above);
}

void fragment() {
	vec3 d = normalize(dir);
	vec3 c;
	if (d.y >= 0.0) {
		c = sky(d);
	} else {
		c = mix(gradient(vec3(d.x, 0.0, d.z)), below_col, smoothstep(0.0, 0.08, -d.y));
	}
	ALBEDO = c;
}
