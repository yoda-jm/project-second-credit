shader_type spatial;
// Mossfolk terrain: the level's rock, both the front face (a quad; the pixel mask cuts the air away) and the carved
// walls extruded behind it (MossSlab). Earth is layered soil and rock (CC0 texture sets) with roots under the moss,
// wet streaks and glowing crystals embedded; moss and grass grow wherever the sky is just above and on every
// upward face; steel is riveted metal plate. mask: R solid, G steel (w x h pixels).

render_mode cull_back;

uniform sampler2D mask : filter_nearest, repeat_disable;
uniform sampler2D mask_soft : filter_linear, repeat_disable;
uniform vec2 size = vec2(640.0, 160.0);
uniform bool wall = false;
uniform float px_size = 0.1;
uniform float front = 0.35;
uniform float depth = 2.4;
uniform vec3 col_earth : source_color = vec3(0.45, 0.32, 0.22);
uniform vec3 col_earth2 : source_color = vec3(0.32, 0.22, 0.16);
uniform vec3 col_moss : source_color = vec3(0.35, 0.62, 0.22);
uniform vec3 col_steel : source_color = vec3(0.34, 0.38, 0.45);
uniform vec3 col_glow : source_color = vec3(0.55, 0.85, 1.0);
uniform float seed = 0.0;
uniform sampler2D rock_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rock_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D soil_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D soil_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D moss_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D moss_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D metal_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D metal_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;

varying vec3 wpos;
varying vec3 wnrm;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7)) + seed) * 43758.5453); }
vec2 hash2(vec2 p) { return vec2(hash(p), hash(p + vec2(17.3, 5.9))); }
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

vec2 m_at(vec2 px) { return texture(mask, (floor(px) + 0.5) / size).rg; }
bool air(vec2 px) { return px.y >= 0.0 && px.y < size.y && px.x >= 0.0 && px.x < size.x && m_at(px).r < 0.5; }

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	// this point in level pixels (y down); walls look just inside the rock
	vec2 pp = vec2(wpos.x / px_size, size.y - wpos.y / px_size);
	vec2 pin = pp;
	vec2 tuv;
	float back = 0.0;   // 0 at the front face, 1 at the rear of the slab
	if (wall) {
		pin -= vec2(wnrm.x, -wnrm.y) * 0.6;
		tuv = UV;
		back = clamp((front - wpos.z) / (front + depth), 0.0, 1.0);
	} else {
		if (texture(mask_soft, UV).r < 0.5) discard;
		tuv = vec2(wpos.x, -wpos.y);
	}
	tuv *= 0.26;
	vec2 m = m_at(pin);
	bool steel = m.g > 0.5;
	vec3 nmap = vec3(0.5, 0.5, 1.0);
	vec3 col;
	float rough = 0.9;
	float metal = 0.0;
	vec3 emit = vec3(0.0);
	if (steel) {
		vec2 b = mod(wall ? tuv / 0.042 : pp, vec2(16.0, 8.0));
		float seam = (b.x < 1.0 || b.y < 1.0) ? 0.5 : 1.0;
		float rivet = (length(b - vec2(3.0, 4.0)) < 1.2 || length(b - vec2(13.0, 4.0)) < 1.2) ? 1.5 : 1.0;
		col = texture(metal_albedo, tuv).rgb * col_steel * 2.2 * seam * rivet;
		nmap = texture(metal_normal, tuv).rgb;
		rough = 0.35;
		metal = 0.7;
	} else {
		// how deep under the surface: a quick look up for the sky (moss) and a coarse one for the roots
		float sky = 0.0;
		float wet_n;
		if (wall) {
			sky = smoothstep(0.35, 0.8, wnrm.y);
			// bare patches on the ledges, more of them towards the back
			float bare = fbm(vec2(wpos.x * 1.1, wpos.z * 1.6) + seed);
			sky *= 1.0 - smoothstep(0.5, 0.68, bare) * (0.35 + 0.55 * back);
			wet_n = sky > 0.0 ? 0.0 : noise(vec2(pp.x * 0.35 + pp.y * 0.35, wpos.z * 0.6));
		} else {
			// moss hangs a ragged few pixels over the edge, with the odd longer tendril
			float md = 3.0 + 4.0 * noise(vec2(pp.x * 0.25, 3.0)) + step(0.88, hash(vec2(floor(pp.x / 1.5), 7.0))) * (2.0 + 6.0 * hash(vec2(floor(pp.x / 1.5), 8.0)));
			for (int i = 1; i <= 13; i++) {
				if (air(pp - vec2(0.0, float(i)))) { sky = clamp(1.0 - float(i - 1) / md, 0.0, 1.0); break; }
			}
			wet_n = noise(vec2(pp.x * 0.35, pp.y * 0.025 + seed));
		}
		float under = 40.0;
		if (!wall) {
			for (int i = 1; i <= 6; i++) {
				if (air(pp - vec2(0.0, float(i) * 6.0))) { under = float(i) * 6.0; break; }
			}
		}
		float strata = fbm(vec2(pp.x * 0.018, pp.y * 0.13));
		vec3 soil = texture(soil_albedo, tuv).rgb;
		vec3 rock = texture(rock_albedo, tuv * 0.8).rgb;
		float rk = smoothstep(0.4, 0.62, strata);
		col = mix(soil * col_earth * 2.4, rock * col_earth2 * 2.6, rk);
		nmap = mix(texture(soil_normal, tuv).rgb, texture(rock_normal, tuv * 0.8).rgb, rk);
		// stones set in the earth, rounded, darker in the crevice round them
		if (!wall) {
			vec2 sc = floor(pp / 9.0);
			float best = 9.0;
			vec2 bd = vec2(0.0);
			float bh = 0.0;
			float jag = (noise(pp * 0.7) - 0.5) * 0.25;
			for (int yy = -1; yy <= 1; yy++) {
				for (int xx = -1; xx <= 1; xx++) {
					vec2 cc = sc + vec2(float(xx), float(yy));
					vec2 dd = pp - (cc + 0.15 + hash2(cc + 4.2) * 0.7) * 9.0;
					float rr = 2.0 + hash(cc + 2.3) * 2.6;
					float q = length(dd * vec2(0.85, 1.3)) / rr + jag;
					if (hash(cc + 6.1) > 0.6 && q < best) { best = q; bd = dd / rr; bh = hash(cc); }
				}
			}
			if (best < 1.05) {
				vec3 stone = texture(rock_albedo, tuv * 1.6 + bh).rgb * mix(col_earth2, vec3(0.62, 0.6, 0.58), 0.45 + bh * 0.2) * 2.4;
				float in_s = smoothstep(1.02, 0.86, best);
				col = mix(col * 0.55, stone, in_s);
				nmap = mix(nmap, normalize(vec3(0.5 + bd.x * 0.4, 0.5 - bd.y * 0.4, 1.0)), in_s);
				rough = mix(rough, 0.5, in_s);
			}
		}
		// roots hanging down from the moss
		float wob = noise(vec2(pp.x * 0.08, pp.y * 0.05)) * 5.0;
		float root = smoothstep(0.035, 0.0, abs(noise(vec2(pp.x * 0.22 + wob, pp.y * 0.03)) - 0.5));
		root *= smoothstep(34.0, 8.0, under) * step(0.001, 1.0 - sky);
		col = mix(col, col_earth2 * 0.45, root * 0.8);
		// wet streaks: darker, glossy
		float wet = smoothstep(0.62, 0.78, wet_n);
		col *= 1.0 - wet * 0.3;
		rough = mix(0.92, 0.18, wet);
		// embedded crystals, glowing
		if (!wall && sky < 0.01) {
			vec2 cell = floor(pp / 11.0);
			vec2 c = (cell + 0.2 + hash2(cell) * 0.6) * 11.0;
			vec2 d = pp - c;
			float ang = hash(cell + 1.7) * 3.0 - 1.5;
			d = mat2(vec2(cos(ang), sin(ang)), vec2(-sin(ang), cos(ang))) * d;
			float r = 0.9 + hash(cell + 3.1) * 1.3;
			float facet = max(abs(d.x) * 1.8 + abs(d.y) * 0.45, abs(d.y) * 0.8);
			bool has = hash(cell + 9.7) > 0.9 && under > 12.0;
			if (has && facet < r) {
				float pulse = 0.7 + 0.3 * sin(TIME * 1.7 + hash(cell) * 6.28);
				col = col_glow * 0.7;
				emit = col_glow * (0.4 + 0.9 * (1.0 - facet / r)) * pulse;
				nmap = vec3(0.5 + sign(d.x) * 0.3, 0.5 - sign(d.y) * 0.2, 0.8);
				rough = 0.08;
			} else {
				// a faint glow round them, as if lit from within the rock
				emit = col_glow * 0.06 * smoothstep(r * 3.0, r, facet) * (has ? 1.0 : 0.0);
			}
		}
		// moss and grass on top
		float mo = clamp(sky * 1.6, 0.0, 1.0);
		vec3 moss = texture(moss_albedo, tuv * 1.3).rgb * col_moss * 2.3;
		moss *= 0.75 + 0.45 * noise(pp * 0.15 + wpos.z);
		// glowing pips in the moss
		vec2 pc = floor(pp / 3.0);
		if (!wall && mo > 0.5 && hash(pc + 2.9) > 0.93 && length(pp - (pc + 0.5) * 3.0) < 0.7) {
			emit += col_glow * 1.4 * (0.6 + 0.4 * sin(TIME * 2.3 + hash(pc) * 6.28));
		}
		col = mix(col, moss, mo);
		nmap = mix(nmap, texture(moss_normal, tuv * 1.3).rgb, mo);
		rough = mix(rough, 0.75, mo);
		emit += col_moss * 0.04 * mo;
	}
	// deeper in the slab, darker (the rock closes in)
	col *= mix(1.0, 0.35, back * back);
	if (!wall) {
		// the front face's lip: a rounded bevel from the softened mask
		vec2 texel = 1.0 / size;
		float sl = texture(mask_soft, UV - vec2(texel.x * 1.5, 0.0)).r;
		float sr = texture(mask_soft, UV + vec2(texel.x * 1.5, 0.0)).r;
		float su = texture(mask_soft, UV - vec2(0.0, texel.y * 1.5)).r;
		float sd = texture(mask_soft, UV + vec2(0.0, texel.y * 1.5)).r;
		vec3 n = normalize(vec3((sl - sr) * 1.6, (sd - su) * 1.6, 1.0));
		NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
	}
	ALBEDO = col;
	NORMAL_MAP = nmap;
	NORMAL_MAP_DEPTH = 1.1;
	ROUGHNESS = rough;
	METALLIC = metal;
	SPECULAR = 0.5;
	EMISSION = emit;
}
