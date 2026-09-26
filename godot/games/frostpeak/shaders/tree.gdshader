shader_type spatial;
// Conifer needles with snow lying on the branches: white wherever the surface faces up (broken up by noise), dark
// green on the steep tips and undersides. Each tree gets its own shade of green from its position.

uniform vec3 needle : source_color = vec3(0.09, 0.24, 0.15);
uniform vec3 needle_b : source_color = vec3(0.16, 0.3, 0.15);
uniform vec3 snow : source_color = vec3(0.93, 0.95, 1.0);
uniform float snow_amount = 0.62;

varying vec3 wn;
varying vec3 lp;
varying float seed;

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
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	lp = VERTEX;
	seed = hash(vec3(MODEL_MATRIX[3].xz * 0.37, 1.7));
}

void fragment() {
	float n = noise(lp * 5.0) * 0.6 + noise(lp * 13.0) * 0.4;
	float s = smoothstep(0.5, 0.68, wn.y + (n - 0.5) * 0.45 + (snow_amount - 0.5) * 0.5 + (seed - 0.5) * 0.15);
	vec3 g = mix(needle, needle_b, seed) * (0.75 + 0.5 * n);
	ALBEDO = mix(g, snow * (0.92 + 0.08 * n), s);
	ROUGHNESS = mix(0.9, 0.65, s);
	SPECULAR = mix(0.2, 0.4, s);
}
