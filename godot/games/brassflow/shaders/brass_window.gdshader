// Brassflow workshop windows: the night outside, in world space so the three panes share one sky: a deep blue
// gradient, stars that twinkle, the moon with its halo (only where moon > 0), thin clouds drifting past it and the
// rooftops and chimneys of the town below. Driven by the workshop's own clock (t), not TIME.
shader_type spatial;
render_mode unshaded, shadows_disabled;

uniform float t = 0.0;
uniform float moon = 0.0;
uniform vec2 moon_pos = vec2(6.2, 6.6);   // world x, y on the window plane
uniform float moon_r = 0.55;
uniform vec3 sky_top : source_color = vec3(0.02, 0.04, 0.12);
uniform vec3 sky_low : source_color = vec3(0.10, 0.16, 0.32);
uniform vec3 moon_col : source_color = vec3(0.95, 0.95, 0.85);
uniform vec3 roof_col : source_color = vec3(0.015, 0.02, 0.04);
uniform vec3 lit_col : source_color = vec3(1.0, 0.7, 0.35);
uniform float energy = 1.0;

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
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wpos.xy;
	float k = clamp((p.y - 0.5) / 8.0, 0.0, 1.0);
	vec3 col = mix(sky_low, sky_top, k);
	// stars
	vec2 sc = floor(p * 6.0);
	float s = hash(sc);
	vec2 sf = fract(p * 6.0) - 0.5 - (vec2(hash(sc + 1.3), hash(sc + 2.9)) - 0.5) * 0.6;
	float star = s > 0.93 ? (1.0 - smoothstep(0.0, 0.06, length(sf))) : 0.0;
	star *= 0.6 + 0.4 * sin(t * (1.5 + 3.0 * hash(sc + 4.4)) + s * 30.0);
	col += vec3(0.8, 0.85, 1.0) * star * k;
	// the moon and its halo
	float d = length(p - moon_pos);
	float disc = 1.0 - smoothstep(moon_r - 0.03, moon_r, d);
	float spots = vnoise((p - moon_pos) * 4.0) * 0.25 + vnoise((p - moon_pos) * 9.0) * 0.12;
	col += moon * moon_col * 0.35 * exp(-max(d - moon_r, 0.0) * 1.3);
	col = mix(col, moon_col * (0.9 - spots), disc * moon);
	// thin clouds drifting across (a few octaves, stretched sideways)
	vec2 cp = mat2(vec2(0.96, 0.28), vec2(-0.28, 0.96)) * vec2(p.x * 0.35 + t * 0.03, p.y * 0.9);
	float c = 0.0;
	float amp = 0.55;
	for (int i = 0; i < 4; i++) {
		c += amp * vnoise(cp);
		cp = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * cp * 2.03 + vec2(1.7, 9.2);
		amp *= 0.5;
	}
	c = smoothstep(0.42, 0.8, c) * smoothstep(1.5, 4.0, p.y);
	vec3 cloud_col = mix(vec3(0.1, 0.13, 0.22), moon_col * 0.55, moon * exp(-d * 0.45));
	col = mix(col, cloud_col, c * 0.65);
	// rooftops: blocks of houses with chimneys, a few lit windows
	float bx = floor(p.x * 0.8);
	float roof = 1.3 + hash(vec2(bx, 0.3)) * 1.1;
	float fx = fract(p.x * 0.8);
	roof += (hash(vec2(bx, 9.1)) > 0.5 ? (0.5 - abs(fx - 0.5)) * 0.9 : 0.0);  // gables
	float chim = step(abs(fx - hash(vec2(bx, 4.2)) * 0.7 - 0.15), 0.05) * step(0.4, hash(vec2(bx, 7.7)));
	roof += chim * 0.45;
	if (p.y < roof) {
		col = roof_col;
		vec2 wc = floor(vec2(p.x * 4.0, p.y * 3.0));
		vec2 wf = fract(vec2(p.x * 4.0, p.y * 3.0));
		float lit = step(0.84, hash(wc + bx)) * step(0.25, wf.x) * step(wf.x, 0.75) * step(0.3, wf.y) * step(wf.y, 0.8);
		lit *= step(p.y, roof - 0.35);
		col += lit_col * lit * (0.75 + 0.25 * sin(t * 0.3 + hash(wc) * 6.0));
	}
	ALBEDO = col * energy;
}
