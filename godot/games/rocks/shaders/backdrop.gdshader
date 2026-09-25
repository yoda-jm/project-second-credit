shader_type spatial;
// The cave's back wall: dark rock with faint veins; lit by the scene lights.
varying vec3 world_pos;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1,0)), f.x), mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), f.x), f.y);
}
void vertex() { world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	vec2 p = world_pos.xy;
	float n = vnoise(p * 1.3) * 0.5 + vnoise(p * 4.1) * 0.3 + vnoise(p * 11.0) * 0.2;
	float vein = smoothstep(0.02, 0.0, abs(vnoise(p * 0.7) - 0.5)) * 0.5;
	ALBEDO = mix(vec3(0.05, 0.045, 0.06), vec3(0.12, 0.1, 0.1), n) + vec3(0.1, 0.25, 0.3) * vein;
	ROUGHNESS = 1.0;
}
