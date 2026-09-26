shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
// A soft shaft of moonlight falling from a window (a quad, UV.y 0 at the window): brightest near the window,
// fading along its length and at the edges, with faint streaks that drift. `spread` narrows the top into a cone
// (the street lamps).

uniform vec3 tint : source_color = vec3(0.55, 0.65, 1.0);
uniform float strength = 0.12;
uniform float spread = 0.0;

float hash(float n) { return fract(sin(n) * 43758.5453); }
float noise(float x) { float i = floor(x); float f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(hash(i), hash(i + 1.0), f); }

void fragment() {
	float x = (UV.x - 0.5) / mix(1.0 - spread, 1.0, UV.y) + 0.5;
	float edge = smoothstep(0.0, 0.3, x) * smoothstep(1.0, 0.7, x);
	float along = smoothstep(0.0, 0.08, UV.y) * (1.0 - UV.y) * (1.0 - UV.y);
	float streaks = 0.6 + 0.4 * noise(UV.x * 14.0 + TIME * 0.15) * noise(UV.x * 5.0 - TIME * 0.1 + 3.0);
	ALBEDO = tint * strength * edge * along * streaks;
}
