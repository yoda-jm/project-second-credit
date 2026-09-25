shader_type spatial;
render_mode cull_disabled;
// Sea: moving layered waves, deep-to-shallow colour from a blurred land mask of the map (shore_mask), animated
// foam lines along the coast, fresnel sky reflection and sun sparkles.
uniform vec3 deep : source_color = vec3(0.01, 0.09, 0.2);
uniform vec3 shallow : source_color = vec3(0.05, 0.45, 0.5);
uniform sampler2D shore_mask : filter_linear;  // 1 on land, blurred: shallow water near 0.3..0.6
uniform vec2 map_size = vec2(40.0, 28.0);
varying vec3 world_pos;

float wave(vec2 p, vec2 dir, float freq, float speed, float t) { return sin(dot(p, dir) * freq + t * speed); }
// smooth gradient (Perlin-style) noise in 0..1: no grid-aligned artefacts, unlike value noise
vec2 grad(vec2 p) {
	float a = fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453) * 6.2831853;
	return vec2(cos(a), sin(a));
}
float vnoise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
	float n00 = dot(grad(i), f);
	float n10 = dot(grad(i + vec2(1.0, 0.0)), f - vec2(1.0, 0.0));
	float n01 = dot(grad(i + vec2(0.0, 1.0)), f - vec2(0.0, 1.0));
	float n11 = dot(grad(i + vec2(1.0, 1.0)), f - vec2(1.0, 1.0));
	return 0.5 + 0.7 * mix(mix(n00, n10, u.x), mix(n01, n11, u.x), u.y);
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float t = TIME;
	VERTEX.y += 0.07 * wave(world_pos.xz, vec2(0.8, 0.6), 0.9, 1.4, t) + 0.04 * wave(world_pos.xz, vec2(-0.3, 1.0), 1.8, 2.1, t)
		+ 0.02 * wave(world_pos.xz, vec2(1.0, -0.2), 3.3, 3.0, t);
}

void fragment() {
	float t = TIME;
	vec2 p = world_pos.xz;
	vec2 muv = (p + 0.5) / map_size;
	float land = texture(shore_mask, clamp(muv, vec2(0.0), vec2(1.0))).r;
	if (muv.x < 0.0 || muv.y < 0.0 || muv.x > 1.0 || muv.y > 1.0) { land = 0.0; }
	float dx = cos(dot(p, vec2(0.8, 0.6)) * 0.9 + t * 1.4) * 0.8 + cos(dot(p, vec2(-0.3, 1.0)) * 1.8 + t * 2.1) * -0.4;
	float dz = cos(dot(p, vec2(0.8, 0.6)) * 0.9 + t * 1.4) * 0.6 + cos(dot(p, vec2(-0.3, 1.0)) * 1.8 + t * 2.1) * 1.1;
	// fine ripples: a sum of short sine waves in scattered directions (no grid, unlike noise)
	float rx = 0.0;
	float rz = 0.0;
	for (int k = 0; k < 8; k++) {
		float fk = float(k);
		float ang = fk * 2.39996 + 0.7;  // golden angle: directions never line up
		vec2 dir = vec2(cos(ang), sin(ang));
		float freq = 2.2 + fk * 0.9;
		float amp = 0.035 / (1.0 + fk * 0.35);
		float ph = dot(p, dir) * freq + t * (1.2 + fk * 0.23);
		float c = cos(ph) * freq * amp;
		rx += dir.x * c;
		rz += dir.y * c;
	}
	vec3 n = normalize(vec3(-dx * 0.14 - rx, 1.0, -dz * 0.14 - rz));
	NORMAL = (VIEW_MATRIX * vec4(n, 0.0)).xyz;
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	float sparkle = pow(vnoise(p * 9.0 + vec2(t * 0.9, -t * 0.6)) * vnoise(p * 12.7 - vec2(t * 0.5, t * 0.8)), 10.0) * 0.5;
	float depth = smoothstep(0.05, 0.55, land);
	vec3 col = mix(deep, shallow, depth);
	col = mix(col, col * 1.25, vnoise(p * 0.6 + t * 0.05));
	// foam: bands that move towards the shore, broken up by noise
	float band = sin(land * 30.0 - t * 2.2) * 0.5 + 0.5;
	float foam = smoothstep(0.25, 0.5, land) * smoothstep(0.75, 0.35, land) * smoothstep(0.55, 0.95, band * vnoise(p * 3.0 + t * 0.3) * 1.6);
	foam += smoothstep(0.42, 0.5, land) * 0.8;
	ALBEDO = mix(col, vec3(0.92, 0.96, 1.0), clamp(foam, 0.0, 1.0));
	ROUGHNESS = mix(0.16, 0.6, clamp(foam, 0.0, 1.0));
	SPECULAR = 0.5;
	EMISSION = vec3(0.7, 0.85, 1.0) * (fres * 0.12 + sparkle) + vec3(0.9) * foam * 0.12;
}
