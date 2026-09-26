shader_type spatial;
render_mode unshaded, shadows_disabled;
// What the alley sees through an open window: the lit room behind, in that room's wallpaper, with a lamp hanging
// in the middle, curtains at the sides and the floor at the bottom. Dark while the shutters are closed. On a quad
// (UV 0-1, v down).

uniform float open = 0.0;
uniform vec3 paper : source_color = vec3(0.7, 0.52, 0.3);
uniform float flicker = 1.0;

void fragment() {
	vec2 uv = UV;
	float lamp = exp(-length((uv - vec2(0.5, 0.18)) * vec2(1.3, 1.8)) * 2.6);
	vec3 room = paper * (0.35 + 1.4 * lamp);
	room *= 0.88 + 0.12 * step(0.5, fract(uv.x * 7.0));
	room = mix(room, vec3(0.9, 0.85, 0.75) * (0.4 + 0.6 * lamp), step(0.68, uv.y) * step(uv.y, 0.72));  // dado rail
	room = mix(room, vec3(0.35, 0.2, 0.12) * (0.5 + lamp), step(0.86, uv.y));  // floor
	float shade = step(abs(uv.x - 0.5), 0.07 + (uv.y - 0.05) * 0.4) * step(0.05, uv.y) * step(uv.y, 0.16);
	room = mix(room, vec3(1.6, 1.25, 0.8), shade);  // the lamp shade
	room = mix(room, vec3(0.08), step(abs(uv.x - 0.5), 0.006) * step(uv.y, 0.05));
	float side = max(smoothstep(0.16, 0.1, uv.x), smoothstep(0.84, 0.9, uv.x));
	vec3 curtain = vec3(0.45, 0.1, 0.12) * (0.6 + 0.4 * sin(uv.x * 90.0)) * (0.5 + lamp);
	room = mix(room, curtain, side);
	ALBEDO = mix(vec3(0.012, 0.012, 0.02), room * 1.3 * flicker, open);
}
