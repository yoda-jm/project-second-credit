shader_type spatial;
// Marble Drift: the course's top faces (our own design, CC BY-SA 4.0). Polished chequered tiles like a lacquered toy
// track: each 1-unit tile is a slightly domed pillow with a soft bevel, a dark groove and a thin glowing seam, under a
// glossy clear coat (the environment's sky gives the reflections). Steeper faces are a touch darker.
// Mesh contract (built by the view from the height field): UV = world x, z (1 unit per cell); COLOR.r = the cell's
// kind index in ".#_~G=^" order / 6 (give a cell's four vertices the same colour). Per kind:
//   .  floor: the chequer                     #  wall top: brushed metal trim with a glowing inset band
//   _  void: discarded (never drawn)          ~  acid: bubbling green glow
//   G  goal: a fine chequered finish with light rings and a chase of light along z
//   =  glass: icy translucent-looking floor with frozen veins inside and glints   ^  rough: studded rubber grip
// Everything animates on TIME (deterministic with a fixed frame rate). DriftSky.palette(theme) gives the colours.
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

#include "res://games/marbledrift/shaders/drift_noise.gdshaderinc"

uniform vec3 tile_a : source_color = vec3(0.93, 0.94, 0.97);   // the light squares
uniform vec3 tile_b : source_color = vec3(0.13, 0.40, 0.88);   // the coloured squares
uniform vec3 seam : source_color = vec3(0.45, 0.88, 1.0);      // the glowing seams between tiles
uniform vec3 accent : source_color = vec3(1.0, 0.72, 0.22);    // goal lights, wall trim band
uniform vec3 trim : source_color = vec3(0.78, 0.8, 0.86);      // wall tops (brushed metal)
uniform vec3 glass : source_color = vec3(0.5, 0.85, 1.0);
uniform vec3 acid : source_color = vec3(0.4, 1.0, 0.18);
uniform float seam_energy = 2.4;
uniform float gloss : hint_range(0.0, 1.0) = 0.1;              // tile roughness (lower = sharper reflections)
uniform float bevel : hint_range(0.02, 0.3) = 0.11;            // bevel width, in tile units
uniform float bevel_depth : hint_range(0.0, 0.08) = 0.028;     // how much the bevel tilts the normal
uniform float slope_shade : hint_range(0.0, 1.0) = 0.32;       // darkening of steep faces

varying flat int v_kind;
varying vec3 v_wpos;
varying vec3 v_wn;

void vertex() {
	v_kind = int(round(COLOR.r * 6.0));
	v_wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

// d/dx smoothstep(0, b, x)
float ss_d(float b, float x) {
	float t = clamp(x / b, 0.0, 1.0);
	return 6.0 * t * (1.0 - t) / b;
}

void fragment() {
	int k = v_kind;
	if (k == 2) {
		discard;
	}
	float t = TIME;
	vec2 p = UV;
	vec2 cell = floor(p);
	vec2 f = fract(p);
	vec2 e = min(f, 1.0 - f);
	float edge = min(e.x, e.y);
	float par = mod(cell.x + cell.y, 2.0);
	vec3 wn = normalize(v_wn);
	vec3 tx = normalize(vec3(1.0, 0.0, 0.0) - wn * wn.x);
	vec3 tz = normalize(vec3(0.0, 0.0, 1.0) - wn * wn.z);
	vec3 wv = normalize((INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz);   // towards the camera
	float px = max(fwidth(p.x), fwidth(p.y));                        // one pixel, in tile units
	float detail = 1.0 - smoothstep(0.04, 0.2, px);                  // fine detail fades when tiles are tiny

	// the pillow bevel: the height rises over `bevel` from each edge; its gradient tilts the normal outwards
	vec2 g = vec2(ss_d(bevel, e.x) * sign(0.5 - f.x), ss_d(bevel, e.y) * sign(0.5 - f.y)) * bevel_depth * detail;
	float groove = smoothstep(0.0, 0.03 + px, edge);                 // 0 in the groove between tiles
	float seam_line = 1.0 - smoothstep(0.004, 0.004 + px * 1.3, edge);
	float rim = 1.0 - smoothstep(0.0, bevel, edge);                  // over the bevel

	vec3 base = mix(tile_a, tile_b, par);
	base *= 0.95 + 0.05 * (f.x + f.y) * 0.5 + 0.03 * (md_hash(cell + 3.1) - 0.5);
	float rough = gloss;
	float metal = 0.0;
	float coat = 1.0;
	vec3 emit = vec3(0.0);
	vec3 seam_col = seam;
	float seam_e = seam_energy;
	vec2 bump = vec2(0.0);

	if (k == 1) {
		// wall top: brushed metal, a bright bevel and a glowing inset band
		float br = md_noise(vec2(p.x * 3.0, p.y * 140.0)) * 0.6 + md_noise(vec2(p.x * 9.0, p.y * 400.0)) * 0.4;
		base = trim * (0.8 + 0.25 * br);
		metal = 0.95;
		rough = 0.22 + 0.12 * br;
		coat = 0.3;
		float band = smoothstep(0.12, 0.13 + px, edge) * (1.0 - smoothstep(0.155, 0.165 + px, edge));
		emit += accent * band * 2.2 * detail;
		seam_col = accent;
		seam_e *= 0.7;
	} else if (k == 3) {
		// acid: dark lacquer over a churning green glow, bubbles that swell and pop
		vec2 q = p * 2.2 + vec2(0.0, -t * 0.12);
		float sw = md_fbm(p * 1.3 + vec2(t * 0.07, -t * 0.11), 3);
		vec2 c = md_cells(q + sw * 0.6);
		float life = fract(t * 0.35 + c.y * 7.0);
		float r = 0.12 + 0.32 * life;
		float shell = smoothstep(r - 0.07, r - 0.01, c.x) * (1.0 - smoothstep(r - 0.01, r + 0.015, c.x));
		float inside = 1.0 - smoothstep(r - 0.02, r, c.x);
		float pop = smoothstep(0.85, 1.0, life);
		base = vec3(0.01, 0.04, 0.01);
		rough = 0.05;
		coat = 1.0;
		emit = acid * (0.35 + 0.9 * sw * sw) + acid * shell * (1.6 - 1.4 * pop) + vec3(0.8, 1.0, 0.6) * inside * 0.08;
		bump = vec2(md_noise(q * 3.0 + t) - 0.5, md_noise(q * 3.0 - t + 5.0) - 0.5) * 0.25;
		seam_col = acid;
	} else if (k == 4) {
		// goal: a fine chequered finish, rings of light swelling from each tile and a chase along the course
		vec2 q = floor(p * 4.0);
		float c4 = mod(q.x + q.y, 2.0);
		base = mix(vec3(0.03, 0.03, 0.04), vec3(0.92, 0.92, 0.9), c4);
		rough = 0.08;
		float rr = length(f - 0.5);
		float ring = exp(-pow((rr - fract(t * 0.6) * 0.75) * 16.0, 2.0)) * (1.0 - fract(t * 0.6));
		float chase = pow(0.5 + 0.5 * sin((p.y - t * 4.0) * 1.1), 10.0);
		emit = accent * (ring * 2.4 + chase * 1.3 * (0.4 + 0.6 * c4) + 0.12);
		seam_col = accent;
		seam_e *= 1.3;
	} else if (k == 5) {
		// glass: nearly black so the reflections carry it, frozen veins seen through depth, glints that move
		vec2 depth_off = -wv.xz / max(wv.y, 0.25);
		vec2 p1 = p + depth_off * 0.18;
		vec2 p2 = p + depth_off * 0.42;
		float v1 = 1.0 - smoothstep(0.0, 0.035, abs(md_noise(p1 * 2.3) - 0.5));
		float v2 = 1.0 - smoothstep(0.0, 0.06, abs(md_noise(p2 * 1.4 + 7.0) - 0.5));
		float cloud = md_fbm(p2 * 0.9, 3);
		base = glass * 0.08;
		rough = 0.025;
		coat = 1.0;
		float fres = pow(1.0 - clamp(dot(wn, wv), 0.0, 1.0), 4.0);
		emit = glass * (0.1 + 0.35 * cloud * cloud + 0.7 * v1 * detail + 0.3 * v2 * detail + 0.5 * fres);
		vec2 sc = floor(p * 26.0);
		float h = md_hash(sc + floor(wv.xz * 9.0) * 17.0);
		float tw = 0.5 + 0.5 * sin(t * 4.0 + h * 60.0);
		vec2 so = fract(p * 26.0) - 0.5;
		float spark = step(0.965, h) * tw * (1.0 - smoothstep(0.0, 0.18, length(so)));
		emit += vec3(1.0) * spark * 6.0 * detail;
		seam_col = mix(glass, vec3(1.0), 0.4);
	} else if (k == 6) {
		// rough: studded rubber grip, four by four studs per tile
		vec2 s = fract(p * 4.0) - 0.5;
		float r = length(s);
		float stud = 1.0 - smoothstep(0.25, 0.3 + px * 4.0, r);
		float hgt = sqrt(max(0.09 - r * r, 0.0));
		bump = s / max(hgt, 0.08) * stud * 0.35 * detail;
		base = mix(base * vec3(0.55, 0.55, 0.6), base * 0.9 + 0.04, stud);
		rough = mix(0.65, 0.4, stud);
		coat = 0.0;
		groove *= mix(0.6, 1.0, smoothstep(0.2, 0.32, r));
		seam_e *= 0.6;
	} else {
		// floor: tiny paint flakes catch the light near the camera
		float fl = md_hash(floor(p * 60.0));
		emit += seam * step(0.992, fl) * 0.6 * detail * (0.5 + 0.5 * sin(t * 2.0 + fl * 80.0));
		emit += seam * rim * 0.06 * seam_e;
	}

	// slope: steeper faces a touch darker
	float slope = clamp((1.0 - wn.y) * 3.0, 0.0, 1.0);
	base *= 1.0 - slope_shade * slope;

	vec3 n = normalize(wn - tx * (g.x + bump.x) - tz * (g.y + bump.y));
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
	ALBEDO = base * mix(0.18, 1.0, groove);
	ROUGHNESS = mix(0.5, rough, groove);
	METALLIC = metal;
	SPECULAR = 0.6;
	CLEARCOAT = coat * groove;
	CLEARCOAT_ROUGHNESS = 0.04;
	AO = mix(0.35, 1.0, groove);
	AO_LIGHT_AFFECT = 0.3;
	EMISSION = emit + seam_col * seam_line * seam_e * mix(0.35, 1.0, detail);
}
