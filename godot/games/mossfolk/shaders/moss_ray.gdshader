shader_type spatial;
// Mossfolk: a shaft of light falling from a crack high in the cave, soft at its sides, fading as it falls, with
// motes of dust shimmering through it. Additive, on a long quad behind the slab.

render_mode unshaded, blend_add, cull_disabled, shadows_disabled, depth_draw_never;

uniform vec3 col : source_color = vec3(0.6, 0.9, 1.0);
uniform float energy = 0.35;
uniform float seed = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7)) + seed) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	float x = UV.x * 2.0 - 1.0;
	float fall = UV.y;                      // 0 at the crack, 1 at the far end
	float side = exp(-x * x * 5.0);
	float streak = 0.6 + 0.4 * noise(vec2(UV.x * 9.0 + seed, fall * 1.5 - TIME * 0.06));
	float motes = smoothstep(0.82, 1.0, noise(vec2(UV.x * 40.0, fall * 60.0 - TIME * 0.8))) * 1.5;
	float a = side * streak * smoothstep(0.0, 0.08, fall) * pow(1.0 - fall, 1.6);
	a *= 0.8 + 0.2 * sin(TIME * 0.4 + seed * 3.0);
	ALBEDO = col * energy * (a + motes * side * (1.0 - fall) * 0.5);
}
