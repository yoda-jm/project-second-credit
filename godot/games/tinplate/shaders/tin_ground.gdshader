// Tinplate Turbo board ground: the theme's texture with broad two-tone patches, an optional mown stripe, worn paths
// and a darker rim towards the board's edge. Our own shader (CC BY-SA 4.0); the textures are the shared CC0 ones.
shader_type spatial;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform vec4 patch_col : source_color = vec4(0.8, 0.9, 0.5, 1.0);
uniform float patch_amount = 0.35;
uniform float stripes = 0.0;
uniform float tex_scale = 0.12;
uniform float plain = 0.0;          // 1: no texture colour (snow)
uniform vec2 board_min = vec2(-9.0, -6.5);
uniform vec2 board_max = vec2(57.0, 34.5);

varying vec3 wpos;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

void fragment() {
	vec2 uv = wpos.xz * tex_scale;
	vec3 base = mix(texture(albedo_tex, uv).rgb, vec3(1.0), plain) * tint.rgb;
	float n = noise(wpos.xz * 0.09) * 0.65 + noise(wpos.xz * 0.27) * 0.35;
	base = mix(base, base * patch_col.rgb * 1.3, smoothstep(0.45, 0.7, n) * patch_amount);
	base *= 1.0 + stripes * 0.07 * (step(0.5, fract(wpos.x * 0.25)) * 2.0 - 1.0);
	// darker towards the board's rim
	vec2 e = min(wpos.xz - board_min, board_max - wpos.xz);
	base *= mix(0.78, 1.0, smoothstep(0.0, 4.0, min(e.x, e.y)));
	ALBEDO = base;
	NORMAL_MAP = texture(normal_tex, uv).rgb;
	ROUGHNESS = mix(0.9, 0.75, plain);
}
