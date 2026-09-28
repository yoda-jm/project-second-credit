shader_type spatial;
// The top of a cube: the colour it has reached, a bevel, a soft inner glow and a sheen that sweeps across when it
// changes (flash 1 -> 0).

uniform vec4 color : source_color = vec4(0.3, 0.4, 0.8, 1.0);
uniform float glow = 0.0;
uniform float flash = 0.0;
uniform float time_offset = 0.0;

varying vec3 lp;

void vertex() {
	lp = VERTEX;
}

void fragment() {
	vec2 q = abs(lp.xz) / 0.47;
	float rim = smoothstep(0.78, 0.98, max(q.x, q.y));
	float inset = smoothstep(0.62, 0.66, max(q.x, q.y)) * (1.0 - smoothstep(0.66, 0.70, max(q.x, q.y)));
	float sweep = smoothstep(0.25, 0.0, abs(lp.x + lp.z - mix(-1.2, 1.2, 1.0 - flash))) * flash;
	vec3 c = color.rgb * (1.0 - rim * 0.25) + inset * 0.08;
	ALBEDO = c;
	float pulse = 0.85 + 0.15 * sin(TIME * 2.0 + time_offset);
	EMISSION = color.rgb * glow * pulse * (1.0 - rim * 0.5) * 0.6 + mix(color.rgb, vec3(1.0), 0.4) * (sweep * 0.7 + flash * 0.15);
	ROUGHNESS = 0.42;  // satin: a low sun must not mirror off the tops into the camera
	METALLIC = 0.1;
	SPECULAR = 0.35;
}
