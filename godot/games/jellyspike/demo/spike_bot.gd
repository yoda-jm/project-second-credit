class_name SpikeBot
extends RefCounted
## The Jelly Spike CPU player (and the demo). It plays the ball forward to find where it comes down to hitting height on
## its own half, stands a little behind that point (away from the net) so the touch sends the ball forward, and jumps
## into the ball to spike when it drops near the net or high over its head. With the ball on the other side it waits
## near home. "skill" (0-1) is how early it reads the ball and how precisely it stands; a little aim noise keeps rallies
## varied.

const S = preload("res://games/jellyspike/engine/spike_engine.gd")

var side := 1
var skill := 0.8
var rng := RandomNumberGenerator.new()
var _aim := 0.0
var _aim_t := 0.0
var _read := Vector2(8.0, 9.0)   ## where it last read the ball coming down (x, height reach), and when
var _read_t := 0.0


func _init(side_ := 1, skill_ := 0.8, seed_ := 7) -> void:
	side = side_
	skill = skill_
	rng.seed = seed_


func drive(e: SpikeEngine) -> void:
	e.move[side] = 0.0
	e.jump[side] = false
	if e.phase == S.Phase.OVER:
		return
	var b: Dictionary = e.blobs[side]
	var bx: float = b["pos"].x
	var to_net := 1.0 if side == 0 else -1.0
	_aim_t -= S.TICK
	if _aim_t <= 0.0:
		_aim_t = 0.6
		_aim = rng.randf_range(-0.5, 0.5) * (1.2 - skill)
	var ball: Dictionary = e.ball
	var bp: Vector2 = ball["pos"]
	var target := S._home(side)
	var want_jump := false
	var mine := (bp.x < S.NET_X) == (side == 0)
	if e.phase == S.Phase.SERVE and e.server == side:
		# serve: stand just behind the hanging ball, hop into it
		target = bp.x - to_net * 0.35
		want_jump = absf(bx - target) < 0.15 and e.phase_t <= 0.0
	elif e.phase == S.Phase.RALLY:
		# it reads the ball now and then, not every instant (less often at low skill)
		_read_t -= S.TICK
		if _read_t <= 0.0:
			_read_t = lerpf(0.3, 0.06, skill)
			_read = _landing(e, 1.35)
		var land := _read
		var on_my_side := (land.x < S.NET_X) == (side == 0)
		if on_my_side and land.y < 2.2 + skill * 1.5:
			target = land.x - to_net * (0.38 + _aim)
			# spike: the ball close to the net and coming down near him, or high over his head
			var near_net: bool = absf(bp.x - S.NET_X) < 3.2
			var over: bool = absf(bp.x - bx) < 0.9 and bp.y > 2.2 and bp.y < 4.2 and ball["vel"].y < 1.0
			want_jump = over and (near_net or e.touches[side] >= 2 or rng.randf() < 0.02 + skill * 0.03)
		elif mine:
			target = bp.x - to_net * 0.4
	# the power spike: arm it when the meter is full and the ball is on its way here
	if e.power[side] >= 1.0 and not e.armed[side] and e.phase == S.Phase.RALLY and mine and rng.randf() < 0.05 + skill * 0.05:
		e.power_pressed[side] = true
	var h := S.half(side)
	target = clampf(target, h.x, h.y)
	# not too close to the net: a ball played from under it goes into the net and comes straight back
	if absf(target - S.NET_X) < 1.4:
		target = S.NET_X - to_net * 1.4
	var dx := target - bx
	if absf(dx) > 0.06:
		e.move[side] = signf(dx)
	var d: Vector2 = bp - b["pos"]
	if e.phase == S.Phase.RALLY and mine and d.length() < 1.6:
		# about to touch: never move away from the net (that would flick the ball back), and after a first touch
		# jump into it from behind to get it over
		if e.move[side] * to_net < 0.0 and d.x * to_net > -0.2:
			e.move[side] = 0.0
		if e.touches[side] >= 1 and e.last_side == side and d.x * to_net > 0.0 and d.y > 0.6:
			want_jump = true
	e.jump[side] = want_jump or (not b["ground"] and b["vel"].y > 0.0)  # hold for a full jump
	return
	e.jump[side] = want_jump or (not b["ground"] and b["vel"].y > 0.0)  # hold for a full jump


## Where (x) and when (seconds) the ball comes down to height y, played forward with walls and the net's post.
func _landing(e: SpikeEngine, y: float) -> Vector2:
	var p: Vector2 = e.ball["pos"]
	var v: Vector2 = e.ball["vel"]
	var t := 0.0
	while t < 3.0:
		t += S.TICK * 2.0
		v.y -= S.BALL_G * S.TICK * 2.0
		p += v * S.TICK * 2.0
		if p.x < S.BALL_R or p.x > S.W - S.BALL_R:
			v.x = -v.x * 0.9
			p.x = clampf(p.x, S.BALL_R, S.W - S.BALL_R)
		if p.y < S.NET_H and absf(p.x - S.NET_X) < S.NET_HALF + S.BALL_R:
			v.x = -v.x * 0.8
			p.x = S.NET_X + signf(p.x - S.NET_X + 0.0001) * (S.NET_HALF + S.BALL_R)
		if v.y < 0.0 and p.y <= y:
			return Vector2(p.x, t)
	return Vector2(p.x, t)
