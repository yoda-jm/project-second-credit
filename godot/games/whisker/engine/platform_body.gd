class_name PlatformBody
extends RefCounted
## A kinematic platformer body: an axis-aligned box standing on its feet (pos is the bottom centre), with gravity,
## one-way platforms (land on them from above, drop through with down) and moving platforms that carry it.
## World units are metres, x to the right, y up. Deterministic: step() only depends on its inputs.

var pos := Vector2.ZERO
var vel := Vector2.ZERO
var size := Vector2(0.9, 0.6)
var on_ground := false
var ground: Dictionary = {}  ## the platform stood on, or empty
var gravity := 30.0
var drop_until := 0.0  ## ignore one-way platforms until this time (dropping through)


## Platforms: {rect: Rect2 (only the top edge matters: y = rect.end.y), vel: Vector2, solid: bool}.
## `solid` platforms (floors) can't be dropped through. Bounds clamp x.
func step(dt: float, platforms: Array, bounds: Rect2, time: float) -> void:
	var was_ground := ground
	if on_ground and not was_ground.is_empty():
		pos += was_ground.get("vel", Vector2.ZERO) * dt  # carried by moving platforms
	vel.y -= gravity * dt
	pos.x = clampf(pos.x + vel.x * dt, bounds.position.x + size.x * 0.5, bounds.end.x - size.x * 0.5)
	var prev_y := pos.y
	pos.y += vel.y * dt
	on_ground = false
	ground = {}
	if vel.y <= 0.0:
		var best := -INF
		for p in platforms:
			var r: Rect2 = p["rect"]
			var top := r.end.y
			if not p.get("solid", false) and time < drop_until:
				continue
			if pos.x + size.x * 0.4 < r.position.x or pos.x - size.x * 0.4 > r.end.x:
				continue
			if prev_y >= top - 0.001 and pos.y <= top and top > best:
				best = top
				ground = p
		if not ground.is_empty():
			pos.y = best
			vel.y = 0.0
			on_ground = true
	if pos.y < bounds.position.y:
		pos.y = bounds.position.y
		vel.y = 0.0
		on_ground = true


func rect() -> Rect2:
	return Rect2(pos.x - size.x * 0.5, pos.y, size.x, size.y)


func touches(other: Rect2) -> bool:
	return rect().intersects(other)
