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
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1,0)), f.x), mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), f.x), f.y);
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
	vec3 n = normalize(vec3(-dx * 0.14, 1.0, -dz * 0.14));
	NORMAL = (VIEW_MATRIX * vec4(n, 0.0)).xyz;
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	float sparkle = pow(max(0.0, sin(p.x * 7.0 + t * 2.0) * sin(p.y * 6.0 - t * 1.7)), 30.0);
	float depth = smoothstep(0.05, 0.55, land);
	vec3 col = mix(deep, shallow, depth);
	col = mix(col, col * 1.25, vnoise(p * 0.6 + t * 0.05));
	// foam: bands that move towards the shore, broken up by noise
	float band = sin(land * 30.0 - t * 2.2) * 0.5 + 0.5;
	float foam = smoothstep(0.25, 0.5, land) * smoothstep(0.75, 0.35, land) * smoothstep(0.55, 0.95, band * vnoise(p * 3.0 + t * 0.3) * 1.6);
	foam += smoothstep(0.42, 0.5, land) * 0.8;
	ALBEDO = mix(col, vec3(0.92, 0.96, 1.0), clamp(foam, 0.0, 1.0));
	ROUGHNESS = mix(0.06, 0.6, clamp(foam, 0.0, 1.0));
	SPECULAR = 0.7;
	EMISSION = vec3(0.7, 0.85, 1.0) * (fres * 0.1 + sparkle * 1.2) + vec3(0.9) * foam * 0.15;
}
