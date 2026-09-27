shader_type spatial;
// Fizzlings: the shell of a bubble with a toy inside. Clear in the middle so the toy reads, a strong glowing rim
// (the colour tells it is full), thin-film swirls and two window glints. "warn" (0..1) turns it red and pulses.

render_mode unshaded, blend_mix, depth_draw_never, cull_back, shadows_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.78, 0.2);
uniform float glow = 2.2;
uniform float time_s = 0.0;
uniform float phase = 0.0;

void fragment() {
	float nv = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float fres = pow(1.0 - nv, 2.2);
	vec3 n = NORMAL;
	// thin-film swirl around the rim
	float a = atan(n.y, n.x);
	float swirl = 0.5 + 0.5 * sin(a * 3.0 + time_s * 2.0 + phase + n.z * 6.0);
	vec3 film = mix(color, vec3(1.0, 0.55, 0.95), swirl * 0.35);
	// glints: an upper-left window and a small dot
	float g1 = smoothstep(0.965, 0.99, dot(n, normalize(vec3(-0.45, 0.55, 0.7))));
	float g2 = smoothstep(0.985, 0.995, dot(n, normalize(vec3(0.5, -0.35, 0.8))));
	vec3 col = film * (0.15 + fres * glow * 1.6) + vec3(1.0) * (g1 * 1.6 + g2 * 1.4);
	ALBEDO = col;
	ALPHA = clamp(0.04 + fres * 0.95 + g1 + g2, 0.0, 1.0);
}
