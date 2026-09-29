// Jelly Spike beach sky: a dome round the camera. A three-stop gradient, the sun (or the moon) with its halo,
// drifting cloud wisps, twinkling stars. Unshaded and unfogged: it is the horizon the fog fades into.
// At golden hour: a warm lobe along the horizon towards the sun (horizon_glow), a big HDR disc that feeds the bloom
// (sun_hot), thin stratus streaks low over the sea (streaks) and wisps lit from below by the low sun (cloud_glow).
shader_type spatial;
render_mode unshaded, cull_front, fog_disabled, shadows_disabled;

uniform vec3 top_col : source_color = vec3(0.3, 0.6, 0.9);
uniform vec3 mid_col : source_color = vec3(0.6, 0.8, 0.95);
uniform vec3 horizon_col : source_color = vec3(0.85, 0.92, 0.97);
uniform vec3 ground_col : source_color = vec3(0.6, 0.7, 0.8);
uniform float mid_height = 0.18;
uniform float top_height = 0.85;
uniform vec3 sun_dir = vec3(-0.6, 0.25, -0.75);
uniform vec3 sun_col : source_color = vec3(1.0, 0.95, 0.85);
uniform float sun_disc = 1.0;     // 0 hides the disc (the glow stays)
uniform float sun_size = 0.03;
uniform float sun_glow = 0.35;
uniform vec3 cloud_col : source_color = vec3(1.0);
uniform vec3 cloud_shade : source_color = vec3(0.75, 0.8, 0.9);
uniform float cloud_amount = 0.3;
uniform float cloud_speed = 0.004;
uniform float stars = 0.0;
uniform float moon = 0.0;
uniform vec3 moon_dir = vec3(0.5, 0.45, -0.75);
uniform vec3 moon_col : source_color = vec3(0.95, 0.95, 1.0);
uniform vec3 glow_col : source_color = vec3(1.0, 0.55, 0.25);
uniform float horizon_glow = 0.0;  // the warm band along the horizon, strongest under the sun
uniform float anti_glow = 0.0;     // the rosy belt on the side away from the sun
uniform vec3 anti_col : source_color = vec3(0.9, 0.55, 0.65);
uniform float sun_hot = 1.6;
uniform vec3 disc_col : source_color = vec3(1.0);
uniform float disc_mix = 0.0;   // the disc's own colour (paler than the halo at sunset)       // the disc's brightness (above 1 it blooms)
uniform float streaks = 0.0;       // stratus bands just over the horizon
uniform vec3 streak_col : source_color = vec3(1.0, 0.7, 0.45);
uniform vec3 streak_shade : source_color = vec3(0.55, 0.4, 0.55);
uniform float cloud_glow = 0.0;    // wisps lit from below by a low sun

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

void fragment() {
	vec3 d = normalize(dir);
	float e = d.y;
	vec3 c;
	if (e >= 0.0) {
		float k = clamp(e / mid_height, 0.0, 1.0);
		c = mix(horizon_col, mid_col, smoothstep(0.0, 1.0, k));
		c = mix(c, top_col, smoothstep(mid_height, top_height, e));
	} else {
		c = mix(horizon_col, ground_col, smoothstep(0.0, 0.08, -e));
	}
	vec3 sd = normalize(sun_dir);
	float s = max(dot(d, sd), 0.0);
	// azimuth towards the sun, on the horizontal plane
	float az = dot(normalize(d.xz + vec2(1e-5)), normalize(sd.xz + vec2(1e-5))) * 0.5 + 0.5;
	if (horizon_glow > 0.0) {
		float band = exp(-max(e, 0.0) * 9.0) * (e > -0.02 ? 1.0 : 0.0);
		c = mix(c, glow_col, clamp(horizon_glow * band * pow(az, 2.5), 0.0, 1.0));
		c = mix(c, anti_col, clamp(anti_glow * exp(-abs(e - 0.06) * 14.0) * pow(1.0 - az, 2.0), 0.0, 1.0));
	}
	// the halo blends towards the sun's colour (never adds past it, so no ring where a channel tops out)
	c = mix(c, sun_col, clamp(sun_glow * (pow(s, 6.0) * 0.45 + pow(s, 48.0) * 0.5), 0.0, 1.0));
	float disc = sun_disc * smoothstep(1.0 - sun_size * 0.012, 1.0 - sun_size * 0.008, s);
	// a hot core, a little limb darkening towards the rim
	float core = smoothstep(1.0 - sun_size * 0.012, 1.0, s);
	vec3 dcol = mix(sun_col, disc_col, disc_mix);
	c = mix(c, dcol * sun_hot * (0.8 + 0.35 * core), disc);
	c += dcol * pow(s, 900.0 / max(sun_size, 0.01)) * sun_disc * sun_hot * 0.25;
	// stars, above the horizon haze
	if (stars > 0.0) {
		vec3 p = d * 260.0;
		vec3 cell = floor(p);
		float h = hash3(cell);
		vec3 f = fract(p) - 0.5;
		float star = step(1.0 - 0.06 * stars, h) * smoothstep(0.3, 0.0, length(f));
		float tw = 0.6 + 0.4 * sin(TIME * (1.5 + h * 4.0) + h * 60.0);
		vec3 sc = mix(vec3(0.75, 0.85, 1.0), vec3(1.0, 0.9, 0.75), fract(h * 13.0));
		c += sc * star * tw * 1.4 * smoothstep(0.03, 0.25, e) * stars;
		// a faint band of dust
		float band = exp(-pow(dot(d, normalize(vec3(0.3, 0.2, 1.0))) * 3.5, 2.0));
		c += vec3(0.25, 0.3, 0.45) * band * fbm(d.xy * 9.0 + d.z * 3.0) * 0.18 * stars * smoothstep(0.05, 0.3, e);
	}
	if (moon > 0.0) {
		vec3 md = normalize(moon_dir);
		float m = max(dot(d, md), 0.0);
		float disc = smoothstep(0.99955, 0.99965, m);
		float craters = 0.85 + 0.15 * fbm(d.xy * 400.0);
		c = mix(c, moon_col * craters * 1.8, disc * moon);
		c += moon_col * moon * (pow(m, 600.0) * 0.5 + pow(m, 40.0) * 0.12);
	}
	// cloud wisps on a plane high over the scene
	if (cloud_amount > 0.0 && e > 0.0) {
		vec2 uv = d.xz / (e + 0.08) * 0.9 + vec2(TIME * cloud_speed, TIME * cloud_speed * 0.3);
		float n = fbm(uv * vec2(1.0, 2.2));
		float dens = smoothstep(1.0 - cloud_amount * 0.9, 1.25 - cloud_amount * 0.7, n);
		dens *= smoothstep(0.0, 0.12, e) * 0.85;
		float lit = clamp(0.5 + 0.8 * (fbm(uv * vec2(1.0, 2.2) + sd.xz * 0.08) - n) * -4.0, 0.0, 1.0);
		vec3 cc = mix(cloud_shade, cloud_col, lit);
		cc += sun_col * pow(s, 6.0) * 0.5;
		// lit from below: the thin edges and the side facing the sun catch a hot rim
		cc += glow_col * cloud_glow * (0.35 + 0.65 * pow(az, 3.0)) * (1.0 - smoothstep(0.3, 1.0, dens)) * 1.4;
		c = mix(c, cc, dens);
	}
	if (streaks > 0.0 && e > -0.005 && e < 0.2) {
		// long thin bands: stretched noise in azimuth and elevation, thickest a few degrees up
		float ang = atan(d.x, -d.z);
		// long thin bands, gently warped so no noise cell shows
		float y = e * 120.0 + 0.9 * sin(ang * 5.0 + 1.3) + 0.5 * sin(ang * 11.0);
		vec2 q = vec2(ang * 7.0 + TIME * 0.002, y);
		q = mat2(vec2(0.995, 0.1), vec2(-0.1, 0.995)) * q;
		float n = fbm(q * vec2(0.35, 1.0)) + (vnoise(q * vec2(1.6, 0.8) + 3.1) - 0.5) * 0.25;
		float h = exp(-pow((e - 0.045) / 0.035, 2.0));
		float sd2 = smoothstep(0.5, 0.78, n) * h * streaks;
		// towards the sun they glow gold-white; away, dusky rose
		float hot = pow(az, 4.0);
		vec3 sc = mix(streak_shade, streak_col, 0.25 + 0.75 * hot);
		sc += sun_col * pow(s, 12.0) * 1.6;
		// the edges are lit brighter than the cores (thin cloud against the light)
		sc *= 1.0 + 0.6 * (1.0 - smoothstep(0.62, 0.9, n)) * hot;
		c = mix(c, sc, clamp(sd2, 0.0, 0.9));
	}
	ALBEDO = c;
}
