// Biosurge: the living cavern walls and islands (view3d/bio_world.gd builds the meshes). UV.x runs along the wall
// (metres), UV.y along its cross-section from the deadly edge (0 at the play plane, + up and over the crown,
// - down into the abyss). One pattern per theme: 0 tissue and veins, 1 coral pores, 2 crystal-plated chitin,
// 3 a molten crust, 4 heart membranes. The rim along the edge glows so the channel reads at a glance.
// Our own code, CC BY-SA 4.0.
shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;

#include "res://games/biosurge/shaders/bio_noise.gdshaderinc"

uniform vec3 deep_color : source_color = vec3(0.02, 0.08, 0.06);
uniform vec3 base_color : source_color = vec3(0.12, 0.4, 0.33);
uniform vec3 top_color : source_color = vec3(0.3, 0.6, 0.48);
uniform vec3 seam_color : source_color = vec3(0.03, 0.12, 0.1);
uniform vec3 vein_color : source_color = vec3(0.4, 1.0, 0.65);
uniform vec3 rim_color : source_color = vec3(0.65, 1.0, 0.4);
uniform float vein_energy = 2.0;
uniform float rim_energy = 3.0;
uniform float roughness_v = 0.4;
uniform float pattern = 0.0;
uniform float scale = 1.0;
uniform float clock = 0.0;
uniform float pulse_rate = 0.5;
uniform float heart = 0.0;
uniform float breathe = 0.1;
uniform float flow = 0.0;

varying vec3 wpos;
varying float lump;

void vertex() {
	float arc = UV.y;
	float m = smoothstep(0.8, 2.6, arc) + 0.6 * smoothstep(-1.5, -4.0, arc);
	float n = bio_vnoise(UV * vec2(0.18, 0.3));
	float b = bio_beat(clock * pulse_rate - UV.x * 0.035, heart);
	VERTEX += NORMAL * breathe * m * (b - 0.35) * (0.5 + n);
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	lump = n;
}

void fragment() {
	vec2 p = UV * scale;
	float arc = UV.y;
	float big = bio_fbm(p * vec2(0.22, 0.3) + 11.0);
	float hgt = smoothstep(0.8, 4.2, wpos.y + (big - 0.5) * 2.0);
	vec3 alb = mix(base_color, top_color, hgt);
	alb *= 0.72 + 0.56 * big;
	float rough = roughness_v;
	vec3 emit = vec3(0.0);
	float t = clock;
	float b = bio_beat(t * pulse_rate - UV.x * 0.06, heart);
	vec3 nm = vec3(0.5, 0.5, 1.0);

	if (pattern < 0.5) {
		// tissue: wet cells and a net of glowing veins
		vec3 v = bio_voro(p * vec2(1.2, 1.5));
		alb = mix(seam_color, alb, smoothstep(0.0, 0.16, v.y));
		alb *= 0.85 + 0.3 * v.z;
		vec2 dn = vec2(bio_vnoise(p * 1.6), bio_vnoise(p * 1.6 + 5.2)) - 0.5;
		nm = vec3(0.5 + dn * 0.5, 1.0);
		float n1 = bio_fbm(p * vec2(0.32, 0.45) + vec2(0.0, 7.0));
		float n2 = bio_fbm(p * vec2(0.9, 1.2) + vec2(3.0, 1.0));
		float vein = (1.0 - smoothstep(0.0, 0.02, abs(n1 - 0.5))) + 0.45 * (1.0 - smoothstep(0.0, 0.012, abs(n2 - 0.5)));
		alb = mix(alb, vein_color * 0.35, clamp(vein, 0.0, 1.0) * 0.6);
		emit += vein_color * vein * vein_energy * (0.3 + 0.7 * b);
		emit += vein_color * smoothstep(0.1, 0.0, v.x) * step(0.82, v.z) * vein_energy * 0.6 * (0.5 + 0.5 * b);
	} else if (pattern < 1.5) {
		// coral: pores in a porous reef skeleton, brain grooves, some pores lit
		vec3 v = bio_voro(p * vec2(2.0, 2.4));
		float pore = smoothstep(0.34, 0.16, v.x);
		float groove = 0.5 + 0.5 * sin(bio_fbm(p * 0.5) * 38.0);
		alb *= 0.75 + 0.35 * groove;
		alb = mix(alb, seam_color, pore * 0.85);
		nm = vec3(0.5 + (groove - 0.5) * 0.25, 0.5, 1.0);
		float lit = step(0.6, v.z) * (0.45 + 0.55 * sin(t * 1.7 + v.z * 40.0));
		emit += vein_color * smoothstep(0.16, 0.02, v.x) * max(lit, 0.0) * vein_energy;
		float n1 = bio_fbm(p * vec2(0.25, 0.35) + 3.0);
		emit += vein_color * (1.0 - smoothstep(0.0, 0.025, abs(n1 - 0.5))) * vein_energy * 0.35 * (0.5 + 0.5 * b);
		// caustics from the water above, rippling over the crowns
		vec3 c1 = bio_voro(wpos.xz * 0.32 + vec2(t * 0.12, t * 0.07));
		vec3 c2 = bio_voro(wpos.xz * 0.45 - vec2(t * 0.09, -t * 0.11) + 3.0);
		float caus = (1.0 - smoothstep(0.0, 0.12, c1.y)) * (0.5 + 0.5 * (1.0 - smoothstep(0.0, 0.16, c2.y)));
		emit += vec3(0.55, 0.85, 1.0) * caus * 0.55 * smoothstep(0.5, 3.0, wpos.y);
	} else if (pattern < 2.5) {
		// crystal: chitin plates with dark seams, each plate a facet, amber light in the seams
		vec3 v = bio_voro(p * vec2(0.85, 1.0));
		float seam = 1.0 - smoothstep(0.0, 0.08, v.y);
		alb *= 0.8 + 0.4 * v.z;
		alb = mix(alb, seam_color, seam);
		vec2 tilt = bio_h2(vec2(v.z * 91.0, v.z * 17.0)) - 0.5;
		nm = vec3(0.5 + tilt * 0.25, 1.0);
		rough = mix(roughness_v, 0.3, step(0.5, v.z));
		float zone = smoothstep(0.45, 0.7, bio_fbm(p * 0.25 + vec2(t * 0.04, 0.0)));
		emit += vein_color * seam * vein_energy * (0.25 + zone * (0.6 + 0.4 * b));
		float spark = smoothstep(0.985, 1.0, bio_h1(floor(p * 7.0) + floor(t * 3.0)));
		emit += vec3(1.0, 0.95, 0.85) * spark * 1.5 * step(0.5, v.z);
	} else if (pattern < 3.5) {
		// furnace: a charred crust broken by molten cracks, the heat flowing and welling up from below
		vec3 v = bio_voro(p * vec2(0.8, 0.95));
		float crack = 1.0 - smoothstep(0.0, 0.1, v.y);
		float heat = bio_fbm(p * 0.4 + vec2(t * flow, -t * flow * 0.6));
		alb *= 0.6 + 0.6 * v.z;
		alb = mix(alb, seam_color, crack);
		vec2 dn = vec2(bio_vnoise(p * 2.2), bio_vnoise(p * 2.2 + 3.0)) - 0.5;
		nm = vec3(0.5 + dn * 0.6, 1.0);
		float below = smoothstep(0.0, -10.0, wpos.y);
		float hot = smoothstep(0.35, 0.75, heat);
		emit += vein_color * crack * vein_energy * (0.08 + 2.2 * hot * hot + below) * (0.75 + 0.25 * b);
		alb *= 1.0 - 0.35 * hot;
		emit += vein_color * 0.25 * smoothstep(0.55, 0.0, v.x) * heat * below * vein_energy;
	} else {
		// heart: glossy membranes stretched over a branching net of veins, beating
		float n1 = bio_fbm(p * vec2(0.3, 0.4) + 2.0);
		float n2 = bio_fbm(p * vec2(0.8, 1.0) + 9.0);
		float vein = (1.0 - smoothstep(0.0, 0.05, abs(n1 - 0.5))) + 0.6 * (1.0 - smoothstep(0.0, 0.025, abs(n2 - 0.5)));
		vein = clamp(vein, 0.0, 1.2);
		float fold = bio_fbm(p * vec2(0.6, 0.25));
		alb *= 0.7 + 0.6 * fold;
		alb = mix(alb, seam_color, vein * 0.5);
		nm = vec3(0.5 + (fold - 0.5) * 0.6, 0.5 + (n1 - 0.5) * 0.4, 1.0);
		rough = roughness_v;
		emit += vein_color * vein * vein_energy * (0.2 + 0.9 * b);
		emit += base_color * 0.25 * b * (1.0 - hgt * 0.5);
	}

	// the deep: darker and cooler as the wall falls into the abyss
	float depth = smoothstep(-16.0, -0.5, wpos.y);
	alb = mix(deep_color, alb, depth * 0.85 + 0.15);
	emit *= 0.35 + 0.65 * depth;

	// the deadly edge: a hot line right at the play plane and a softer glow up the shoulder
	float line = exp(-pow((arc - 0.12) / 0.16, 2.0));
	float band = exp(-pow((arc - 0.7) / 0.75, 2.0));
	float flick = 0.85 + 0.15 * bio_beat(t * pulse_rate * 1.5 - UV.x * 0.1, heart);
	emit += rim_color * rim_energy * (line + 0.3 * band * COLOR.g) * flick;
	alb = mix(alb, rim_color * 0.6, line * 0.5);

	// a wet sheen on the crowns facing the view
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	emit += top_color * fres * 0.1 * depth;

	ALBEDO = alb * COLOR.r;
	AO = COLOR.r;
	AO_LIGHT_AFFECT = 0.6;
	ROUGHNESS = rough;
	SPECULAR = 0.55;
	NORMAL_MAP = nm;
	NORMAL_MAP_DEPTH = 1.0;
	EMISSION = emit;
}
