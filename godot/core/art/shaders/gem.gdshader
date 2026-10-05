shader_type spatial;
render_mode specular_schlick_ggx, depth_draw_always;
// Gems: refraction of what lies behind (with colour dispersion), strong fresnel, facet flashes that travel
// with time and the view, tiny dark inclusions and hairline cracks inside. Emission feeds the glow.
uniform vec3 gem_color : source_color = vec3(0.2, 0.85, 1.0);
uniform float glow = 1.6;
uniform float refraction = 0.06;
uniform sampler2D screen : hint_screen_texture, filter_linear_mipmap;
varying vec3 local_pos;
varying vec3 world_pos;

float hash3(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
float noise3(vec3 p) {
	vec3 i = floor(p); vec3 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash3(i), hash3(i + vec3(1,0,0)), f.x), mix(hash3(i + vec3(0,1,0)), hash3(i + vec3(1,1,0)), f.x), f.y),
	           mix(mix(hash3(i + vec3(0,0,1)), hash3(i + vec3(1,0,1)), f.x), mix(hash3(i + vec3(0,1,1)), hash3(i + vec3(1,1,1)), f.x), f.y), f.z);
}
// distance to the nearest cell border of a 3D voronoi: thin lines = cracks
float crack(vec3 p) {
	vec3 i = floor(p); vec3 f = fract(p);
	float d1 = 8.0; float d2 = 8.0;
	for (int z = -1; z <= 1; z++) for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) {
		vec3 g = vec3(float(x), float(y), float(z));
		vec3 o = vec3(hash3(i + g), hash3(i + g + 17.0), hash3(i + g + 31.0));
		float d = length(g + o - f);
		if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) { d2 = d; }
	}
	return d2 - d1;
}

void vertex() {
	local_pos = VERTEX;
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float ndv = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float fres = pow(1.0 - ndv, 3.0);
	// refraction with a little dispersion: each channel bends a bit differently
	vec2 bend = NORMAL.xy * refraction;
	vec3 behind = vec3(texture(screen, SCREEN_UV - bend * 1.0).r, texture(screen, SCREEN_UV - bend * 1.15).g,
		texture(screen, SCREEN_UV - bend * 1.3).b);
	// facet flashes: each flat facet lights up when its normal lines up with a slowly turning "light"
	vec3 wn = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
	vec3 flash_dir = normalize(vec3(sin(TIME * 0.7), 0.8, cos(TIME * 0.9)));
	float flash = pow(max(0.0, dot(reflect(-normalize((INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz), wn), flash_dir)), 60.0);
	// inside: inclusions (dark specks) and hairline cracks, in object space so they stay with the gem
	float specks = smoothstep(0.83, 0.9, noise3(local_pos * 22.0));
	float cracks = 1.0 - smoothstep(0.0, 0.035, crack(local_pos * 5.0 + 3.0));
	vec3 body = gem_color * (0.6 + 0.4 * behind) * (1.0 - 0.6 * specks);
	ALBEDO = body * 0.25;
	METALLIC = 0.0;
	ROUGHNESS = 0.03;
	SPECULAR = 1.0;
	EMISSION = body * glow * (0.55 + 0.9 * fres) + vec3(0.85, 0.95, 1.0) * (cracks * 0.35 + flash * 3.0 + fres * 0.3);
}
