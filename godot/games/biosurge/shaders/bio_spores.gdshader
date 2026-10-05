// Biosurge: spores, plankton, dust or embers drifting in the abyss (a MultiMesh of quads, billboarded here).
// INSTANCE_CUSTOM: x phase, y speed, z size, w colour mix. The particles live in a box and wrap round its height.
// Our own code, CC BY-SA 4.0.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, skip_vertex_transform, fog_disabled;

uniform vec3 color_a : source_color = vec3(0.6, 1.0, 0.6);
uniform vec3 color_b : source_color = vec3(0.3, 0.9, 1.0);
uniform float energy = 1.5;
uniform float size = 0.12;
uniform float rise = 0.3;
uniform float wander = 0.6;
uniform float box_bottom = -16.0;
uniform float box_height = 15.0;
uniform float clock = 0.0;

varying float fade;
varying float mixv;

void vertex() {
	vec3 c = MODEL_MATRIX[3].xyz;
	float ph = INSTANCE_CUSTOM.x;
	float t = clock * INSTANCE_CUSTOM.y + ph * 50.0;
	float h = mod(c.y - box_bottom + t * rise, box_height);
	c.y = box_bottom + h;
	c.x += sin(t * 0.7 + ph * 20.0) * wander;
	c.z += cos(t * 0.53 + ph * 13.0) * wander;
	fade = smoothstep(0.0, 2.0, h) * smoothstep(box_height, box_height - 3.0, h);
	fade *= 0.65 + 0.35 * sin(clock * 3.0 + ph * 40.0);
	mixv = INSTANCE_CUSTOM.w;
	vec3 vc = (VIEW_MATRIX * vec4(c, 1.0)).xyz;
	float s = size * (0.5 + INSTANCE_CUSTOM.z);
	VERTEX = vc + vec3(VERTEX.xy * s, 0.0);
}

void fragment() {
	float d = length(UV - 0.5) * 2.0;
	float a = pow(max(1.0 - d, 0.0), 2.2) * fade;
	ALBEDO = mix(color_a, color_b, mixv) * a * energy;
}
