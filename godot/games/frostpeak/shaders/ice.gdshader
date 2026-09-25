shader_type spatial;
// Rink ice: a glossy, slightly blue sheet with fine skate scratches that break the reflections up.

uniform vec3 tint : source_color = vec3(0.86, 0.93, 1.0);
uniform float scratches = 1.0;

varying vec3 wpos;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float line_field(vec2 p, float angle) {
	vec2 d = vec2(cos(angle), sin(angle));
	float t = dot(p, vec2(-d.y, d.x));
	float id = floor(t * 6.0);
	float f = fract(t * 6.0);
	return smoothstep(0.03, 0.0, abs(f - 0.5)) * step(0.7, hash(vec2(id, floor(dot(p, d) * 0.2))));
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wpos.xz;
	float s = line_field(p, 0.2) + line_field(p * 1.3, -0.35) + line_field(p * 0.8, 1.2) * 0.5;
	s *= scratches;
	ALBEDO = tint * (0.92 + 0.08 * s);
	METALLIC = 0.0;
	SPECULAR = 0.9;
	ROUGHNESS = 0.06 + 0.25 * s;
}
