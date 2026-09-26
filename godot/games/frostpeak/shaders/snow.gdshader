shader_type spatial;
// Snow: a soft white with a blue tint where it faces away from the light, a gentle bumpy normal, and tiny glints
// that sparkle as the camera moves. World-space, so any mesh can wear it.

uniform vec3 tint : source_color = vec3(0.95, 0.97, 1.0);
uniform vec3 shade : source_color = vec3(0.82, 0.86, 0.94);
uniform float bump_scale = 0.35;
uniform float sparkle = 1.0;
uniform sampler2D mark_tex : source_color, hint_default_white;  // optional markings (lines), world XZ
uniform vec4 mark_rect = vec4(0.0, 0.0, 0.0, 0.0);              // x0, z0, width, depth of the markings

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

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnorm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	float n = noise(wpos * 1.3) * 0.6 + noise(wpos * 4.1) * 0.3 + noise(wpos * 11.0) * 0.1;
	vec3 col = mix(shade, tint, 0.75 + 0.25 * n);
	float painted = 0.0;
	if (mark_rect.z != 0.0) {
		vec2 uv = (wpos.xz - mark_rect.xy) / mark_rect.zw;
		if (uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0) {
			vec4 m = texture(mark_tex, uv);
			// paint soaked into the snow: grainy edges, lighter where the snow sparkles through
			float grain = noise(wpos * 9.0) * 0.5 + noise(wpos * 27.0) * 0.5;
			painted = m.a * smoothstep(0.15, 0.45, grain + m.a * 0.6 - 0.35);
			col = mix(col, m.rgb * (0.85 + 0.25 * n), painted);
		}
	}
	ALBEDO = col;
	ROUGHNESS = 0.75;
	SPECULAR = 0.35;
	// bumps from the noise gradient
	float e = 0.05;
	float nx = noise((wpos + vec3(e, 0, 0)) * 1.3) - noise(wpos * 1.3);
	float nz = noise((wpos + vec3(0, 0, e)) * 1.3) - noise(wpos * 1.3);
	vec3 bn = normalize(wnorm - vec3(nx, 0.0, nz) * bump_scale * 8.0);
	NORMAL = normalize((VIEW_MATRIX * vec4(bn, 0.0)).xyz);
	// glints: tiny facets that catch the light from some angles only
	vec3 cell = floor(wpos * 60.0);
	float h = hash(cell);
	vec3 view_w = (INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz;
	float g = step(0.992, h) * step(0.7, fract(h * 97.0 + dot(view_w, vec3(3.1, 5.7, 2.3))));
	EMISSION = vec3(1.0, 0.98, 0.92) * g * sparkle * 1.6 * (1.0 - painted);
}
