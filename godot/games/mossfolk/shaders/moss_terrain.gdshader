shader_type spatial;
// Mossfolk terrain: the level's pixel mask drawn as carved earth. Air is cut away; earth shows layered rock and soil
// with a bevel lit from the mask's slope, moss and grass where the sky is just above, and darker rims; steel is
// riveted slate. "back" draws the darker slab behind, for depth. mask: 0 air, 0.4 earth, 0.8 steel (R8, w x h).

render_mode cull_disabled;

uniform sampler2D mask : filter_nearest, repeat_disable;
uniform sampler2D mask_soft : filter_linear, repeat_disable;
uniform vec2 size = vec2(640.0, 160.0);
uniform bool back = false;
uniform vec3 col_earth : source_color = vec3(0.45, 0.32, 0.22);
uniform vec3 col_earth2 : source_color = vec3(0.32, 0.22, 0.16);
uniform vec3 col_moss : source_color = vec3(0.35, 0.62, 0.22);
uniform vec3 col_steel : source_color = vec3(0.34, 0.38, 0.45);
uniform float seed = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7)) + seed) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) {
	float v = 0.0; float a = 0.5;
	for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.07; a *= 0.5; }
	return v;
}

float m_at(vec2 px) { return texture(mask, (px + 0.5) / size).r; }

void fragment() {
	vec2 px = floor(UV * size);
	float m = m_at(px);
	// the outline from the filtered mask, so slopes are smooth rather than stair-stepped
	if (texture(mask_soft, UV).r < 0.2) discard;
	if (m < 0.2) m = 0.4;
	bool steel = m > 0.6;
	vec2 texel = 1.0 / size;
	// the bevel: slope of the softened mask
	float sl = texture(mask_soft, UV - vec2(texel.x * 1.5, 0.0)).r;
	float sr = texture(mask_soft, UV + vec2(texel.x * 1.5, 0.0)).r;
	float su = texture(mask_soft, UV - vec2(0.0, texel.y * 1.5)).r;
	float sd = texture(mask_soft, UV + vec2(0.0, texel.y * 1.5)).r;
	vec3 n = normalize(vec3((sl - sr) * 2.2, (sd - su) * 2.2, 1.0));   // UV y runs down the level
	NORMAL = normalize((VIEW_MATRIX * vec4(n.x, -n.y, n.z, 0.0)).xyz);
	// how far the sky is above (moss grows there) and how near any air is (the rim)
	float sky = 0.0;
	for (int i = 1; i <= 4; i++) {
		if (m_at(px - vec2(0.0, float(i))) < 0.2) { sky = 1.0 - float(i - 1) / 4.0; break; }
	}
	float rim = 0.0;
	for (int i = 1; i <= 3; i++) {
		float r = float(i);
		if (m_at(px + vec2(r, 0.0)) < 0.2 || m_at(px - vec2(r, 0.0)) < 0.2 || m_at(px + vec2(0.0, r)) < 0.2) {
			rim = max(rim, 1.0 - (r - 1.0) / 3.0);
		}
	}
	vec3 col;
	if (steel) {
		vec2 b = mod(px, vec2(16.0, 8.0));
		float seam = (b.x < 1.0 || b.y < 1.0) ? 0.55 : 1.0;
		float rivet = (length(b - vec2(3.0, 4.0)) < 1.2 || length(b - vec2(13.0, 4.0)) < 1.2) ? 1.35 : 1.0;
		col = col_steel * seam * rivet * (0.85 + 0.3 * noise(px * 0.3));
		ROUGHNESS = 0.45;
		METALLIC = 0.4;
	} else {
		vec2 pf = UV * size;  // continuous, so the grain is not blocky
		float strata = fbm(vec2(pf.x * 0.02, pf.y * 0.18));
		float grain = noise(pf * 0.6) * 0.6 + noise(pf * 2.3) * 0.4;
		col = mix(col_earth2, col_earth, smoothstep(0.35, 0.65, strata)) * (0.8 + 0.35 * grain);
		// pebbles
		col *= 1.0 + smoothstep(0.72, 0.8, noise(pf * 0.35 + 17.0)) * 0.25;
		// moss on top, with grass tufts
		float tuft = noise(vec2(px.x * 0.7, 0.0)) * 2.0;
		col = mix(col, col_moss * (0.8 + 0.4 * grain), clamp(sky * 1.2 + (sky > 0.9 ? tuft * 0.2 : 0.0), 0.0, 1.0));
		ROUGHNESS = 0.9;
	}
	col *= 1.0 - rim * 0.28 * (1.0 - sky);
	if (back) {
		col *= 0.35;
	}
	ALBEDO = col;
}
