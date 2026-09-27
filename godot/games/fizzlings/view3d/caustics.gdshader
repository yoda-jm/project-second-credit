shader_type spatial;
// Fizzlings: light from the surface rippling over whatever wears this as its overlay (tiles, heroes, toys), plus an
// optional rim light so a character stands out from the water. Additive, drawn over the model's own material.

render_mode unshaded, blend_add, depth_draw_never, cull_back, shadows_disabled, fog_disabled;

uniform float time_s = 0.0;
uniform vec3 caustic_color : source_color = vec3(0.55, 0.9, 1.0);
uniform float caustic_strength = 0.35;
uniform vec3 rim_color : source_color = vec3(0.6, 0.95, 1.0);
uniform float rim_strength = 0.0;
uniform float rim_power = 2.6;

// a tileable water caustic (after Joe Gardner / Dave Hoskins), cheap: four iterations
float caustic(vec2 p, float t) {
	vec2 i = p;
	float c = 1.0;
	float inten = 0.005;
	for (int n = 0; n < 4; n++) {
		float tt = t * (1.0 - (3.5 / float(n + 1)));
		i = p + vec2(cos(tt - i.x) + sin(tt + i.y), sin(tt - i.y) + cos(tt + i.x));
		c += 1.0 / length(vec2(p.x / (sin(i.x + tt) / inten), p.y / (cos(i.y + tt) / inten)));
	}
	c /= 4.0;
	c = 1.17 - pow(c, 1.4);
	return clamp(pow(abs(c), 6.0), 0.0, 2.0);
}

void fragment() {
	vec3 wp = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec3 wn = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	vec2 p = vec2(wp.x + wp.z * 0.35, wp.y * 0.55 + wp.z * 0.6) * 2.6;
	p = mod(p, 6.2831853) - 250.0;
	float c = caustic(p, time_s * 0.55 + 23.0);
	// strongest on what faces up, still there on what faces us, faint underneath
	float face = clamp(0.45 + 0.75 * wn.y, 0.12, 1.0);
	vec3 col = caustic_color * c * caustic_strength * face;
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), rim_power);
	col += rim_color * rim * rim_strength;
	ALBEDO = col;
}
