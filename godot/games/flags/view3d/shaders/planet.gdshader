shader_type spatial;
// Iron Flags ground: the planet's base texture and a second one mixed by a soft noise, rough ground (COLOR.r),
// roads (COLOR.g), scorch marks (COLOR.b), and the territories: each tile tinted by its owner's colour, with a glowing
// line where two territories meet. Textures are CC0 (ambientCG), mapped in world space so tiles join seamlessly.
uniform sampler2D base_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D base_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D alt_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D alt_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D road_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D road_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec3 base_tint = vec3(1.0);
uniform vec3 alt_tint = vec3(1.0);
uniform vec3 road_tint = vec3(1.0);
uniform float scale = 0.3;
uniform sampler2D owners : source_color, filter_linear;   // one pixel per tile: the owner's colour, alpha = strength
uniform sampler2D zone_ids : filter_nearest;             // one pixel per tile: zone index / 255
uniform vec2 map_size = vec2(64.0);
uniform float tint_strength = 0.22;
uniform float time_offset = 0.0;
varying vec3 world_pos;
varying vec3 world_normal;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec2 uv = world_pos.xz * scale;
	float patch = smoothstep(0.3, 0.7, 0.5 + 0.5 * sin(world_pos.x * 0.21 + sin(world_pos.z * 0.17) * 2.3) * cos(world_pos.z * 0.19 + world_pos.x * 0.07));
	vec3 base = texture(base_albedo, uv).rgb * base_tint;
	vec3 alt = texture(alt_albedo, uv * 0.7).rgb * alt_tint;
	vec3 c = mix(base, alt, clamp(patch * 0.45 + COLOR.r, 0.0, 1.0));
	vec3 n = mix(texture(base_normal, uv).rgb, texture(alt_normal, uv * 0.7).rgb, clamp(patch * 0.45 + COLOR.r, 0.0, 1.0));
	vec3 road = texture(road_albedo, uv * 1.4).rgb * road_tint;
	float rd = smoothstep(0.3, 0.55, COLOR.g);  // crisp road edges from the soft corner blend
	c = mix(c, road, rd);
	n = mix(n, texture(road_normal, uv * 1.4).rgb, rd);
	c *= 1.0 - COLOR.b * 0.75;  // scorched
	// territories: map point (x, y) is at world (x - 0.5, y - 0.5), as in the shared water shader
	vec2 mp = (world_pos.xz + vec2(0.5)) / map_size;
	vec4 own = texture(owners, mp);
	c = mix(c, c * 0.6 + own.rgb * 0.55, own.a * tint_strength);
	vec2 px = 1.0 / map_size;
	float id = texture(zone_ids, mp).r;
	float edge = 0.0;
	for (int k = 0; k < 4; k++) {
		vec2 o = vec2(k == 0 ? 1.0 : (k == 1 ? -1.0 : 0.0), k == 2 ? 1.0 : (k == 3 ? -1.0 : 0.0)) * px * 0.07;
		edge = max(edge, step(0.001, abs(texture(zone_ids, mp + o).r - id)));
	}
	float dash = step(0.35, fract((world_pos.x + world_pos.z) * 0.8));
	c = mix(c, own.rgb * 1.2 + 0.1, edge * dash * 0.8 * max(own.a, 0.35));
	EMISSION = own.rgb * edge * dash * 0.6 * own.a;
	if (abs(world_normal.y) < 0.6) { c = alt * 0.7; }
	ALBEDO = c;
	NORMAL_MAP = n;
	ROUGHNESS = 0.9 - rd * 0.2;
}
