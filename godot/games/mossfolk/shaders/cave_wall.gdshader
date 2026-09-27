shader_type spatial;
// Mossfolk: the far cave wall, rough rock in the theme's tint with faint glowing veins. Lit, so the crystals,
// lanterns and light shafts play across it.

uniform vec3 tint : source_color = vec3(0.15, 0.18, 0.22);
uniform vec3 glow : source_color = vec3(0.5, 0.8, 1.0);
uniform vec2 extent = vec2(90.0, 36.0);   // the wall's size in world units
uniform sampler2D rock_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rock_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) {
	float v = 0.0; float a = 0.5;
	for (int i = 0; i < 5; i++) { v += a * noise(p); p *= 2.1; a *= 0.5; }
	return v;
}

void fragment() {
	vec2 wp = UV * extent;
	vec2 p = wp * vec2(0.45, 0.33);
	float rock = fbm(p);
	float cracks = smoothstep(0.012, 0.0, abs(fbm(p * 0.6 + 3.0) - 0.5)) * 0.6;
	float vein = smoothstep(0.015, 0.0, abs(fbm(p * 0.35 + 11.0) - 0.52)) * (0.6 + 0.4 * sin(TIME * 0.8 + p.x));
	vec3 tex = texture(rock_albedo, wp * 0.16).rgb;
	vec3 col = tint * tex * 3.2 * (0.55 + rock * 0.8) * (1.0 - cracks * 0.5);
	col *= 0.6 + 0.4 * sin(UV.y * 3.14159);
	ALBEDO = col;
	NORMAL_MAP = texture(rock_normal, wp * 0.16).rgb;
	NORMAL_MAP_DEPTH = 1.6;
	ROUGHNESS = 0.85;
	EMISSION = glow * vein * 0.06 + tint * 0.1;
}
