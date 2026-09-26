shader_type spatial;
// Hopline canal: green-blue water with a slow swell, drifting ripples and sun glints.

render_mode cull_back;

uniform vec3 deep : source_color = vec3(0.05, 0.2, 0.24);
uniform vec3 shallow : source_color = vec3(0.14, 0.38, 0.38);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() {
	VERTEX.y += sin(VERTEX.x * 1.3 + TIME * 1.2) * 0.02 + sin(VERTEX.z * 2.1 + TIME * 0.9) * 0.015;
}

void fragment() {
	vec2 p = UV * vec2(26.0, 5.0);
	float r1 = noise(p * 3.0 + vec2(TIME * 0.3, 0.0));
	float r2 = noise(p * 5.0 - vec2(TIME * 0.2, TIME * 0.1));
	float ripple = r1 * 0.6 + r2 * 0.4;
	ALBEDO = mix(deep, shallow, ripple);
	float glint = smoothstep(0.82, 0.95, ripple);
	EMISSION = vec3(1.0, 0.95, 0.8) * glint * 0.25;
	ROUGHNESS = 0.08;
	METALLIC = 0.1;
	SPECULAR = 0.7;
	NORMAL_MAP = vec3(0.5 + (r1 - 0.5) * 0.3, 0.5 + (r2 - 0.5) * 0.3, 1.0);
}
