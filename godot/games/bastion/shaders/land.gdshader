shader_type spatial;
// Land tiles: grass inland, sand near the sea (per-instance COLOR.r = shore blend), soft noise variation.
uniform vec3 grass : source_color = vec3(0.2, 0.42, 0.14);
uniform vec3 grass2 : source_color = vec3(0.3, 0.5, 0.17);
uniform vec3 sand : source_color = vec3(0.78, 0.66, 0.42);
uniform vec3 rock : source_color = vec3(0.45, 0.43, 0.42);
varying vec3 world_pos;
varying vec4 inst;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1,0)), f.x), mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), f.x), f.y);
}
void vertex() { world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; inst = INSTANCE_CUSTOM; }
void fragment() {
	float n = vnoise(world_pos.xz * 1.7) * 0.6 + vnoise(world_pos.xz * 6.0) * 0.4;
	vec3 g = mix(grass, grass2, n);
	vec3 c = mix(g, sand, clamp(COLOR.r, 0.0, 1.0));
	c = mix(c, rock * (0.8 + 0.4 * n), COLOR.g);
	// territory tint (COLOR.b) and the sides of the tiles darker
	c = mix(c, c * vec3(0.75, 0.85, 1.25) + vec3(0.02, 0.04, 0.1), COLOR.b * 0.55);
	float side = 1.0 - abs(NORMAL.y);
	ALBEDO = c * (1.0 - 0.35 * step(0.5, abs((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).x) + abs((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).z)));
	ROUGHNESS = 0.9;
}
