shader_type spatial;
// Old-fashioned wallpaper: two-tone vertical stripes with a small repeating motif, above a painted wooden wainscot.
// Mapped in world space on the room's back wall (x along the wall, y up).

uniform vec3 base : source_color = vec3(0.45, 0.62, 0.7);
uniform vec3 stripe : source_color = vec3(0.55, 0.72, 0.8);
uniform vec3 motif : source_color = vec3(0.3, 0.42, 0.5);
uniform vec3 wainscot : source_color = vec3(0.92, 0.9, 0.84);
uniform float panel_top = 1.3;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float motif_mask(vec2 p) {
	// a little four-petal flower on a diamond grid
	vec2 g = vec2(p.x * 2.0, p.y * 2.0);
	g.x += floor(g.y) * 0.5;
	vec2 f = fract(g) - 0.5;
	float r = length(f);
	float a = atan(f.y, f.x);
	float petals = 0.13 + 0.05 * cos(a * 4.0);
	return smoothstep(petals, petals - 0.02, r) * (1.0 - smoothstep(0.02, 0.0, r - 0.03));
}

void fragment() {
	vec2 p = wpos.xy;
	if (p.y < panel_top) {
		// the wainscot: panels with a darker frame and a top rail
		vec2 q = vec2(fract(p.x / 1.6), p.y / panel_top);
		float frame = step(q.x, 0.06) + step(0.94, q.x) + step(q.y, 0.08) + step(0.86, q.y);
		vec3 c = wainscot * (1.0 - 0.18 * clamp(frame, 0.0, 1.0));
		c *= 1.0 - 0.25 * smoothstep(panel_top - 0.12, panel_top, p.y);
		ALBEDO = c;
		ROUGHNESS = 0.45;
	} else {
		float s = step(0.5, fract(p.x * 1.4));
		vec3 c = mix(base, stripe, s * 0.6);
		c = mix(c, motif, motif_mask(p) * 0.7);
		ALBEDO = c;
		ROUGHNESS = 0.85;
	}
}
