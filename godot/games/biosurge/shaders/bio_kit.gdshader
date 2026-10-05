// Biosurge: the world kit's materials (art/world/*.glb), one ShaderMaterial per role and theme. MultiMesh
// instances carry INSTANCE_CUSTOM: x phase, y sway, z glow, w tint. `kind`: 0 flesh/shell/metal, 1 glow,
// 2 egg (lit from inside), 3 crystal. Our own code, CC BY-SA 4.0.
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

uniform vec3 albedo : source_color = vec3(0.5);
uniform vec3 albedo_b : source_color = vec3(0.5);
uniform vec3 glow_color : source_color = vec3(1.0);
uniform float glow_energy = 3.0;
uniform float roughness_v = 0.45;
uniform float metallic_v = 0.0;
uniform float kind = 0.0;
uniform float clock = 0.0;
uniform float pulse_rate = 0.5;

varying float ph;
varying float glowv;
varying float tint;
varying float wy;

void vertex() {
	ph = INSTANCE_CUSTOM.x;
	glowv = INSTANCE_CUSTOM.z;
	tint = INSTANCE_CUSTOM.w;
	float h = max(VERTEX.y, 0.0);
	float s = INSTANCE_CUSTOM.y * h * h;
	float a = clock * 1.1 + ph * 6.2831;
	VERTEX.x += s * (sin(a) * 0.6 + sin(a * 2.3 + 1.0) * 0.25);
	VERTEX.z += s * (cos(a * 0.8 + 2.0) * 0.5);
	wy = (MODEL_MATRIX * vec4(VERTEX, 1.0)).y;
}

void fragment() {
	vec3 alb = mix(albedo, albedo_b, tint);
	float depth = smoothstep(-15.0, -1.0, wy);
	depth *= depth;
	float pulse = 0.6 + 0.4 * sin(clock * pulse_rate * 6.2831 + ph * 6.2831);
	float fres = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	vec3 emit = vec3(0.0);
	if (kind > 0.5 && kind < 1.5) {
		emit = glow_color * glow_energy * glowv * pulse;
		alb = glow_color;
	} else if (kind > 1.5 && kind < 2.5) {
		emit = glow_color * glow_energy * 0.35 * glowv * (pow(1.0 - fres, 2.0) * 0.8 + 0.2) * pulse;
		emit += alb * fres * fres * 0.6;
	} else if (kind > 2.5) {
		emit = glow_color * glow_energy * 0.12 * glowv * (0.3 + fres) * pulse;
	}
	ALBEDO = alb * (0.12 + 0.88 * depth);
	ROUGHNESS = roughness_v;
	METALLIC = metallic_v;
	EMISSION = emit * (0.35 + 0.65 * depth);
}
