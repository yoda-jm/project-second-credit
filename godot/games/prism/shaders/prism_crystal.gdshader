shader_type spatial;
render_mode specular_schlick_ggx, cull_back, depth_draw_always;
// Prism Breaker crystal: thick glass that refracts the glowing core and the stage behind it, tinted by its colour,
// with a bright fresnel rim, an inner glow and a flash when it is hit or a shock wave passes ("flash", per brick).
instance uniform vec4 tint : source_color = vec4(1.0, 0.3, 0.3, 1.0);
instance uniform float flash = 0.0;
uniform float refraction = 0.045;
uniform float rim = 1.4;
uniform float body = 0.1;
uniform sampler2D screen : hint_screen_texture, filter_linear_mipmap;
varying vec3 lpos;

void vertex() {
	lpos = VERTEX;
}

void fragment() {
	vec3 c = tint.rgb;
	float nv = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float fres = pow(1.0 - nv, 3.0);
	vec2 off = NORMAL.xy * refraction + (lpos.xy * vec2(0.02, 0.05));
	vec3 behind = textureLod(screen, SCREEN_UV - off, 1.5).rgb;
	// facet flashes that travel across the face with time
	float sweep = smoothstep(0.96, 1.0, sin(lpos.x * 2.2 - lpos.y * 3.0 + TIME * 1.3) * 0.5 + 0.5);
	float inner = 1.0 - smoothstep(0.0, 0.55, length(lpos.xy * vec2(1.0, 1.8)));
	ALBEDO = c * 0.08;
	ROUGHNESS = 0.06;
	METALLIC = 0.25;
	SPECULAR = 0.9;
	EMISSION = behind * c * 0.55 + c * (body + inner * 0.25 + fres * rim + sweep * 0.6)
		+ mix(c, vec3(1.0), 0.6) * flash * 3.0;
}
