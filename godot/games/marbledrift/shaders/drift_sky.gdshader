shader_type sky;
// Marble Drift: the sky all round the floating courses (our own design, CC BY-SA 4.0). Used as the environment's sky,
// so the glossy tiles reflect it. A gradient that runs on below the horizon into the abyss, the sun with its glow (or
// a striped synthwave sun), high cloud streaks, stars, a nebula band and an aurora glow. Static (no TIME), so the
// radiance is baked once; DriftSky animates the living parts with meshes.

#include "res://games/marbledrift/shaders/drift_noise.gdshaderinc"

uniform vec3 top : source_color = vec3(0.2, 0.4, 0.8);
uniform vec3 mid : source_color = vec3(0.5, 0.7, 0.95);
uniform vec3 horizon : source_color = vec3(0.95, 0.85, 0.7);
uniform vec3 below : source_color = vec3(0.6, 0.55, 0.6);      // just under the horizon
uniform vec3 deep : source_color = vec3(0.1, 0.1, 0.2);        // straight down
uniform vec3 sun_dir = vec3(0.0, 0.2, 1.0);                     // towards the sun
uniform vec3 sun_col : source_color = vec3(1.0, 0.9, 0.7);
uniform float sun_disc = 1.0;        // 0 = no disc
uniform float sun_size = 0.03;       // disc radius, radians
uniform float sun_glow = 0.6;
uniform float synth_sun = 0.0;       // 1 = a big striped synthwave sun
uniform vec3 synth_top : source_color = vec3(1.0, 0.85, 0.3);
uniform vec3 synth_bottom : source_color = vec3(1.0, 0.2, 0.6);
uniform float streaks = 0.0;         // high cloud streaks
uniform vec3 streak_col : source_color = vec3(1.0, 0.9, 0.8);
uniform float stars = 0.0;
uniform float nebula = 0.0;
uniform vec3 neb_a : source_color = vec3(0.5, 0.2, 0.7);
uniform vec3 neb_b : source_color = vec3(0.1, 0.6, 0.7);
uniform vec3 neb_axis = vec3(0.3, 0.9, 0.3);                    // normal of the nebula's band
uniform float aurora = 0.0;
uniform vec3 aurora_col : source_color = vec3(0.2, 1.0, 0.6);
uniform vec3 aurora_dir = vec3(0.0, 0.0, 1.0);

float star_layer(vec3 d, float scale, float density) {
	vec3 p = d * scale;
	vec3 c = floor(p);
	float h = md_hash3(c);
	if (h < 1.0 - density) {
		return 0.0;
	}
	vec3 o = vec3(md_hash3(c + 1.3), md_hash3(c + 2.7), md_hash3(c + 4.1)) * 0.6 + 0.2;
	float r = length(p - c - o);
	return (1.0 - smoothstep(0.0, 0.14, r)) * (0.4 + 0.6 * fract(h * 97.0));
}

void sky() {
	vec3 d = EYEDIR;
	float el = d.y;
	vec3 col;
	if (el >= 0.0) {
		col = mix(horizon, mid, smoothstep(0.0, 0.22, el));
		col = mix(col, top, smoothstep(0.18, 0.85, el));
	} else {
		col = mix(horizon, below, smoothstep(0.0, 0.08, -el));
		col = mix(col, deep, smoothstep(0.05, 0.75, -el));
	}
	vec3 sd = normalize(sun_dir);
	float cs = dot(d, sd);
	float az = atan(d.x, d.z);

	// high streaks of cloud, lit from the sun's side
	if (streaks > 0.0 && el > -0.05) {
		vec2 q = vec2(az * 3.0, el * 18.0 / (0.25 + el));
		float s = md_fbm(q * vec2(1.0, 0.35) + vec2(0.0, 3.0), 4);
		s = smoothstep(0.5, 0.8, s) * smoothstep(-0.05, 0.08, el) * (1.0 - smoothstep(0.35, 0.8, el));
		col = mix(col, streak_col * (0.8 + 0.6 * pow(max(cs, 0.0), 3.0)), s * streaks);
	}

	// nebula band and stars
	if (nebula > 0.0) {
		float band = exp(-pow(dot(d, normalize(neb_axis)) * 2.6, 2.0));
		float n1 = md_fbm3(d * 2.4, 5);
		float n2 = md_fbm3(d * 5.0 + 3.0, 4);
		float dust = smoothstep(0.45, 0.75, md_fbm3(d * 7.0 + 9.0, 3));
		vec3 neb = mix(neb_a, neb_b, smoothstep(0.35, 0.65, n2)) * pow(n1, 2.2) * 2.6;
		neb += neb_b * pow(max(n2 - 0.4, 0.0), 2.0) * 3.0;
		col += neb * band * nebula * (1.0 - 0.7 * dust);
		col += neb_a * 0.05 * nebula;
	}
	if (stars > 0.0 && !AT_CUBEMAP_PASS) {
		float s = star_layer(d, 140.0, 0.035) + star_layer(d, 300.0, 0.05) * 0.6 + star_layer(d, 60.0, 0.012) * 1.8;
		float hz = el > 0.0 ? smoothstep(0.0, 0.15, el) : smoothstep(0.0, 0.3, -el) * 0.85;
		vec3 tint = mix(vec3(0.75, 0.85, 1.0), vec3(1.0, 0.85, 0.7), md_hash3(floor(d * 140.0)));
		col += tint * s * stars * 2.2 * hz;
	}
	if (aurora > 0.0) {
		vec3 ad = normalize(aurora_dir);
		float a = max(dot(normalize(vec3(d.x, 0.0, d.z)), normalize(vec3(ad.x, 0.0, ad.z))), 0.0);
		float h = exp(-pow((el - 0.12) * 5.0, 2.0));
		float rays = 0.6 + 0.4 * md_noise(vec2(az * 30.0, 0.0));
		col += aurora_col * pow(a, 3.0) * h * rays * aurora;
	}

	// the sun
	if (synth_sun > 0.0) {
		float ang = acos(clamp(cs, -1.0, 1.0));
		float r = 0.16;
		float inside = 1.0 - smoothstep(r - 0.004, r, ang);
		vec3 sl = sd;
		float v = (d.y - sd.y) / r;          // -1 bottom .. 1 top of the disc
		vec3 sc = mix(synth_bottom, synth_top, smoothstep(-0.9, 0.8, v));
		float gap = v < 0.15 ? step(0.5, fract((v + 1.0) * 5.0 + (v * v) * 2.0)) * smoothstep(0.15, -0.1, v) : 0.0;
		inside *= 1.0 - gap * smoothstep(0.0, -0.4, v + 0.2) * 1.0;
		col = mix(col, sc * 2.4, inside * synth_sun);
		col += synth_bottom * exp(-ang * 5.0) * 0.6 * synth_sun;
	} else {
		col += sun_col * (pow(max(cs, 0.0), 6.0) * 0.35 + pow(max(cs, 0.0), 60.0) * 0.8) * sun_glow;
		float disc = smoothstep(cos(sun_size), cos(sun_size * 0.85), cs);
		col = mix(col, sun_col * 5.0, disc * sun_disc);
	}
	COLOR = col;
}
