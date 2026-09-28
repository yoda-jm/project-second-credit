shader_type spatial;
// The bobsled channel's ice: sprayed white-blue ice, glossy and hard, clearer and bluer where it is thick at the foot
// of the walls, milky in patches where it was re-sprayed; the runners' grooves polished along the floor and swept
// up the banks, and fine scratches along the run that dull the shine. UV: x across (metres from the centre along
// the surface, + right), y along the run (metres). COLOR.r: 1 on the floor, 0 up the walls.

uniform vec3 tint : source_color = vec3(0.84, 0.91, 0.98);
uniform vec3 deep : source_color = vec3(0.55, 0.72, 0.9);
uniform vec3 milk : source_color = vec3(0.96, 0.98, 1.0);

varying vec3 wpos;
varying float floorw;

float hash2(vec2 q) {
	vec2 p = fract(q * vec2(0.3183099, 0.3678794) + 0.1) * 17.0;
	return fract(p.x * p.y * (p.x + p.y));
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash2(i), hash2(i + vec2(1, 0)), f.x), mix(hash2(i + vec2(0, 1)), hash2(i + vec2(1, 1)), f.x), f.y);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	floorw = COLOR.r;
}

void fragment() {
	float u = UV.x;
	float v = UV.y;
	float cloud = vnoise(vec2(u * 0.8, v * 0.12)) * 0.6 + vnoise(vec2(u * 3.0, v * 0.5)) * 0.4;
	// streaks along the run: long, thin, a little wavy
	float st = vnoise(vec2(u * 38.0 + sin(v * 0.05) * 3.0, v * 0.04));
	float streak = smoothstep(0.62, 0.9, st) * 0.6;
	// the runners' grooves: two polished lanes 0.67 m apart on the floor, fanning out as they climb the walls
	float lane = abs(abs(u) - 0.335 - (1.0 - floorw) * 0.4 * sin(v * 0.07 + u));
	float groove = smoothstep(0.09, 0.0, lane) * (0.55 + 0.45 * floorw);
	vec3 col = mix(tint, milk, smoothstep(0.35, 0.85, cloud) * 0.55);
	col = mix(col, deep, (1.0 - smoothstep(0.0, 0.6, abs(abs(u) - 0.9))) * 0.25 * floorw);  // thick ice at the walls' foot
	col = mix(col, deep * 1.05, groove * 0.3);
	col = mix(col, milk, streak * 0.5);
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	ALBEDO = col;
	METALLIC = 0.0;
	SPECULAR = 0.5 + 0.3 * fres;
	ROUGHNESS = clamp(0.1 + 0.12 * cloud + 0.3 * streak - 0.08 * groove, 0.03, 1.0);
	CLEARCOAT = 1.0;
	CLEARCOAT_ROUGHNESS = 0.03 + 0.25 * streak;
	// fine bumps across the spray
	NORMAL_MAP = vec3(0.5 + (vnoise(vec2(u * 9.0, v * 2.0)) - 0.5) * 0.08, 0.5 + (vnoise(vec2(u * 7.0 + 3.0, v * 1.7)) - 0.5) * 0.08, 1.0);
}
