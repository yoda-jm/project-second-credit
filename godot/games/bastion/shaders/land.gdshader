shader_type spatial;
// Land tiles with CC0 PBR textures (ambientCG): grass inland, sand at the shore (instance COLOR.r), rock where
// COLOR.g, territory tint from COLOR.b. World-space top mapping, so neighbouring tiles join seamlessly.
uniform sampler2D grass_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D grass_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D lush_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D lush_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D sand_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D sand_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rock_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rock_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float scale = 0.35;
varying vec3 world_pos;
varying vec3 world_normal;
void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}
void fragment() {
	vec2 uv = abs(world_normal.y) > 0.5 ? world_pos.xz * scale : (abs(world_normal.x) > 0.5 ? world_pos.zy : world_pos.xy) * scale;
	// two grasses mixed by a large, soft noise so fields vary instead of repeating one tile
	float patch = smoothstep(0.35, 0.65, 0.5 + 0.5 * sin(world_pos.x * 0.37 + sin(world_pos.z * 0.23) * 2.0) * cos(world_pos.z * 0.29 + world_pos.x * 0.11));
	vec3 g = mix(texture(lush_albedo, uv * 0.8).rgb, texture(grass_albedo, uv).rgb * vec3(0.85, 0.95, 0.75), patch * 0.6);
	vec3 s = texture(sand_albedo, uv * 1.3).rgb * vec3(0.95, 0.9, 0.8);
	vec3 r = texture(rock_albedo, uv).rgb;
	vec3 c = mix(g, s, clamp(COLOR.r, 0.0, 1.0));
	c = mix(c, r, COLOR.g);
	c = mix(c, c * vec3(0.8, 0.9, 1.2) + vec3(0.02, 0.03, 0.08), COLOR.b * 0.5);
	if (abs(world_normal.y) < 0.5) { c = mix(s, r, 0.35) * 0.75; }  // tile sides: earth and stone
	ALBEDO = c;
	vec3 gn = mix(texture(lush_normal, uv * 0.8).rgb, texture(grass_normal, uv).rgb, patch * 0.6);
	vec3 n = mix(gn, texture(sand_normal, uv * 1.3).rgb, clamp(COLOR.r, 0.0, 1.0));
	NORMAL_MAP = mix(n, texture(rock_normal, uv).rgb, COLOR.g);
	ROUGHNESS = 0.92;
}
