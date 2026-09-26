shader_type spatial;
// Distant towers, drawn by the shader from world position: either brick-and-stone blocks with punched windows (some
// lit warm or cool, whole floors brighter than others, a few with a blind down) or glass office towers with
// continuous floor bands, lit in strips. The facade catches a little of the city's glow near the ground.
instance uniform float seed = 0.0;
uniform vec3 wall : source_color = vec3(0.05, 0.045, 0.07);
uniform float lit_ratio = 0.3;
uniform vec2 cell = vec2(1.1, 1.5);
uniform float brightness = 1.0;
varying vec3 wpos;
varying vec3 wnrm;

float h21(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7)) + seed * 17.13) * 43758.5453);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	float side = step(abs(wnrm.z), abs(wnrm.x));
	float roof = step(0.5, abs(wnrm.y));
	float u = mix(wpos.x, wpos.z, side);
	float glass_tower = step(0.62, fract(seed * 0.618 + 0.13));
	vec2 c = cell * mix(1.0, 1.0 + 0.4 * fract(seed * 0.37), 1.0);
	vec2 g = vec2(u, wpos.y) / c;
	vec2 id = floor(g);
	vec2 f = fract(g);
	float floor_mood = h21(vec2(id.y * 0.37, 11.0 + side));
	vec3 warm = vec3(1.0, 0.68, 0.36);
	vec3 cool = vec3(0.6, 0.76, 1.0);
	vec3 alb;
	vec3 em;
	float rough;
	if (glass_tower > 0.5) {
		// office glass: dark blue panes, thin mullions, floors lit in long strips
		float mull = step(0.93, f.x) + step(0.9, f.y);
		float strip = floor(u / (c.x * 6.0));
		float lit = step(h21(vec2(strip, id.y) + side * 31.0), lit_ratio * (0.3 + 1.4 * floor_mood));
		alb = mix(vec3(0.02, 0.03, 0.05), wall * 1.4, clamp(mull, 0.0, 1.0));
		em = (1.0 - clamp(mull, 0.0, 1.0)) * lit * mix(cool, vec3(0.85, 0.9, 1.0), h21(vec2(strip, 3.0))) * (0.12 + 0.2 * h21(vec2(strip, id.y)));
		rough = mix(0.08, 0.6, clamp(mull, 0.0, 1.0));
	} else {
		float win = step(0.24, f.x) * step(f.x, 0.76) * step(0.3, f.y) * step(f.y, 0.8);
		float lit = step(h21(id + side * 91.0), lit_ratio * (0.4 + 1.2 * floor_mood));
		vec3 wc = mix(warm, cool, step(0.72, h21(id + 5.0)));
		wc = mix(wc, vec3(1.0, 0.35, 0.7), step(0.97, h21(id + 9.0)));
		float blind = step(0.7, h21(id + 13.0)) * step(f.y, 0.58);
		float slab = step(fract(g.y + 0.1), 0.1);
		alb = mix(wall + slab * 0.025, vec3(0.012, 0.015, 0.025), win);
		em = win * lit * (1.0 - blind * 0.75) * wc * (0.3 + 0.8 * h21(id + 3.0));
		rough = mix(0.85, 0.15, win);
	}
	// the city's glow washing up the lower floors
	alb += vec3(0.05, 0.02, 0.05) * exp(-max(wpos.y, 0.0) * 0.06);
	ALBEDO = mix(alb, wall * 0.7, roof);
	ROUGHNESS = rough;
	SPECULAR = 0.5;
	EMISSION = em * (1.0 - roof) * brightness;
}
