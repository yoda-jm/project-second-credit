shader_type spatial;
// Tumbletop cube sides: a soft bevel lit along every edge, a faint stone grain and a gradient that darkens towards
// the bottom of the cube, so the pyramid reads as a stack of polished blocks.

uniform vec4 side_color : source_color = vec4(0.4, 0.45, 0.6, 1.0);
uniform vec4 edge_color : source_color = vec4(1.0, 0.95, 0.85, 1.0);
uniform float edge_glow = 0.35;

varying vec3 lp;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

void vertex() {
	lp = VERTEX;
}

void fragment() {
	vec3 a = abs(lp) * 2.0;           // 0 at the centre, 1 on the faces
	// distance to the nearest edge: the second-largest axis
	float m1 = max(a.x, max(a.y, a.z));
	float m2 = a.x + a.y + a.z - m1 - min(a.x, min(a.y, a.z));
	float edge = smoothstep(0.86, 0.985, m2);
	float grain = hash(floor(lp * 40.0)) * 0.06;
	float shade = mix(0.72, 1.0, smoothstep(-0.5, 0.5, lp.y));
	vec3 c = side_color.rgb * shade * (0.97 + grain);
	ALBEDO = mix(c, edge_color.rgb, edge * 0.3);
	EMISSION = edge_color.rgb * edge * edge_glow;
	ROUGHNESS = mix(0.45, 0.2, edge);
	METALLIC = 0.05;
}
