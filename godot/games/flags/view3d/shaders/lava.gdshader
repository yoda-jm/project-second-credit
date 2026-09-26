shader_type spatial;
// Molten rock: dark crust drifting over a glowing flow, for the volcanic planet's lava channels.
render_mode cull_disabled;
uniform vec3 hot : source_color = vec3(1.0, 0.45, 0.08);
uniform vec3 crust : source_color = vec3(0.12, 0.05, 0.04);
varying vec3 wp;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	VERTEX.y += sin(wp.x * 1.3 + TIME * 0.8) * 0.02;
}

void fragment() {
	vec2 p = wp.xz * 0.9 + vec2(TIME * 0.12, TIME * 0.05);
	float n = noise(p) * 0.6 + noise(p * 2.3 - TIME * 0.2) * 0.3 + noise(p * 5.0) * 0.1;
	float cracks = smoothstep(0.42, 0.62, n);
	float pulse = 0.85 + 0.15 * sin(TIME * 2.0 + wp.x * 0.5);
	ALBEDO = mix(crust, hot * 0.4, 1.0 - cracks);
	EMISSION = hot * (1.0 - cracks) * 3.0 * pulse + hot * 0.15;
	ROUGHNESS = mix(0.4, 0.95, cracks);
}
