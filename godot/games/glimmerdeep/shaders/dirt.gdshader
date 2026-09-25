shader_type spatial;
// Dirt: layered world-space value noise, warm earthy tones with darker pebbles. No textures needed.
uniform vec3 base_color : source_color = vec3(0.23, 0.16, 0.10);
uniform vec3 light_color : source_color = vec3(0.36, 0.26, 0.16);
uniform vec3 pebble_color : source_color = vec3(0.16, 0.14, 0.12);
varying vec3 world_pos;

float hash(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
float vnoise(vec3 p) {
	vec3 i = floor(p); vec3 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i), hash(i + vec3(1,0,0)), f.x), mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
	           mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x), mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z);
}
void vertex() { world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	float n = vnoise(world_pos * 3.0) * 0.6 + vnoise(world_pos * 9.0) * 0.4;
	float pebbles = smoothstep(0.78, 0.84, vnoise(world_pos * 11.0 + 13.0)) * 0.7;
	vec3 c = mix(base_color, light_color, n);
	c = mix(c, pebble_color, pebbles);
	ALBEDO = c;
	ROUGHNESS = 0.95;
	SPECULAR = 0.2;
}
