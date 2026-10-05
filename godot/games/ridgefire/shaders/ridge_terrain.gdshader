// Ridgefire ground: the top is the theme's surface (sand, grass, regolith, ash, snow) with grain and a lighter crust;
// the cut face shows wavy strata, a darker band of bedrock below, and a fresh, darker scar where a blast bit. UV2.x is
// the column's surface height, so the crust follows the ground. Our own shader (CC BY-SA 4.0).
shader_type spatial;

uniform vec4 top_col : source_color = vec4(0.75, 0.55, 0.35, 1.0);
uniform vec4 soil_col : source_color = vec4(0.55, 0.35, 0.22, 1.0);
uniform vec4 strata_col : source_color = vec4(0.7, 0.45, 0.3, 1.0);
uniform vec4 deep_col : source_color = vec4(0.3, 0.22, 0.18, 1.0);

varying vec3 wpos;
varying vec3 wnrm;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) { float v = 0.0; float a = 0.5; for (int k = 0; k < 4; k++) { v += a * noise(p); p *= 2.03; a *= 0.5; } return v; }

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	float surface = UV2.x;
	float below = surface - wpos.y;
	vec3 col;
	float rough = 0.9;
	if (wnrm.y > 0.6) {
		// the top: grain, tufts and pebbles
		float g = fbm(wpos.xz * 1.7);
		col = top_col.rgb * (0.82 + 0.3 * g);
		col = mix(col, top_col.rgb * 1.2, smoothstep(0.75, 0.9, noise(wpos.xz * 9.0)) * 0.5);
		// steep slopes (crater walls) show the earth, not the surface
		vec3 earth = mix(soil_col.rgb, strata_col.rgb, 0.35) * (0.75 + 0.3 * fbm(wpos.xy * 0.8));
		col = mix(col, earth, smoothstep(0.92, 0.7, wnrm.y));
	} else {
		float wob = fbm(vec2(wpos.x * 0.08, wpos.y * 0.25)) * 3.0;
		float yy = wpos.y + wob;
		// broad, soft layers with a few fine dark seams; colour varies along them
		float band = smoothstep(0.2, 0.8, sin(yy * 0.9) * 0.5 + 0.5);
		float seam = smoothstep(0.93, 0.99, sin(yy * 3.1 + fbm(vec2(wpos.x * 0.2, yy)) * 2.0) * 0.5 + 0.5);
		float grain = fbm(vec2(wpos.x * 0.9, yy * 4.0));
		col = mix(soil_col.rgb, strata_col.rgb, band * 0.45);
		col *= 0.78 + 0.32 * grain;
		col *= 1.0 - seam * 0.3;
		col = mix(col, deep_col.rgb, smoothstep(4.0, -6.0, yy));
		// the crust under the surface, and pebbles in the face
		col = mix(col, top_col.rgb * 0.8, smoothstep(0.8, 0.2, below + noise(vec2(wpos.x * 3.0, 0.0)) * 0.35));
		col *= 1.0 - 0.3 * smoothstep(0.84, 0.96, noise(wpos.xy * 4.0));
		rough = 0.95;
	}
	ALBEDO = col;
	ROUGHNESS = rough;
}
