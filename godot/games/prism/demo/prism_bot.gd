class_name PrismBot
extends RefCounted
## The Prism Breaker autopilot (the demo): it follows where the lowest falling ball will cross the paddle line
## (bouncing off the side walls), and meets it off-centre so the ball heads for the side with more bricks left.
## With time to spare it goes for a falling capsule; it launches after a short pause and fires any laser.

var _rng := RandomNumberGenerator.new()
var _wait := 0.0
var _bias := 0.0


func _init(seed_ := 1) -> void:
	_rng.seed = seed_


func drive(e: PrismEngine) -> void:
	if e.phase == PrismEngine.Phase.SERVE or _held(e):
		_wait += PrismEngine.TICK
		e.target_x = 6.5 + sin(e.time * 0.9) * 2.0
		if _wait > 0.9:
			_wait = 0.0
			e.launch()
		return
	if e.phase != PrismEngine.Phase.PLAY:
		return
	e.fire()
	if e.warp_open and e.breakable > 0 and e.bricks.size() > 0 and e.balls.size() == 1 and e.balls[0]["vel"].y < 0.0:
		# a door is open: a safe moment to leave
		e.target_x = PrismEngine.W + 1.0
		return
	var ball := {}
	var soonest := INF
	for b in e.balls:
		var t: float = _time_to_line(b)
		if t < soonest:
			soonest = t
			ball = b
	if ball.is_empty():
		return
	var land := _landing(ball)
	# aim: hit with the paddle's side facing away from the bricks we want, sending the ball towards them
	if _rng.randf() < 0.01:
		_bias = _rng.randf_range(-0.35, 0.35)
	var want := _brick_side(e)
	if e._since_break > 5.0:
		# nothing broken for a while: sweep the aim to break the loop
		want = 0.0
		_bias = sin(e.time * 0.37) * 0.85
	var off := clampf(want * 0.55 + _bias, -0.8, 0.8) * e.paddle_w * 0.5
	var goal := land - off
	# a capsule worth catching, when the ball is far away
	for cp in e.capsules:
		var ct: float = (PrismEngine.PADDLE_Y - cp["pos"].y) / 3.0
		if ct > 0.0 and ct < soonest - 0.6 and absf(cp["pos"].x - e.paddle_x) / 26.0 + absf(cp["pos"].x - land) / 26.0 < soonest - ct:
			goal = cp["pos"].x
			break
	e.target_x = goal


func _held(e: PrismEngine) -> bool:
	for b in e.balls:
		if b["held"] > -90.0:
			return true
	return false


## Seconds until the ball next reaches the paddle line (going up counts the trip to the top and back).
func _time_to_line(b: Dictionary) -> float:
	var v: Vector2 = b["vel"]
	var p: Vector2 = b["pos"]
	var line := PrismEngine.PADDLE_Y - 0.17 - PrismEngine.BALL_R
	if v.y > 0.0:
		return (line - p.y) / v.y
	return (p.y + line) / maxf(-v.y, 0.01)


func _landing(b: Dictionary) -> float:
	var v: Vector2 = b["vel"]
	var p: Vector2 = b["pos"]
	var line := PrismEngine.PADDLE_Y - 0.17 - PrismEngine.BALL_R
	var dy := line - p.y if v.y > 0.0 else p.y + line
	var x := p.x + v.x / absf(v.y) * dy
	# unfold the reflections off the side walls
	var lo := PrismEngine.BALL_R
	var span := PrismEngine.W - 2.0 * lo
	var u := fposmod(x - lo, 2.0 * span)
	if u > span:
		u = 2.0 * span - u
	return lo + u


## -1 .. 1: which side of the paddle holds more of the breakable bricks.
func _brick_side(e: PrismEngine) -> float:
	var sum := 0.0
	var n := 0
	for c in e.bricks:
		if e.bricks[c]["hits"] > 0:
			sum += c.x + 0.5
			n += 1
	if n == 0:
		return 0.0
	return clampf((sum / n - e.paddle_x) / 4.0, -1.0, 1.0)
