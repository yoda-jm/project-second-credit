shader_type spatial;
// A beach ball: six panels of colour round the axis, white caps at both poles, glossy vinyl.

uniform vec4 c0 : source_color = vec4(1.0, 0.25, 0.25, 1.0);
uniform vec4 c1 : source_color = vec4(1.0, 0.85, 0.2, 1.0);
uniform vec4 c2 : source_color = vec4(0.2, 0.55, 1.0, 1.0);

varying vec3 lp;

void vertex() {
	lp = VERTEX;
}

void fragment() {
	vec3 n = normalize(lp);
	float a = atan(n.z, n.x) / 6.2831853 + 0.5;
	int seg = int(floor(a * 6.0)) % 3;
	vec3 c = seg == 0 ? c0.rgb : (seg == 1 ? c1.rgb : c2.rgb);
	if (int(floor(a * 6.0)) % 2 == 1) { c = vec3(0.97); }
	float cap = smoothstep(0.86, 0.9, abs(n.y));
	c = mix(c, vec3(0.97), cap);
	ALBEDO = c;
	ROUGHNESS = 0.22;
	SPECULAR = 0.7;
	CLEARCOAT = 0.6;
}
