shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;
// The moonlit night seen through a room's window: a deep sky with twinkling stars, the moon with its halo and a
// wisp of cloud, and the rooftops across the street with chimneys and a few lit windows. Drawn on a quad (UV 0-1,
// v down) behind the window opening.

uniform vec2 moon = vec2(0.66, 0.26);  // in UV
uniform float aspect = 1.2;  // quad width / height
uniform float moon_size = 0.06;
uniform float skyline = 0.72;  // UV v of the tallest roofs
uniform float seed = 0.0;
uniform float sky_energy = 1.0;

float hash(float n) { return fract(sin(n * 12.9898 + seed * 7.13) * 43758.5453); }
float hash2(vec2 p) { return fract(sin(dot(p + seed, vec2(127.1, 311.7))) * 43758.5453); }

void fragment() {
	vec2 uv = UV;
	vec2 p = vec2(uv.x * aspect, uv.y);
	float up = 1.0 - uv.y;
	vec3 col = mix(vec3(0.11, 0.14, 0.3), vec3(0.012, 0.018, 0.06), smoothstep(0.05, 1.0, up)) * sky_energy;
	vec2 mp = vec2(moon.x * aspect, moon.y);
	float d = length(p - mp);
	col += vec3(0.3, 0.36, 0.6) * 0.55 * exp(-d * 6.0) + vec3(0.5, 0.5, 0.6) * 0.25 * exp(-d * 18.0);
	// stars
	vec2 g = floor(p * 70.0);
	vec2 f = fract(p * 70.0) - 0.5;
	float s = hash2(g);
	float star = step(0.982, s) * smoothstep(0.14, 0.0, length(f)) * (0.55 + 0.45 * sin(TIME * (1.0 + s * 3.0) + s * 40.0));
	col += vec3(0.9, 0.92, 1.0) * star * smoothstep(0.3, 0.55, up) * smoothstep(moon_size * 1.6 + 0.02, moon_size * 3.0 + 0.05, d) * 1.6;
	// the moon, with soft maria
	if (moon_size > 0.001) {
		float disc = smoothstep(moon_size, moon_size - 0.004, d);
		vec2 q = (p - mp) / moon_size;
		float maria = smoothstep(0.35, 0.0, length(q - vec2(-0.25, -0.2))) * 0.18 + smoothstep(0.3, 0.0, length(q - vec2(0.3, 0.25))) * 0.12
			+ smoothstep(0.22, 0.0, length(q - vec2(0.1, -0.45))) * 0.1;
		col = mix(col, vec3(1.0, 0.97, 0.86) * (2.4 - maria * 3.0 - 0.25 * q.x), disc);
	}
	// a wisp of cloud crossing the moon
	float band = uv.y - moon.y - 0.035 - 0.02 * sin(p.x * 9.0 + 1.3) - 0.01 * sin(p.x * 23.0);
	float cloud = smoothstep(0.035, 0.0, abs(band)) * smoothstep(0.5, 0.05, abs(p.x - mp.x));
	col = mix(col, vec3(0.2, 0.23, 0.38) + vec3(0.35, 0.36, 0.45) * exp(-d * 8.0), cloud * 0.75);
	// rooftops across the street
	float bx = floor(p.x * 4.0 + seed);
	float fx = fract(p.x * 4.0 + seed);
	float roof = skyline + hash(bx) * 0.16;
	if (hash(bx + 3.0) > 0.55) roof += abs(fx - 0.5) * 0.18 - 0.05;  // a gable
	if (hash(bx + 7.0) > 0.35 && fx > 0.18 && fx < 0.28) roof -= 0.07 + hash(bx + 9.0) * 0.04;  // a chimney
	float bld = smoothstep(roof - 0.002, roof + 0.002, uv.y);
	vec3 wall = vec3(0.018, 0.02, 0.04) + vec3(0.05, 0.06, 0.1) * exp(-(uv.y - roof) * 30.0);
	vec2 wg = vec2(p.x * 26.0, uv.y * 30.0);
	vec2 wc = floor(wg);
	vec2 wf = fract(wg);
	float lit = step(0.84, hash2(wc + bx * 3.1)) * step(roof + 0.05, uv.y);
	float pane = step(0.3, wf.x) * step(wf.x, 0.7) * step(0.2, wf.y) * step(wf.y, 0.8);
	wall = mix(wall, vec3(1.0, 0.68, 0.32) * (1.2 + hash2(wc) * 0.8), pane * lit);
	col = mix(col, wall, bld);
	col += vec3(0.25, 0.3, 0.55) * 0.5 * smoothstep(0.006, 0.0, abs(uv.y - roof)) * (1.0 - smoothstep(0.3, 0.9, abs(p.x - mp.x)));
	ALBEDO = col;
}
