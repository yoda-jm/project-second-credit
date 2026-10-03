shader_type spatial;
// Marble Drift: the course's side faces: the edges of the floating slab and the flanks of walls (our own design,
// CC BY-SA 4.0). Dark lacquered metal panels with bevelled joints and rivets, thin light seams glowing in the joints
// (a slow pulse runs along them), a soft sheen; lower down, the faces fade into the abyss colour.
// Mesh contract: UV.x runs along the edge (world units; only its direction is used), UV.y = height. The panel rows and light seams follow the world
// height, so every face of the course lines up like one layered block. Uniform names match DriftSky.palette() keys
// (side, seam, abyss): the view can copy the palette straight in. fade_top / fade_bottom: world heights.
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

#include "res://games/marbledrift/shaders/drift_noise.gdshaderinc"

uniform vec3 side : source_color = vec3(0.13, 0.16, 0.26);     // panel colour
uniform vec3 seam : source_color = vec3(0.45, 0.88, 1.0);      // the light seams
uniform vec3 abyss : source_color = vec3(0.04, 0.05, 0.1);     // what the faces fade into lower down
uniform float seam_energy = 2.2;
uniform float row_h = 0.8;           // panel height (world units); a light seam every second joint
uniform float panel_w = 1.0;         // panel width along the edge
uniform float fade_top = -2.0;       // world height where the fade into the abyss begins
uniform float fade_bottom = -14.0;   // and where it is complete

varying vec3 v_wpos;
varying vec3 v_wn;

void vertex() {
	v_wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

float ss_d(float b, float x) {
	float t = clamp(x / b, 0.0, 1.0);
	return 6.0 * t * (1.0 - t) / b;
}

void fragment() {
	float t = TIME;
	vec3 wn = normalize(v_wn);
	float u = UV.x;
	float y = v_wpos.y;
	// the world direction in which u grows (its sign from the screen derivatives)
	vec3 th = normalize(cross(vec3(0.0, 1.0, 0.0), wn) + vec3(1e-5, 0.0, 0.0));
	float su = dot(th, dFdx(v_wpos)) * dFdx(u) + dot(th, dFdy(v_wpos)) * dFdy(u);
	th *= su < 0.0 ? -1.0 : 1.0;
	vec3 tv = vec3(0.0, 1.0, 0.0);
	u = dot(v_wpos, th);   // continuous along the course's edges (the mesh's UV.x restarts per edge)

	float px = max(fwidth(u), fwidth(y));
	float detail = 1.0 - smoothstep(0.03, 0.15, px);

	float row = floor(y / row_h);
	vec2 cell = vec2(floor(u / panel_w), row);
	vec2 f = vec2(fract(u / panel_w), fract(y / row_h));
	vec2 e = min(f, 1.0 - f) * vec2(panel_w, row_h);
	float edge = min(e.x, e.y);
	float groove = smoothstep(0.0, 0.02 + px, edge);
	vec2 g = vec2(ss_d(0.07, e.x) * sign(0.5 - f.x), ss_d(0.07, e.y) * sign(0.5 - f.y)) * 0.025 * detail;
	float ph = md_hash(cell + 11.0);
	vec3 base = side * (0.85 + 0.3 * ph);
	// a soft vertical sheen band across each panel and a faint brushing
	base *= 0.9 + 0.12 * sin(f.x * 3.14159) + 0.06 * md_noise(vec2(u * 24.0, y * 0.7));
	// rivets near the panel corners
	vec2 cd = min(f, 1.0 - f) * vec2(panel_w, row_h);
	float rivet = 1.0 - smoothstep(0.02, 0.028 + px, length(cd - 0.075));
	base = mix(base, side * 2.5 + 0.06, rivet * detail);

	// light seams in every second horizontal joint
	float sy = y / (row_h * 2.0);
	float d = abs(fract(sy + 0.5) - 0.5) * row_h * 2.0;     // distance to the nearest seam
	float core = 1.0 - smoothstep(0.012, 0.012 + px * 1.5, d);
	float halo = exp(-d * 14.0);
	float run = pow(0.5 + 0.5 * sin(u * 0.45 - t * 1.8 + floor(sy + 0.5) * 2.1), 8.0);
	float lit = 0.5 + 0.5 * run;

	float fade = smoothstep(fade_top, fade_bottom, y);
	vec3 col = mix(base, abyss, fade);

	vec3 n = normalize(wn - th * g.x - tv * g.y);
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
	ALBEDO = col * mix(0.2, 1.0, groove);
	METALLIC = mix(0.6, 0.1, fade);
	ROUGHNESS = mix(0.28 + 0.12 * ph, 0.9, fade);
	SPECULAR = 0.5;
	CLEARCOAT = 0.6 * (1.0 - fade);
	CLEARCOAT_ROUGHNESS = 0.08;
	AO = mix(0.35, 1.0, groove);
	EMISSION = seam * (core + halo * 0.15) * seam_energy * lit * (1.0 - fade * 0.8) + abyss * fade * 0.5;
}
