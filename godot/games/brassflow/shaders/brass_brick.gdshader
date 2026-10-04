// Brassflow workshop walls: running-bond brick in world space (the wall picks its plane from its normal), each brick
// its own shade of red-brown with soot towards the top, recessed mortar joints (a bump from the joint distance).
shader_type spatial;

uniform vec3 brick_a : source_color = vec3(0.34, 0.15, 0.10);
uniform vec3 brick_b : source_color = vec3(0.42, 0.22, 0.14);
uniform vec3 brick_c : source_color = vec3(0.26, 0.13, 0.10);
uniform vec3 mortar : source_color = vec3(0.3, 0.26, 0.22);
uniform vec2 size = vec2(1.0, 0.36);  // brick + joint, world units
uniform float joint = 0.05;
uniform float soot_from = 6.0;        // world y where the soot starts darkening the bricks
uniform float soot_to = 14.0;

varying vec3 wpos;
varying vec3 wnrm;

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
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = abs(wnrm);
	vec2 p = n.x > n.z ? vec2(wpos.z, wpos.y) : vec2(wpos.x, wpos.y);
	if (n.y > 0.7) {
		p = wpos.xz;
	}
	vec2 q = p / size;
	float row = floor(q.y);
	q.x += mod(row, 2.0) * 0.5;
	vec2 cell = floor(q);
	vec2 f = fract(q) * size;
	float dx = min(f.x, size.x - f.x);
	float dy = min(f.y, size.y - f.y);
	float d = min(dx, dy);
	float j = smoothstep(joint * 0.5, joint * 0.5 + 0.025, d);  // 0 in the joint, 1 on the brick
	float h = hash(cell);
	vec3 col = h < 0.33 ? brick_a : (h < 0.66 ? brick_b : brick_c);
	col *= 0.85 + 0.3 * hash(cell + 7.1);
	float grain = vnoise(p * 9.0) * 0.5 + vnoise(p * 23.0) * 0.5;
	col *= 0.85 + 0.3 * grain;
	float soot = smoothstep(soot_from, soot_to, wpos.y);
	col *= 1.0 - 0.55 * soot;
	vec3 m = mortar * (0.8 + 0.4 * vnoise(p * 15.0)) * (1.0 - 0.5 * soot);
	ALBEDO = mix(m, col, j);
	ROUGHNESS = mix(0.95, 0.82 - 0.1 * hash(cell + 3.3), j);
	// joint bump: tilt the normal towards the joint near a brick's edges (world axes of the wall's plane)
	vec3 ua = n.x > n.z ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
	vec3 va = vec3(0.0, 1.0, 0.0);
	if (n.y > 0.7) {
		ua = vec3(1.0, 0.0, 0.0);
		va = vec3(0.0, 0.0, 1.0);
	}
	vec2 g = vec2(dx < dy ? sign(f.x - size.x * 0.5) : 0.0, dx < dy ? 0.0 : sign(f.y - size.y * 0.5));
	float e = (1.0 - smoothstep(joint * 0.5, joint * 0.5 + 0.05, d)) * j * 0.8;
	vec3 tilt = (ua * g.x + va * g.y) * e;
	NORMAL = normalize(NORMAL + (VIEW_MATRIX * vec4(tilt, 0.0)).xyz);
}
