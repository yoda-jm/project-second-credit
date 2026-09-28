class_name FrostpeakReplay
extends RefCounted
## A recording of one attempt for the TV replay: the athlete's transform (in the venue's frame) and animation, frame
## by frame, stamped with the live clock, plus the moments that matter (take-off, landing). Playback interpolates
## between frames, so slow motion is smooth at any rate.

var times := PackedFloat32Array()
var xforms: Array[Transform3D] = []
var anims: Array[StringName] = []
var anim_pos := PackedFloat32Array()
var marks := {}  ## name -> live time ("takeoff", "landed")
var clock := 0.0


func clear() -> void:
	times.clear()
	xforms.clear()
	anims.clear()
	anim_pos.clear()
	marks.clear()
	clock = 0.0


func record(delta: float, xf: Transform3D, anim: StringName, pos: float) -> void:
	clock += delta
	times.append(clock)
	xforms.append(xf)
	anims.append(anim)
	anim_pos.append(pos)


func mark(name: String) -> void:
	if not marks.has(name):
		marks[name] = clock


func empty() -> bool:
	return times.size() < 2


func length() -> float:
	return clock


## The frame index at or just before live time `t`.
func _index(t: float) -> int:
	var lo := 0
	var hi := times.size() - 1
	if t <= times[0]:
		return 0
	if t >= times[hi]:
		return hi - 1
	while hi - lo > 1:
		var m := (lo + hi) >> 1
		if times[m] <= t:
			lo = m
		else:
			hi = m
	return lo


## The athlete's transform at live time `t` (interpolated).
func xform_at(t: float) -> Transform3D:
	var i := _index(t)
	var f := clampf((t - times[i]) / maxf(times[i + 1] - times[i], 0.0001), 0.0, 1.0)
	return xforms[i].interpolate_with(xforms[i + 1], f)


## [animation, its position] at live time `t`.
func anim_at(t: float) -> Array:
	var i := _index(t)
	var f := clampf((t - times[i]) / maxf(times[i + 1] - times[i], 0.0001), 0.0, 1.0)
	if anims[i] != anims[i + 1] or anim_pos[i + 1] < anim_pos[i]:
		return [anims[i + 1] if f > 0.5 else anims[i], anim_pos[i + 1] if f > 0.5 else anim_pos[i]]
	return [anims[i], lerpf(anim_pos[i], anim_pos[i + 1], f)]
