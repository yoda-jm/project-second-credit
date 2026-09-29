// Nova Wardens night sky: a dome round the camera. A deep gradient down to a hazy horizon that sits where the sea
// ends (horizon_e, below eye level), the city's warm glow low over the bay, the nebula and the Milky Way, dense
// twinkling stars, a huge moon with maria, rays and a halo, a small ringed planet, high moonlit clouds drifting,
// a meteor now and then, a flash for big explosions and the red pulse of the air-raid alarm.
// Everything moves on `clock` (the backdrop's own time). The middle of the screen (calm_rect, in screen UV) is kept
// quieter so the play reads. Unshaded and unfogged: it is the horizon the fog fades into.
shader_type spatial;
render_mode unshaded, cull_front, fog_disabled, shadows_disabled, depth_draw_never;

#include "res://games/novawardens/shaders/nova_noise.gdshaderinc"
#include "res://games/novawardens/shaders/nova_stars.gdshaderinc"
#include "res://games/novawardens/shaders/nova_nebula.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 top_col : source_color = vec3(0.01, 0.015, 0.05);
uniform vec3 mid_col : source_color = vec3(0.03, 0.05, 0.13);
uniform vec3 horizon_col : source_color = vec3(0.14, 0.16, 0.3);
uniform vec3 below_col : source_color = vec3(0.05, 0.07, 0.14);
uniform float horizon_e = -0.09;
uniform vec3 city_glow_col : source_color = vec3(1.0, 0.55, 0.3);
uniform vec3 city_dir = vec3(0.1, 0.0, -1.0);
uniform float city_glow = 0.11;
uniform float star_amount = 1.0;
uniform vec3 band_axis = vec3(0.55, 0.35, 0.75);
uniform vec4 calm_rect = vec4(0.29, 0.02, 0.71, 0.86);  // x0, y0, x1, y1 in screen UV (y down)
uniform float calm = 0.8;
// the moon
uniform vec3 moon_dir = vec3(0.4, 0.21, -0.89);
uniform float moon_radius = 0.07;   // radians
uniform vec3 moon_col : source_color = vec3(0.92, 0.94, 1.0);
uniform float moon_energy = 1.25;
uniform vec3 moon_light = vec3(-0.3, 0.2, 1.0);   // where the moon's sunlight comes from, in its disc frame
// the planet
uniform vec3 planet_dir = vec3(-0.38, 0.24, -0.89);
uniform float planet_radius = 0.016;
uniform vec3 planet_a : source_color = vec3(0.85, 0.62, 0.45);
uniform vec3 planet_b : source_color = vec3(0.45, 0.62, 0.8);
// clouds
uniform float cloud_amount = 0.3;
uniform vec3 cloud_col : source_color = vec3(0.05, 0.06, 0.12);
uniform vec3 cloud_lit : source_color = vec3(0.3, 0.34, 0.5);
uniform float cloud_speed = 0.006;
// events
uniform vec3 meteor_a = vec3(0.0, 1.0, 0.0);
uniform vec3 meteor_b = vec3(0.0, 1.0, 0.0);
uniform float meteor_t = -1.0;      // 0..1 along the path, < 0 when there is none
uniform float meteor_tail = 0.35;
uniform vec3 flash_dir = vec3(0.0, 0.3, -1.0);
uniform float flash = 0.0;
uniform vec3 flash_col : source_color = vec3(1.0, 0.85, 0.7);
uniform float alarm = 0.0;
uniform float alarm_pulse = 0.0;

varying vec3 dir;

void vertex() {
	dir = VERTEX;
}

// a frame on the sky round direction `a`: returns (x, y) in radians-ish
vec2 sky_frame(vec3 d, vec3 a) {
	vec3 r = normalize(cross(vec3(0.0, 1.0, 0.0), a));
	vec3 u = cross(a, r);
	return vec2(dot(d, -r), dot(d, u)) / max(dot(d, a), 1e-3);
}

float crater_field(vec2 uv, float scale, float seed) {
	vec2 p = uv * scale;
	vec2 cell = floor(p);
	float v = 0.0;
	for (int j = -1; j <= 1; j++) {
		for (int i = -1; i <= 1; i++) {
			vec2 c = cell + vec2(float(i), float(j));
			float h = nw_hash(c + seed);
			vec2 o = c + vec2(nw_hash(c + seed + 3.1), nw_hash(c + seed + 7.7));
			float r = 0.15 + 0.3 * h;
			float dd = length(p - o) / r;
			// a dark floor and a bright rim
			v += (smoothstep(1.0, 0.6, dd) * -0.3 + smoothstep(0.7, 1.0, dd) * smoothstep(1.3, 1.0, dd) * 0.3)
					* step(0.78, h);
		}
	}
	return v;
}

void fragment() {
	vec3 d = normalize(dir);
	float e = d.y;
	float e2 = (e - horizon_e) / (1.0 - horizon_e);   // 0 at the sea's horizon, 1 overhead
	vec2 suv = SCREEN_UV;
	float calm_k = calm * smoothstep(calm_rect.x - 0.03, calm_rect.x + 0.05, suv.x)
			* (1.0 - smoothstep(calm_rect.z - 0.05, calm_rect.z + 0.03, suv.x))
			* smoothstep(calm_rect.y - 0.02, calm_rect.y + 0.04, suv.y)
			* (1.0 - smoothstep(calm_rect.w - 0.06, calm_rect.w, suv.y));
	vec3 c;
	if (e2 >= 0.0) {
		c = mix(horizon_col, mid_col, smoothstep(0.0, 0.14, e2));
		c = mix(c, top_col, smoothstep(0.1, 0.6, e2));
	} else {
		c = mix(horizon_col, below_col, smoothstep(0.0, 0.05, -e2));
	}
	// the city's sodium glow over the bay, and the red of the alarm pulsing in it
	vec3 cd = normalize(city_dir);
	float az = max(dot(normalize(vec3(d.x, 0.0, d.z)), normalize(vec3(cd.x, 0.0, cd.z))), 0.0);
	float low = exp(-max(e2, 0.0) * 14.0) * step(-0.02, e2);
	c += city_glow_col * city_glow * low * pow(az, 6.0);
	c += vec3(1.0, 0.08, 0.04) * alarm * (0.3 + 0.7 * alarm_pulse) * low * pow(az, 2.0) * 0.6;
	// and higher up, a faint red wash in time with the sirens
	c += vec3(0.5, 0.03, 0.02) * alarm * alarm_pulse * exp(-max(e2, 0.0) * 4.0) * 0.12;
	float above = smoothstep(-0.005, 0.03, e2);
	// nebula, galaxy and stars (quieter over the play field)
	vec3 sky_light = nw_nebula(d, clock) * (1.0 - 0.7 * calm_k);
	sky_light += nw_band(d, band_axis) * (1.0 - 0.5 * calm_k);
	sky_light *= smoothstep(0.0, 0.25, e2);
	vec3 st = nw_stars(d, clock, star_amount, calm_k) * smoothstep(0.01, 0.12, e2);
	// the moon
	vec3 md = normalize(moon_dir);
	float cm = dot(d, md);
	float ang = acos(clamp(cm, -1.0, 1.0));
	vec2 muv = sky_frame(d, md) / moon_radius;
	float mr = length(muv);
	float disc = smoothstep(1.0, 0.985, mr) * step(0.0, cm);
	vec3 moon_c = vec3(0.0);
	float occl = 0.0;
	if (disc > 0.0) {
		vec3 n = vec3(muv, sqrt(max(1.0 - mr * mr, 0.0)));
		vec2 tuv = muv * 1.3;
		// maria: broad dark seas; highlands with fine mottling; a few craters, one with rays
		float maria = smoothstep(0.48, 0.66, nw_fbm(tuv * 0.9 + vec2(3.1, 1.7), 5));
		maria = max(maria, smoothstep(0.52, 0.68, nw_fbm(tuv * 1.5 + vec2(9.2, 4.4), 4)) * 0.85);
		float alb = 0.95 - 0.42 * maria + 0.1 * (nw_fbm(tuv * 9.0, 4) - 0.5);
		alb += crater_field(tuv, 5.0, 1.0) * 0.2 + crater_field(tuv, 13.0, 5.0) * 0.08;
		vec2 rc = muv - vec2(-0.22, -0.58);
		float rays = pow(max(0.0, sin(atan(rc.y, rc.x) * 13.0 + nw_noise(rc * 8.0) * 3.0) * 0.5 + 0.5), 5.0)
				* exp(-length(rc) * 3.0);
		alb += rays * 0.22 + smoothstep(0.06, 0.02, length(rc)) * 0.35;
		float lit = smoothstep(-0.08, 0.2, dot(n, normalize(moon_light)));
		float limb = 0.55 + 0.45 * pow(n.z, 0.4);
		moon_c = moon_col * mix(vec3(1.0), vec3(1.0, 0.95, 0.86), maria) * moon_energy * alb * limb * mix(0.03, 1.0, lit);
		occl = disc;
	}
	float halo = exp(-pow(ang / (moon_radius * 1.8), 2.0)) * 0.35 + exp(-ang / (moon_radius * 5.0)) * 0.16
			+ exp(-ang / (moon_radius * 16.0)) * 0.05;
	// the planet: banded, half lit, with a tilted ring
	vec2 puv = sky_frame(d, normalize(planet_dir)) / planet_radius;
	float pr = length(puv);
	vec3 pl_c = vec3(0.0);
	float pl_occl = 0.0;
	{
		mat2 tilt = mat2(vec2(0.94, 0.34), vec2(-0.34, 0.94));
		vec2 ruv = tilt * puv;
		float rr = length(vec2(ruv.x, ruv.y / 0.28));
		float ring = smoothstep(1.35, 1.42, rr) * smoothstep(2.25, 2.15, rr) * (0.55 + 0.45 * sin(rr * 40.0));
		ring *= 1.0 - 0.6 * smoothstep(1.75, 1.8, rr) * smoothstep(1.86, 1.81, rr);
		bool front = ruv.y < 0.0;
		float body = smoothstep(1.0, 0.95, pr);
		if (body > 0.0) {
			vec3 n = vec3(puv, sqrt(max(1.0 - pr * pr, 0.0)));
			vec2 bu = tilt * puv;
			float bands = nw_noise(vec2(bu.y * 7.0, bu.x * 0.8 + 2.0)) * 0.6 + 0.4 * sin(bu.y * 11.0);
			vec3 pc = mix(planet_a, planet_b, smoothstep(-0.3, 0.8, bands));
			float lit = clamp(dot(n, normalize(vec3(0.7, 0.3, 0.5))), 0.0, 1.0);
			pl_c = pc * (0.02 + 1.1 * lit) * 0.9;
			pl_occl = body;
			// the ring's shadow on the body
			pl_c *= 1.0 - 0.5 * smoothstep(0.02, 0.0, abs(bu.y + 0.12)) * step(0.0, bu.x);
		}
		vec3 ring_c = mix(planet_a, vec3(0.9, 0.85, 0.8), 0.5) * ring * 0.6;
		if (front) {
			pl_c = mix(pl_c, ring_c, ring * 0.85);
			pl_occl = max(pl_occl, ring * 0.85);
		} else if (body < 0.5) {
			pl_c += ring_c;
			pl_occl = max(pl_occl, ring * 0.85);
		}
		pl_c += planet_b * exp(-pr * 1.6) * 0.05;   // a faint haze round it
	}
	// clouds: thin high sheets drifting, their edges silvered on the moon's side
	float cloud = 0.0;
	vec3 cloud_c = vec3(0.0);
	if (cloud_amount > 0.0 && e2 > 0.0) {
		vec2 uv = d.xz / (e2 + 0.12) * 0.55 + vec2(clock * cloud_speed, clock * cloud_speed * 0.35);
		float n = nw_fbm(uv * vec2(1.0, 2.6), 5);
		float n2 = nw_fbm(uv * vec2(1.0, 2.6) + normalize(md.xz) * 0.06, 5);
		float dens = smoothstep(0.62 - cloud_amount * 0.25, 0.95 - cloud_amount * 0.2, n);
		dens *= smoothstep(0.0, 0.08, e2) * (1.0 - 0.55 * smoothstep(0.25, 0.7, e2)) * 0.9;
		float moonward = exp(-ang * 2.2);
		float rim = clamp((n - n2) * 9.0 + 0.2, 0.0, 1.0);
		cloud_c = mix(cloud_col, cloud_lit, clamp(rim * 0.5 + moonward * 0.9, 0.0, 1.0));
		cloud_c += moon_col * moonward * moonward * 0.25;
		cloud_c += flash_col * flash * 0.9 * pow(max(dot(d, normalize(flash_dir)), 0.0), 12.0);
		cloud = dens;
	}
	c += sky_light * above;
	c += st * (1.0 - occl) * (1.0 - pl_occl);
	c = mix(c, pl_c, pl_occl * above);
	c += pl_c * (1.0 - pl_occl) * above;
	c = mix(c, moon_c, occl);
	c += moon_col * halo * 0.3;
	c = mix(c, cloud_c + moon_c * 0.25, cloud * (1.0 - occl * 0.5));
	// the meteor: a streak along the great circle from meteor_a to meteor_b, bright at its head
	if (meteor_t >= 0.0) {
		vec3 a = normalize(meteor_a), b = normalize(meteor_b);
		vec3 nrm = normalize(cross(a, b));
		float span = acos(clamp(dot(a, b), -1.0, 1.0));
		vec3 side = cross(nrm, a);
		float along = atan(dot(d, side), dot(d, a)) / span;
		float off = abs(dot(d, nrm));
		float head = meteor_t;
		float tail = head - meteor_tail;
		float k = smoothstep(tail, head, along) * step(along, head + 0.004);
		float w = 0.0009 + 0.0012 * k;
		float fade = smoothstep(0.0, 0.15, meteor_t) * (1.0 - smoothstep(0.75, 1.0, meteor_t));
		float line = smoothstep(w, 0.0, off) * k * k * fade;
		float hd = exp(-pow(length(vec2((along - head) * span, off)) / 0.004, 2.0)) * fade;
		c += vec3(0.8, 0.9, 1.0) * (line * 3.0 + hd * 4.0) * (1.0 - cloud * 0.8) * (1.0 - occl) * (1.0 - pl_occl);
	}
	// a flash in the sky (a big explosion or the mothership going down)
	float fd = max(dot(d, normalize(flash_dir)), 0.0);
	c += flash_col * flash * (pow(fd, 40.0) * 0.35 + pow(fd, 8.0) * 0.08 + 0.008);
	ALBEDO = c;
}
