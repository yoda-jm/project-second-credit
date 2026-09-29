// Nova Wardens night sky: a dome round the camera. A deep gradient down to a hazy horizon that sits where the sea
// ends (horizon_e, below eye level), a faint airglow and the town's warm glow low over the bay, the baked deep sky
// (nebula and Milky Way: `pano`, made once by nova_sky_bake), dense twinkling stars, a gibbous moon with maria, rayed
// craters in relief along the terminator, earthshine and a halo, a small ringed planet, two layers of drifting clouds
// silvered by the moon (a high veil and a low broken bank), a faint aurora over the left-hand hills, a distant storm on
// the right-hand horizon whose clouds light up now and then (storm, storm_at, storm_bolt, set by the backdrop),
// satellites crossing, a meteor now and then, a flash for big explosions and the red pulse of the air-raid alarm.
// Everything moves on `clock` (the backdrop's own time). The middle of the screen (calm_rect, in screen UV) is kept
// quieter so the play reads. Unshaded and unfogged: it is the horizon the fog fades into.
shader_type spatial;
render_mode unshaded, cull_front, fog_disabled, shadows_disabled, depth_draw_never;

#include "res://games/novawardens/shaders/nova_noise.gdshaderinc"
#include "res://games/novawardens/shaders/nova_stars.gdshaderinc"

uniform float clock = 0.0;
uniform vec3 top_col : source_color = vec3(0.01, 0.015, 0.05);
uniform vec3 mid_col : source_color = vec3(0.03, 0.05, 0.13);
uniform vec3 horizon_col : source_color = vec3(0.14, 0.16, 0.3);
uniform vec3 below_col : source_color = vec3(0.05, 0.07, 0.14);
uniform float horizon_e = -0.09;
uniform vec3 city_glow_col : source_color = vec3(1.0, 0.55, 0.3);
uniform vec3 city_dir = vec3(0.1, 0.0, -1.0);
uniform float city_glow = 0.11;
uniform vec3 airglow_col : source_color = vec3(0.1, 0.2, 0.14);
uniform float airglow = 0.25;
uniform float star_amount = 1.0;
uniform vec4 calm_rect = vec4(0.29, 0.02, 0.71, 0.86);  // x0, y0, x1, y1 in screen UV (y down)
uniform float calm = 0.8;
// the baked deep sky
uniform sampler2D pano : filter_linear, repeat_disable;
uniform vec4 pano_rect = vec4(-1.1, 1.1, 0.62, -0.12);  // az0, az1, el_top, el_bottom (radians)
uniform float pano_gain = 1.0;
// the moon
uniform vec3 moon_dir = vec3(0.4, 0.21, -0.89);
uniform float moon_radius = 0.07;   // radians
uniform vec3 moon_col : source_color = vec3(0.92, 0.94, 1.0);
uniform float moon_energy = 1.25;
uniform vec3 moon_light = vec3(0.62, 0.22, 0.75);   // where the moon's sunlight comes from, in its disc frame
uniform float moon_bump = 0.5;
// the planet
uniform vec3 planet_dir = vec3(-0.38, 0.24, -0.89);
uniform float planet_radius = 0.016;
uniform vec3 planet_a : source_color = vec3(0.85, 0.62, 0.45);
uniform vec3 planet_b : source_color = vec3(0.45, 0.62, 0.8);
// clouds (two tiling noise textures, with mipmaps)
uniform sampler2D cloud_a : filter_linear_mipmap, repeat_enable;
uniform sampler2D cloud_b : filter_linear_mipmap, repeat_enable;
uniform float cloud_amount = 0.25;
uniform vec3 cloud_col : source_color = vec3(0.045, 0.055, 0.1);
uniform vec3 cloud_lit : source_color = vec3(0.34, 0.38, 0.54);
uniform float cloud_speed = 0.005;
// the aurora
uniform float aurora = 1.0;
uniform vec3 aurora_a : source_color = vec3(0.15, 1.0, 0.55);
uniform vec3 aurora_b : source_color = vec3(0.55, 0.25, 1.0);
uniform vec2 aurora_az = vec2(-0.56, -0.1);
// the storm
uniform vec2 storm_az = vec2(0.1, 0.34);
uniform float storm = 0.0;
uniform float storm_at = 0.4;
uniform float storm_bolt = 0.0;
uniform float storm_seed = 0.0;
uniform vec3 storm_col : source_color = vec3(0.75, 0.8, 1.0);
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

// craters as a height field: bowls with raised rims and ejecta aprons, one cell in (1 - dens) holds one
float crater_h(vec2 p, float seed, float dens) {
	vec2 cell = floor(p);
	float h = 0.0;
	for (int j = -1; j <= 1; j++) {
		for (int i = -1; i <= 1; i++) {
			vec2 c = cell + vec2(float(i), float(j));
			float r0 = nw_hash(c + seed);
			if (r0 > dens) {
				vec2 o = c + 0.2 + 0.6 * vec2(nw_hash(c + seed + 3.1), nw_hash(c + seed + 7.7));
				float r = 0.18 + 0.3 * fract(r0 * 13.7);
				float dd = length(p - o) / r;
				h += dd < 1.0 ? (dd * dd - 1.0) * 0.55 + 0.3 * smoothstep(0.6, 1.0, dd) + 0.15 * exp(-dd * dd * 40.0)
						: 0.3 * exp(-(dd - 1.0) * 4.0);
			}
		}
	}
	return h;
}

float moon_h(vec2 p) {
	return crater_h(p * 3.2, 1.0, 0.7) * 0.6 + crater_h(p * 7.5, 5.0, 0.55) * 0.25 + crater_h(p * 17.0, 9.0, 0.45) * 0.1;
}

// a satellite on the great circle through a and b, angular speed w (rad/s)
float satellite(vec3 d, vec3 a, vec3 b, float w, float ph) {
	vec3 u = normalize(a);
	vec3 v = normalize(b - dot(b, u) * u);
	float th = mod(clock * w + ph, 6.2832) - 1.0;
	vec3 p = u * cos(th) + v * sin(th);
	float k = max(1.0 - dot(d, p), 0.0);
	return exp(-k / 6e-7);
}

void fragment() {
	vec3 d = normalize(dir);
	float e = d.y;
	float e2 = (e - horizon_e) / (1.0 - horizon_e);   // 0 at the sea's horizon, 1 overhead
	float az = atan(d.x, -d.z);
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
	// airglow: a faint green band a little above the horizon
	c += airglow_col * airglow * exp(-abs(e2 - 0.05) * 22.0) * step(0.0, e2);
	// the town's sodium glow over the bay, and the red of the alarm pulsing in it
	vec3 cd = normalize(city_dir);
	float azk = max(dot(normalize(vec3(d.x, 0.0, d.z)), normalize(vec3(cd.x, 0.0, cd.z))), 0.0);
	float low = exp(-max(e2, 0.0) * 14.0) * step(-0.02, e2);
	c += city_glow_col * city_glow * low * pow(azk, 6.0);
	c += vec3(1.0, 0.08, 0.04) * alarm * (0.3 + 0.7 * alarm_pulse) * low * pow(azk, 2.0) * 0.6;
	// and higher up, a faint red wash in time with the sirens
	c += vec3(0.5, 0.03, 0.02) * alarm * alarm_pulse * exp(-max(e2, 0.0) * 4.0) * 0.12;
	float above = smoothstep(-0.005, 0.03, e2);
	// the baked nebula and Milky Way (quieter over the play field)
	vec2 puv = vec2((az - pano_rect.x) / (pano_rect.y - pano_rect.x), (asin(clamp(e, -1.0, 1.0)) - pano_rect.z)
			/ (pano_rect.w - pano_rect.z));
	vec3 deep = texture(pano, puv).rgb;
	deep *= deep * pano_gain * (1.0 - 0.65 * calm_k) * smoothstep(0.0, 0.2, e2);
	deep *= smoothstep(0.0, 0.03, puv.x) * smoothstep(1.0, 0.97, puv.x);
	vec3 st = nw_stars(d, clock, star_amount, calm_k) * smoothstep(0.01, 0.12, e2);
	// the moon
	vec3 md = normalize(moon_dir);
	float cm = dot(d, md);
	float ang = acos(clamp(cm, -1.0, 1.0));
	vec3 moon_c = vec3(0.0);
	float occl = 0.0;
	if (ang < moon_radius * 1.05) {
		vec2 muv = sky_frame(d, md) / moon_radius;
		float mr = length(muv);
		float disc = smoothstep(1.0, 0.985, mr);
		vec3 n = vec3(muv, sqrt(max(1.0 - mr * mr, 0.0)));
		// surface coordinates on the sphere (craters foreshorten towards the limb)
		vec2 sp = vec2(atan(n.x, n.z), asin(clamp(n.y, -1.0, 1.0))) * 1.25;
		float maria = smoothstep(0.47, 0.64, nw_fbm(sp * 1.1 + vec2(3.1, 1.7), 5));
		maria = max(maria, smoothstep(0.52, 0.66, nw_fbm(sp * 1.8 + vec2(9.2, 4.4), 4)) * 0.85);
		float alb = 0.95 - 0.42 * maria + 0.12 * (nw_fbm(sp * 11.0, 4) - 0.5);
		// the relief: craters (fewer and softer in the maria), shading from their slopes
		float ep = 0.012;
		float h0 = moon_h(sp);
		float hx = moon_h(sp + vec2(ep, 0.0));
		float hy = moon_h(sp + vec2(0.0, ep));
		vec2 g = vec2(hx - h0, hy - h0) / ep * (1.0 - 0.6 * maria) * 0.012;
		vec3 t = normalize(vec3(n.z, 0.0, -n.x) + vec3(1e-4, 0.0, 0.0));
		vec3 b = cross(n, t);
		vec3 nb = normalize(n - (t * g.x + b * g.y) * moon_bump * 10.0);
		alb += h0 * 0.05 * (1.0 - maria);
		// a young rayed crater
		vec2 rc = muv - vec2(-0.22, -0.55);
		float rays = pow(max(0.0, sin(atan(rc.y, rc.x) * 13.0 + nw_noise(rc * 8.0) * 3.0) * 0.5 + 0.5), 5.0)
				* exp(-length(rc) * 2.6);
		alb += rays * 0.2 + smoothstep(0.06, 0.02, length(rc)) * 0.35;
		vec3 L = normalize(moon_light);
		float lit = smoothstep(-0.06, 0.25, dot(nb, L)) * smoothstep(-0.15, 0.05, dot(n, L));
		float earthshine = 0.035;
		float limb = 0.75 + 0.25 * pow(n.z, 0.5);
		moon_c = moon_col * mix(vec3(1.0), vec3(1.0, 0.95, 0.86), maria) * moon_energy * alb * limb
				* (earthshine + (1.0 - earthshine) * lit);
		occl = disc;
	}
	float halo = exp(-pow(ang / (moon_radius * 1.8), 2.0)) * 0.3 + exp(-ang / (moon_radius * 5.0)) * 0.14
			+ exp(-ang / (moon_radius * 16.0)) * 0.05;
	halo += exp(-pow((ang - moon_radius * 3.2) / (moon_radius * 0.35), 2.0)) * 0.012;   // a faint corona ring
	// the planet: banded, half lit, with a tilted ring
	vec3 pl_c = vec3(0.0);
	float pl_occl = 0.0;
	vec2 plv = sky_frame(d, normalize(planet_dir)) / planet_radius;
	float pr = length(plv);
	if (pr < 4.0 && dot(d, normalize(planet_dir)) > 0.0) {
		mat2 tilt = mat2(vec2(0.94, 0.34), vec2(-0.34, 0.94));
		vec2 ruv = tilt * plv;
		float rr = length(vec2(ruv.x, ruv.y / 0.28));
		float ring = smoothstep(1.35, 1.42, rr) * smoothstep(2.25, 2.15, rr) * (0.55 + 0.45 * sin(rr * 40.0));
		ring *= 1.0 - 0.6 * smoothstep(1.75, 1.8, rr) * smoothstep(1.86, 1.81, rr);
		bool front = ruv.y < 0.0;
		float body = smoothstep(1.0, 0.95, pr);
		if (body > 0.0) {
			vec3 n = vec3(plv, sqrt(max(1.0 - pr * pr, 0.0)));
			vec2 bu = tilt * plv;
			float bands = nw_noise(vec2(bu.y * 7.0, bu.x * 0.8 + 2.0)) * 0.6 + 0.4 * sin(bu.y * 11.0);
			bands += 0.25 * nw_noise(vec2(bu.y * 22.0, bu.x * 3.0 + clock * 0.01));
			vec3 pc = mix(planet_a, planet_b, smoothstep(-0.3, 0.8, bands));
			float lit = clamp(dot(n, normalize(vec3(0.7, 0.3, 0.5))), 0.0, 1.0);
			pl_c = pc * (0.02 + 1.1 * lit) * 0.9;
			pl_occl = body;
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
		pl_c += planet_b * exp(-pr * 1.6) * 0.05;
	}
	// clouds: a high veil stretched by the wind and a low broken bank nearer the horizon, both drifting; their edges
	// silvered on the moon's side, their bodies dark; lit from inside near the storm
	float cloud = 0.0;
	vec3 cloud_c = vec3(0.0);
	float moonward = exp(-ang * 2.4);
	if (cloud_amount > 0.0 && e2 > -0.01) {
		vec2 wind = vec2(1.0, 0.3) * clock * cloud_speed;
		// the layers are planes over the sea: seen through the elevation above the horizon (e2), not above eye level
		float eh = max(e2, 0.0);
		vec2 tm = normalize(md.xz / (md.y + 0.1) - d.xz / (eh + 0.1) + vec2(1e-4)) * 0.012;
		vec2 uh = d.xz / (eh + 0.1) * 0.2 + wind;
		float nh = texture(cloud_a, uh * vec2(0.45, 1.6)).r;
		float nh2 = texture(cloud_a, (uh + tm) * vec2(0.45, 1.6)).r;
		float dh = smoothstep(0.56 - 0.2 * cloud_amount, 0.86, nh) * smoothstep(0.04, 0.14, e2)
				* (1.0 - 0.5 * smoothstep(0.3, 0.7, e2)) * 0.6;
		vec2 ul = d.xz / (eh + 0.04) * 0.3 + wind * 2.6 + vec2(3.7, 1.1);
		float nl = texture(cloud_b, ul * vec2(0.4, 1.1)).r;
		float nl2 = texture(cloud_b, (ul + tm * 2.0) * vec2(0.4, 1.1)).r;
		float dl = smoothstep(0.56 - 0.25 * cloud_amount, 0.8, nl) * smoothstep(-0.01, 0.025, e2)
				* (1.0 - smoothstep(0.1, 0.3, e2)) * 0.9;
		float rim = clamp((nh - nh2) * 14.0 + 0.15, 0.0, 1.0) * dh + clamp((nl - nl2) * 14.0 + 0.1, 0.0, 1.0) * dl;
		cloud = clamp(dh + dl - dh * dl, 0.0, 1.0);
		float thin = 1.0 - smoothstep(0.3, 0.9, cloud);
		cloud_c = mix(cloud_col, cloud_lit, clamp(rim / max(cloud, 1e-3) * 0.6 * thin + moonward * 0.8, 0.0, 1.0));
		cloud_c += moon_col * moonward * moonward * 0.3 * thin;
		cloud_c += city_glow_col * city_glow * 0.6 * low * pow(azk, 4.0);
		cloud_c += flash_col * flash * 0.9 * pow(max(dot(d, normalize(flash_dir)), 0.0), 12.0);
		cloud_c += storm_col * storm * exp(-abs(az - storm_at) * 5.0) * exp(-max(e2, 0.0) * 6.0) * 0.5;
		cloud *= 1.0 - 0.35 * calm_k;
	}
	// the aurora: faint folded curtains over the left-hand hills, bright at their foot, rayed, slowly swaying
	vec3 aur = vec3(0.0);
	if (aurora > 0.0 && az > aurora_az.x - 0.05 && az < aurora_az.y + 0.05 && e2 > 0.0 && e2 < 0.5) {
		float span = smoothstep(aurora_az.x, aurora_az.x + 0.12, az) * (1.0 - smoothstep(aurora_az.y - 0.15, aurora_az.y, az));
		float sway = texture(cloud_a, vec2(az * 0.3 + clock * 0.0015, 0.37)).r - 0.5;
		float fold = sin(az * 11.0 + clock * 0.05) * 0.022 + sin(az * 23.0 - clock * 0.08) * 0.01 + sway * 0.06;
		float h = e2 - (0.1 + fold);
		float body = smoothstep(-0.008, 0.004, h) * exp(-max(h, 0.0) * 13.0);
		float h2 = e2 - (0.17 + fold * 1.4 + 0.02 * sin(az * 7.0 - clock * 0.04));
		body += 0.5 * smoothstep(-0.006, 0.004, h2) * exp(-max(h2, 0.0) * 10.0);
		float rays = texture(cloud_b, vec2(az * 3.2 + clock * 0.004 + sway * 0.4, 0.61 + h * 0.4)).r;
		rays = 0.35 + 0.9 * smoothstep(0.35, 0.9, rays);
		vec3 ac = mix(aurora_a, aurora_b, smoothstep(0.02, 0.2, h));
		aur = ac * body * rays * span * aurora * 0.085 * (0.75 + 0.25 * sin(clock * 0.21 + az * 7.0)) * (1.0 - 0.6 * calm_k);
	}
	// the storm: a far thunderhead on the horizon right of the bay, only seen when lightning lights it from inside
	// (billowing towers under an anvil), with a bolt now and then
	vec3 stc = vec3(0.0);
	if (storm > 0.001 && az > storm_az.x - 0.02 && az < storm_az.y + 0.02 && e2 > -0.02 && e2 < 0.2) {
		float span = smoothstep(storm_az.x, storm_az.x + 0.1, az) * (1.0 - smoothstep(storm_az.y - 0.1, storm_az.y, az));
		// a few rounded towers on a low base, their edges lumpy
		float top = 0.012 * span;
		for (int k = 0; k < 5; k++) {
			float fk = float(k);
			float cx = storm_az.x + (fk + 0.5) / 5.0 * (storm_az.y - storm_az.x);
			float w = 0.028 + 0.022 * fract(fk * 0.618 + 0.3);
			float hk = 0.03 + 0.045 * fract(fk * 0.381 + 0.7);
			float q = (az - cx) / w;
			top = max(top, hk * sqrt(max(1.0 - q * q, 0.0)));
		}
		top += (texture(cloud_a, vec2(az * 9.0, 0.21)).r - 0.5) * 0.01 * span;
		float inside = smoothstep(top + 0.006, top - 0.012, e2) * span;
		float tex = texture(cloud_a, vec2(az * 5.0, e2 * 11.0)).r;
		float inner = storm * exp(-abs(az - storm_at) * 12.0) * (0.3 + tex) * inside
				* (0.6 + 0.4 * smoothstep(0.0, top + 1e-3, e2));
		stc = storm_col * inner * 0.6 * (1.0 - 0.4 * calm_k);
		if (storm_bolt > 0.0) {
			float x = storm_at + (nw_noise(vec2(e2 * 90.0, storm_seed)) - 0.5) * 0.012 + (e2 - top) * 0.05;
			float bolt = exp(-abs(az - x) / 0.0006) * step(0.0, e2) * step(e2, top * 0.7);
			stc += storm_col * bolt * storm_bolt * 3.0;
		}
	}
	c += deep * above;
	c += aur;
	c += st * (1.0 - occl) * (1.0 - pl_occl);
	c = mix(c, pl_c, pl_occl * above);
	c += pl_c * (1.0 - pl_occl) * above;
	c = mix(c, moon_c, occl);
	c += moon_col * halo * 0.3;
	c += stc;
	c = mix(c, cloud_c + moon_c * 0.2, cloud * (1.0 - occl * 0.5));
	// satellites: faint steady points crossing, one that glints
	if (e2 > 0.05) {
		float s1 = satellite(d, vec3(-0.75, 0.12, -0.65), vec3(0.2, 0.62, -0.75), 0.011, 1.25);
		float s2 = satellite(d, vec3(0.8, 0.4, -0.45), vec3(-0.3, 0.2, -0.93), 0.008, 0.85);
		float s3 = satellite(d, vec3(-0.2, 0.55, -0.8), vec3(0.65, 0.1, -0.75), 0.014, 5.9);
		float glint = 0.35 + 3.0 * pow(max(sin(clock * 0.07 + 1.3), 0.0), 40.0);
		c += vec3(0.85, 0.9, 1.0) * (s1 * 0.4 + s2 * 0.3 + s3 * glint) * (1.0 - cloud * 0.9) * (1.0 - occl);
	}
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
		vec3 mc = mix(vec3(0.6, 1.0, 0.8), vec3(0.85, 0.9, 1.0), k);
		c += mc * (line * 3.0 + hd * 4.0) * (1.0 - cloud * 0.8) * (1.0 - occl) * (1.0 - pl_occl);
	}
	// a flash in the sky (a big explosion or the mothership going down)
	float fd = max(dot(d, normalize(flash_dir)), 0.0);
	c += flash_col * flash * (pow(fd, 40.0) * 0.35 + pow(fd, 8.0) * 0.08 + 0.008);
	// the storm's glow on the horizon haze
	c += storm_col * storm * exp(-abs(az - storm_at) * 6.0) * exp(-abs(e2) * 20.0) * 0.06;
	ALBEDO = c;
}
