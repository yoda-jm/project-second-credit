shader_type spatial;
// Fizzlings backdrop: deep water tinted by the level, lighter towards the surface, with light rays and caustics.

render_mode unshaded;

uniform vec3 tint : source_color = vec3(0.95, 0.55, 0.7);
uniform float time_s = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	vec2 uv = UV;
	vec3 deep = vec3(0.02, 0.07, 0.16);
	vec3 shallow = mix(vec3(0.1, 0.35, 0.55), tint * 0.5, 0.25);
	vec3 col = mix(shallow, deep, smoothstep(0.0, 1.0, uv.y));
	// god rays from the top, slowly swaying
	float ray = 0.0;
	for (int i = 0; i < 4; i++) {
		float fi = float(i);
		float x = 0.2 + fi * 0.2 + sin(time_s * 0.2 + fi * 1.7) * 0.05 + (uv.y) * (0.1 - fi * 0.05);
		ray += smoothstep(0.035, 0.0, abs(uv.x - x)) * (1.0 - uv.y);
	}
	col += vec3(0.5, 0.8, 1.0) * ray * 0.12;
	// caustics shimmer
	vec2 p = uv * vec2(30.0, 18.0);
	float c = noise(p + vec2(time_s * 0.4, time_s * 0.3)) * noise(p * 1.7 - vec2(time_s * 0.3, 0.0));
	col += vec3(0.4, 0.7, 0.9) * smoothstep(0.35, 0.6, c) * 0.08 * (1.0 - uv.y * 0.6);
	ALBEDO = col;
}
