shader_type spatial;
// Inkstorm board: open ground is dark parchment washed with drifting ink; claimed land rises out of it as a painted
// relief (water, meadow, hills, rock, peaks by height) with earth-coloured cliffs and a gilt edge. The rise plays
// after the land is claimed. mask: 1 where claimed (linear filtered, W x H); claimed_at: the claim time per cell
// (nearest filtered); height_map: the relief (0..1), shared with the game script so props sit on it.

render_mode cull_back;

uniform sampler2D mask : filter_linear, repeat_disable;
uniform sampler2D claimed_at : filter_nearest, repeat_disable;
uniform sampler2D height_map : filter_linear, repeat_enable;
uniform sampler2D paper : filter_linear_mipmap, repeat_enable;
uniform float now = 0.0;
uniform float rise_time = 0.9;
uniform float land_height = 0.42;
uniform float water_level = 0.3;
uniform vec3 col_water : source_color = vec3(0.18, 0.42, 0.62);
uniform vec3 col_low : source_color = vec3(0.45, 0.66, 0.28);
uniform vec3 col_mid : source_color = vec3(0.28, 0.5, 0.2);
uniform vec3 col_high : source_color = vec3(0.55, 0.5, 0.42);
uniform vec3 col_peak : source_color = vec3(0.93, 0.93, 0.9);
uniform vec3 col_cliff : source_color = vec3(0.42, 0.3, 0.2);
uniform vec3 col_parchment : source_color = vec3(0.16, 0.13, 0.12);
uniform vec3 col_ink : source_color = vec3(0.07, 0.05, 0.1);
uniform vec3 col_gilt : source_color = vec3(1.0, 0.78, 0.35);

varying float v_land;
varying float v_h;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) {
	float v = 0.0; float a = 0.5;
	for (int i = 0; i < 5; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; }
	return v;
}

float rise_at(vec2 uv) {
	float t = texture(claimed_at, uv).r;
	if (t < -0.5 && t > -1.5) return 0.0;  // never claimed (-1)
	return smoothstep(0.0, rise_time, now - t);
}

float disp(vec2 uv) {
	float m = texture(mask, uv).r;
	float h = texture(height_map, uv).r;
	float relief = max(h, water_level);
	return smoothstep(0.35, 0.65, m) * rise_at(uv) * land_height * (0.25 + relief * 0.9);
}

void vertex() {
	float d = disp(UV);
	v_h = texture(height_map, UV).r;
	v_land = d > 0.0005 ? smoothstep(0.35, 0.65, texture(mask, UV).r) * rise_at(UV) : 0.0;
	VERTEX.y += d;
	// the normal from the neighbouring heights (board 12.8 x 9.6, sampled a cell's half apart)
	vec2 e = vec2(1.0 / 256.0, 1.0 / 192.0);
	float dx = disp(UV + vec2(e.x, 0.0)) - disp(UV - vec2(e.x, 0.0));
	float dz = disp(UV + vec2(0.0, e.y)) - disp(UV - vec2(0.0, e.y));
	NORMAL = normalize(vec3(-dx, 2.0 * 12.8 * e.x, -dz));
}

void fragment() {
	vec2 uv = UV;
	vec3 up_v = (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz;
	float flat_ = clamp(dot(normalize(NORMAL), up_v), 0.0, 1.0);
	float m = texture(mask, uv).r;
	float land = v_land;
	float grain = texture(paper, uv * 6.0).r;
	// the open ground: parchment under slowly drifting ink
	vec2 drift = vec2(now * 0.01, -now * 0.007);
	float wash = fbm(uv * vec2(9.0, 7.0) + drift) * 0.7 + fbm(uv * vec2(23.0, 17.0) - drift * 2.0) * 0.3;
	vec3 open_col = mix(col_ink, col_parchment, smoothstep(0.3, 0.75, wash)) * (0.8 + grain * 0.35);
	// the land, painted by height, with brush strokes
	float h = v_h + (fbm(uv * 40.0) - 0.5) * 0.08;
	vec3 land_col;
	if (h < water_level) {
		float ripple = fbm(uv * vec2(60.0, 30.0) + vec2(now * 0.05, 0.0));
		land_col = mix(col_water * 0.8, col_water * 1.25, ripple);
	} else if (h < 0.45) {
		land_col = mix(col_low, col_mid, smoothstep(water_level, 0.45, h));
	} else if (h < 0.62) {
		land_col = mix(col_mid, col_high, smoothstep(0.45, 0.62, h));
	} else {
		land_col = mix(col_high, col_peak, smoothstep(0.66, 0.8, h));
	}
	float stroke = fbm(uv * vec2(90.0, 25.0));
	land_col *= 0.85 + stroke * 0.3;
	land_col = mix(land_col, col_cliff * (0.8 + stroke * 0.4), 1.0 - smoothstep(0.35, 0.8, flat_));
	// the gilt edge where land meets the open ground
	float edge = 1.0 - abs(m - 0.5) * 2.0;
	edge = smoothstep(0.55, 0.95, edge);
	vec3 col = mix(open_col, land_col, land);
	col = mix(col, col_gilt, edge * 0.85);
	ALBEDO = col * (0.9 + grain * 0.15);
	ROUGHNESS = mix(0.95, h < water_level ? 0.25 : 0.85, land);
	EMISSION = col_gilt * edge * 0.9 + open_col * (1.0 - land) * 0.15;
}
