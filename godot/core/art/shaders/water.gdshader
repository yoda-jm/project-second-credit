shader_type spatial;
render_mode cull_disabled;
// Sea: a rolling swell (vertex waves), a seamless normal map scrolled in two layers at different scales and
// directions for the surface detail, depth colour from a blurred land mask (shallows near the coast), foam
// along the shore, view-dependent colour (deep blue below, sky tint at grazing angles) and tight sun glints.
// Screen-space reflections (set in the Environment) add the coast and ships.
uniform vec3 deep : source_color = vec3(0.01, 0.07, 0.17);
uniform vec3 mid : source_color = vec3(0.02, 0.2, 0.34);
uniform vec3 shallow : source_color = vec3(0.06, 0.48, 0.52);
uniform vec3 sky : source_color = vec3(0.55, 0.72, 0.9);
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D shore_mask : filter_linear;
uniform vec2 map_size = vec2(40.0, 28.0);
uniform float detail = 1.0;
varying vec3 world_pos;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float t = TIME;
	vec2 p = world_pos.xz;
	float h = 0.10 * sin(dot(p, vec2(0.8, 0.6)) * 0.7 + t * 1.1)
		+ 0.06 * sin(dot(p, vec2(-0.4, 0.9)) * 1.3 + t * 1.6)
		+ 0.035 * sin(dot(p, vec2(0.95, -0.3)) * 2.1 + t * 2.3);
	VERTEX.y += h;
	// analytic normal of the swell
	float dx = 0.10 * 0.7 * 0.8 * cos(dot(p, vec2(0.8, 0.6)) * 0.7 + t * 1.1) + 0.06 * 1.3 * -0.4 * cos(dot(p, vec2(-0.4, 0.9)) * 1.3 + t * 1.6)
		+ 0.035 * 2.1 * 0.95 * cos(dot(p, vec2(0.95, -0.3)) * 2.1 + t * 2.3);
	float dz = 0.10 * 0.7 * 0.6 * cos(dot(p, vec2(0.8, 0.6)) * 0.7 + t * 1.1) + 0.06 * 1.3 * 0.9 * cos(dot(p, vec2(-0.4, 0.9)) * 1.3 + t * 1.6)
		+ 0.035 * 2.1 * -0.3 * cos(dot(p, vec2(0.95, -0.3)) * 2.1 + t * 2.3);
	NORMAL = normalize(vec3(-dx, 1.0, -dz));
	TANGENT = normalize(vec3(1.0, dx, 0.0));
	BINORMAL = normalize(vec3(0.0, dz, 1.0));
}

void fragment() {
	float t = TIME;
	vec2 p = world_pos.xz;
	vec2 muv = (p + 0.5) / map_size;
	float land = texture(shore_mask, clamp(muv, vec2(0.0), vec2(1.0))).r;
	if (muv.x < 0.0 || muv.y < 0.0 || muv.x > 1.0 || muv.y > 1.0) { land = 0.0; }
	// two scrolling layers of the same seamless normal map, blended (whiteout blend)
	vec3 n1 = texture(normal_map, p * 0.07 + vec2(t * 0.010, t * 0.007)).rgb * 2.0 - 1.0;
	vec3 n2 = texture(normal_map, p * 0.16 + vec2(-t * 0.015, t * 0.012)).rgb * 2.0 - 1.0;
	vec3 n3 = texture(normal_map, p * 0.05 + vec2(t * 0.004, -t * 0.006)).rgb * 2.0 - 1.0;
	vec3 nb = normalize(vec3(n1.xy + n2.xy * 0.7 + n3.xy * 0.4, 1.0));
	NORMAL_MAP = nb * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 1.0 * detail;
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 5.0);
	float depth = smoothstep(0.05, 0.55, land);
	vec3 col = mix(deep, mid, 0.55 + 0.15 * nb.x);
	col = mix(col, shallow, depth);
	col = mix(col, sky, fres * 0.6);
	// foam: bands moving towards the shore, broken up by the normal map
	float band = sin(land * 30.0 - t * 2.2) * 0.5 + 0.5;
	float foam = smoothstep(0.25, 0.5, land) * smoothstep(0.75, 0.35, land) * smoothstep(0.55, 0.95, band * (0.6 + nb.x * 1.5));
	foam += smoothstep(0.42, 0.5, land) * 0.8;
	foam = clamp(foam, 0.0, 1.0);
	ALBEDO = mix(col, vec3(0.92, 0.96, 1.0), foam);
	ROUGHNESS = mix(0.04, 0.6, foam);
	METALLIC = 0.0;
	SPECULAR = 0.55;
	EMISSION = vec3(0.9) * foam * 0.1;
}
