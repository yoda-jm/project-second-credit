class_name TinBot
extends RefCounted
## A CPU driver. It follows a racing line (the centreline pulled towards the inside of each bend, a little ahead of
## it), steering for a point further along the line the faster it goes; it lifts off when the bends ahead are
## sharper than its speed allows, and swerves for a wrench near its line. `skill` (0..1) trims its pace and adds a
## little wobble, so the field spreads out.

const T = preload("res://games/tinplate/engine/tin_engine.gd")

var line := PackedVector2Array()
var skill := 0.8
var rng := RandomNumberGenerator.new()
var _wobble := 0.0


func _init(track: TinTrack, seed_ := 1, skill_ := 0.8) -> void:
	rng.seed = seed_
	skill = skill_
	var n := track.count()
	line.resize(n)
	for s in n:
		# the bend a little ahead, smoothed
		var b := 0.0
		for k in range(-6, 14):
			b += track.bend[(s + k + n) % n]
		b /= 20.0
		var off := clampf(b * 9.0, -0.3, 0.3) * track.width
		line[s] = track.pos[s] + track.left_normal(s) * off


func drive(e: TinEngine, c: Dictionary) -> void:
	var t := e.track
	var n := t.count()
	var s: int = c["s"]
	var p: Vector2 = c["pos"]
	var speed: float = (c["vel"] as Vector2).length()
	if e.phase == T.Phase.COUNTDOWN:
		c["throttle"] = 0.0
		c["steer"] = 0.0
		return
	var look := int(5 + speed * 0.5)
	var aim := line[(s + look) % n]
	# a wrench close to the line ahead is worth a swerve
	if not e.wrench.is_empty():
		var wp: Vector2 = e.wrench["pos"]
		var ws: int = e.wrench["s"]
		var ahead := (ws - s + n) % n
		if ahead > 2 and ahead < 30 and absf(e.wrench["y"] - c["y"]) < 1.0:
			aim = aim.lerp(wp, 0.6)
	var want := (aim - p).angle()
	var diff := wrapf(want - float(c["heading"]), -PI, PI)
	_wobble = lerpf(_wobble, rng.randf_range(-1.0, 1.0), 0.02)
	c["steer"] = clampf(diff * 2.8 + _wobble * 0.08 * (1.0 - skill), -1.0, 1.0)
	# how fast the bends ahead allow
	var sharp := 0.0
	for k in range(2, 26, 2):
		sharp = maxf(sharp, absf(t.bend[(s + k) % n]))
	var lat := e.grip(c) * 3.6
	var limit := sqrt(lat / maxf(sharp, 0.01)) * (0.86 + 0.14 * skill)
	var top := e.top_speed(c) * (0.9 + 0.1 * skill)
	c["throttle"] = 1.0 if speed < minf(limit, top) and absf(diff) < 0.9 else 0.0
	if speed < 3.0:
		c["throttle"] = 1.0


## Between races: three wrenches buy a level of whichever upgrade is lowest.
static func upgrade(c: Dictionary) -> void:
	while c["wrenches"] >= 3:
		var up: Dictionary = c["up"]
		var best := "speed"
		for k in ["grip", "accel", "speed"]:
			if up[k] < up[best]:
				best = k
		if up[best] >= 4:
			return
		up[best] += 1
		c["wrenches"] -= 3
