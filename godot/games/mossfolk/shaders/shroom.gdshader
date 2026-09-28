shader_type spatial;
// Mossfolk: the glowing mushrooms' caps and gills. A glossy cap in the level's colours, a coloured rim of light, a
// glow from within (brighter where the cap is thin, at its edge), speckles that twinkle, and the whole cap flaring
// when something bumps it (the instance's "excite", set by MossGarden). Gills and spots ("part" 1) glow outright.

uniform vec3 cap_col : source_color = vec3(0.45, 0.2, 0.8);
uniform vec3 glow_col : source_color = vec3(0.3, 1.0, 0.9);
uniform vec3 speck_col : source_color = vec3(0.8, 1.0, 1.0);
uniform int part = 0;              // 0 the cap, 1 the gills and spots
uniform float glow_energy = 1.0;
instance uniform float excite = 0.0;
instance uniform float phase = 0.0;

varying vec3 lp;

float hash(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }

void vertex() {
	lp = VERTEX;
}

void fragment() {
	float pulse = 0.75 + 0.25 * sin(TIME * 1.6 + phase * 6.283);
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.5);
	if (part == 1) {
		ALBEDO = glow_col * 0.5;
		EMISSION = glow_col * glow_energy * (1.6 * pulse + 2.5 * excite);
		ROUGHNESS = 0.4;
	} else {
		// speckles: a coarse grid in the model's space, a few cells lit, each twinkling at its own pace
		vec3 cell = floor(lp * 26.0);
		float h = hash(cell);
		vec3 f = fract(lp * 26.0) - 0.5;
		float dot_ = smoothstep(0.32, 0.05, length(f)) * step(0.82, h);
		float tw = 0.5 + 0.5 * sin(TIME * (1.5 + h * 3.0) + h * 40.0);
		// darker at the rim underneath, brighter up top: the cap reads as a dome
		float up = clamp(NORMAL.y * 0.5 + 0.5, 0.0, 1.0);
		vec3 base = cap_col * (0.55 + 0.6 * up);
		ALBEDO = base;
		ROUGHNESS = 0.28;
		SPECULAR = 0.7;
		CLEARCOAT = 1.0;
		CLEARCOAT_ROUGHNESS = 0.08;
		SSS_STRENGTH = 0.5;
		BACKLIGHT = mix(cap_col, glow_col, 0.5) * 0.6;
		EMISSION = glow_energy * (glow_col * fres * (1.1 + 1.5 * excite)
			+ mix(cap_col, glow_col, 0.3) * (0.1 * pulse + 0.35 * excite)
			+ speck_col * dot_ * (0.8 + 2.2 * tw) * (1.0 + excite));
	}
}
