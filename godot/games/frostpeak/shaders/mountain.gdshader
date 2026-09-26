shader_type spatial;
// Mountains: bare rock on the steep faces and cliffs, snow on the ledges and gentler slopes, more snow higher up.
// The rock is the shared CC0 rock texture mapped from three sides in world space.

uniform sampler2D rock_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rock_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec3 rock_tint : source_color = vec3(0.7, 0.74, 0.86);
uniform vec3 snow : source_color = vec3(0.95, 0.97, 1.0);
uniform vec3 snow_shade : source_color = vec3(0.7, 0.76, 0.9);
uniform float scale = 0.012;
uniform float snow_line = 0.0;

varying vec3 wpos;
varying vec3 wnorm;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}

vec3 tri(sampler2D t, vec3 p, vec3 w) {
	return texture(t, p.zy).rgb * w.x + texture(t, p.xz).rgb * w.y + texture(t, p.xy).rgb * w.z;
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnorm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 w = pow(abs(wnorm), vec3(4.0));
	w /= (w.x + w.y + w.z);
	vec3 p = wpos * scale;
	vec3 rock = tri(rock_tex, p, w) * 0.6 + tri(rock_tex, p * 5.3, w) * 0.4;
	float n = noise(wpos * 0.02) * 0.55 + noise(wpos * 0.09) * 0.3 + noise(wpos * 0.4) * 0.15;
	// strata: faint horizontal bands in the rock; gullies: streaks running down the slopes
	float strata = 0.85 + 0.15 * sin(wpos.y * 0.35 + n * 6.0);
	float gully = noise(vec3(wpos.x * 0.045, wpos.y * 0.003, wpos.z * 0.045)) * 0.7 + noise(wpos * 0.15) * 0.3;
	vec3 rock_col = rock * rock_tint * strata * 2.2;
	float up = wnorm.y + (n - 0.5) * 0.15 + (gully - 0.5) * 0.55 + clamp((wpos.y - 150.0) / 500.0, 0.0, 0.2) + snow_line;
	float s = smoothstep(0.7, 0.8, up);
	vec3 snow_col = mix(snow_shade, snow, 0.55 + 0.45 * n);
	ALBEDO = mix(rock_col, snow_col, s);
	ROUGHNESS = mix(0.95, 0.8, s);
	SPECULAR = mix(0.25, 0.35, s);
	vec3 rn = tri(rock_nrm, p * 5.3, w) * 2.0 - 1.0;
	vec3 bn = normalize(wnorm + vec3(rn.x, 0.0, rn.y) * (1.0 - s) * 0.6);
	NORMAL = normalize((VIEW_MATRIX * vec4(bn, 0.0)).xyz);
}
