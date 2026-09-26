shader_type spatial;
// Mossfolk: the far cave wall, rough rock in the theme's tint with faint glowing veins.

render_mode unshaded;

uniform vec3 tint : source_color = vec3(0.15, 0.18, 0.22);
uniform vec3 glow : source_color = vec3(0.5, 0.8, 1.0);

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
	vec2 p = UV * vec2(40.0, 12.0);
	float rock = fbm(p);
	float cracks = smoothstep(0.012, 0.0, abs(fbm(p * 0.6 + 3.0) - 0.5)) * 0.6;
	float vein = smoothstep(0.015, 0.0, abs(fbm(p * 0.35 + 11.0) - 0.52)) * (0.6 + 0.4 * sin(TIME * 0.8 + p.x));
	vec3 col = tint * (0.55 + rock * 0.8) * (1.0 - cracks * 0.5);
	// darker towards the top and bottom
	col *= 0.6 + 0.4 * sin(UV.y * 3.14159);
	col += glow * vein * 0.12;
	ALBEDO = col;
}
