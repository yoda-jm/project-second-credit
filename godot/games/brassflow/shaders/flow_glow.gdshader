shader_type spatial;
// The glow running through a pipe: a tube whose UV.x runs 0..1 along the pipe; the part past `fill` is not drawn.
// Bright pulses travel with the flow and the front burns hottest. Our own shader (CC BY-SA 4.0).
render_mode cull_disabled;

instance uniform float fill = 0.0;
instance uniform float reverse = 0.0;   // 1: the glow comes in from the U = 1 end
uniform vec4 colour : source_color = vec4(0.3, 1.0, 0.7, 1.0);
uniform float energy = 1.6;
uniform float speed = 1.0;

void fragment() {
	float u = mix(UV.x, 1.0 - UV.x, reverse);
	if (fill <= 0.0 || u > fill) {
		discard;
	}
	float pulse = 0.5 + 0.5 * sin(u * 18.0 - TIME * 7.0 * speed + UV.y * 6.2832 * 2.0);
	float front = smoothstep(fill - 0.12, fill, u);
	ALBEDO = colour.rgb * 0.25;
	ROUGHNESS = 0.2;
	EMISSION = colour.rgb * energy * (0.75 + 0.45 * pulse) + vec3(1.0, 1.0, 0.9) * front * energy * 0.8;
}
