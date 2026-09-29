// Lantern Links booster pad: glowing chevrons that race along the push direction (the plane's -Z in local space).
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, shadows_disabled;

uniform vec3 col : source_color = vec3(1.0, 0.55, 0.15);

void fragment() {
	vec2 uv = UV - 0.5;
	float v = fract(uv.y * 2.5 + abs(uv.x) * 1.6 + TIME * 1.8);
	float chevron = smoothstep(0.0, 0.08, v) * smoothstep(0.42, 0.3, v);
	float edge = smoothstep(0.5, 0.42, abs(uv.x)) * smoothstep(0.5, 0.42, abs(uv.y));
	ALBEDO = col * chevron * edge * 1.6;
}
