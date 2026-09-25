shader_type spatial;
render_mode cull_disabled;
// Sea: layered moving waves (normals), depth tint, fresnel sky reflection and sparkles.
uniform vec3 deep : source_color = vec3(0.01, 0.1, 0.22);
uniform vec3 shallow : source_color = vec3(0.05, 0.32, 0.42);
varying vec3 world_pos;

float wave(vec2 p, vec2 dir, float freq, float speed, float t) { return sin(dot(p, dir) * freq + t * speed); }

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float t = TIME;
	VERTEX.y += 0.04 * wave(world_pos.xz, vec2(0.8, 0.6), 0.9, 1.3, t) + 0.025 * wave(world_pos.xz, vec2(-0.3, 1.0), 1.7, 1.9, t);
}

void fragment() {
	float t = TIME;
	vec2 p = world_pos.xz;
	float dx = 0.9 * cos(dot(p, vec2(0.8, 0.6)) * 0.9 + t * 1.3) * 0.8 + 1.7 * cos(dot(p, vec2(-0.3, 1.0)) * 1.7 + t * 1.9) * -0.3 * 0.6;
	float dz = 0.9 * cos(dot(p, vec2(0.8, 0.6)) * 0.9 + t * 1.3) * 0.6 + 1.7 * cos(dot(p, vec2(-0.3, 1.0)) * 1.7 + t * 1.9) * 1.0 * 0.6;
	vec3 n = normalize(vec3(-dx * 0.08, 1.0, -dz * 0.08));
	NORMAL = (VIEW_MATRIX * vec4(n, 0.0)).xyz;
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	float sparkle = pow(max(0.0, sin(p.x * 7.0 + t * 2.0) * sin(p.y * 6.0 - t * 1.7)), 30.0);
	ALBEDO = mix(deep, shallow, 0.35 + 0.25 * sin(p.x * 0.3 + p.y * 0.2 + t * 0.2));
	ROUGHNESS = 0.08;
	METALLIC = 0.0;
	SPECULAR = 0.7;
	EMISSION = vec3(0.7, 0.85, 1.0) * (fres * 0.12 + sparkle * 1.2);
}
