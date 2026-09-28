// Jelly Spike sand: vertex-coloured (the ripples, the wet band and the footprints are painted by
// tools/blender/jellyspike_beach.py), with a fine grain in the normals, wet sand glossy, and a few sparkling grains
// in the sun near the camera.
shader_type spatial;

uniform float sparkle = 1.0;
uniform float grain = 1.0;
uniform vec3 tint : source_color = vec3(1.0);

varying vec3 wpos;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 c = COLOR.rgb * tint;
	float cam_d = length(wpos - CAMERA_POSITION_WORLD);
	float near = smoothstep(40.0, 12.0, cam_d);
	float lum = dot(COLOR.rgb, vec3(0.3, 0.59, 0.11));
	// grain: speckles of lighter and darker sand
	float sp = vnoise(wpos.xz * 22.0) * 0.6 + vnoise(wpos.xz * 57.0) * 0.4;
	c *= 1.0 + (sp - 0.5) * 0.16 * grain * near;
	float e = 0.02;
	float h0 = vnoise(wpos.xz * 9.0), hx = vnoise(wpos.xz * 9.0 + vec2(e * 9.0, 0.0)), hz = vnoise(wpos.xz * 9.0 + vec2(0.0, e * 9.0));
	vec3 nw = normalize(vec3(-(hx - h0) * 0.6 * grain * near, 1.0, -(hz - h0) * 0.6 * grain * near));
	NORMAL = normalize(mix(NORMAL, (VIEW_MATRIX * vec4(nw, 0.0)).xyz, 0.5));
	ALBEDO = c;
	float wetness = smoothstep(0.42, 0.22, lum);
	ROUGHNESS = mix(0.93, 0.35, wetness);
	SPECULAR = mix(0.3, 0.6, wetness);
	// glints: a few grains catch the light and wink
	vec2 cell = floor(wpos.xz * 45.0);
	float h = hash(cell);
	float on = step(0.985, h) * (0.5 + 0.5 * sin(TIME * (1.0 + h * 3.0) + h * 80.0));
	vec2 f = fract(wpos.xz * 45.0) - 0.5;
	float dotm = smoothstep(0.35, 0.0, length(f));
	EMISSION = vec3(1.0, 0.97, 0.9) * on * dotm * sparkle * near * (1.0 - wetness) * 1.6;
}
