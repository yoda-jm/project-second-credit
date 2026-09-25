class_name ReplayRunner
extends RefCounted
## Plays a recorded replay the way GDash's GameControl does: one recorded movement per cave frame, then the
## bonus points for the remaining time. Used to prove the engine against GDash's replays, and for demos.


## Returns {success, score, frames, checksum, engine}.
static func play(cave: CaveStored, replay: CaveReplay, max_frames: int = 100000) -> Dictionary:
	var engine := CaveEngine.new(cave, replay.level - 1, replay.seed)
	var checksum := engine.adler_checksum()
	var score := 0
	var frames := 0
	var no_more_movements := 0
	replay.rewind()
	while engine.player_state != CaveRendered.PlayerState.TIMEOUT and frames < max_frames:
		var m := replay.next_movement()
		if m.is_empty():
			no_more_movements += 1
			if no_more_movements > 15:
				break
			m = [CaveDirections.STILL, false, false]
		engine.iterate(m[0], m[1], m[2])
		frames += 1
		score += engine.score
		if engine.player_state == CaveRendered.PlayerState.EXITED:
			score += time_bonus(engine)
			break
	return {"success": engine.player_state == CaveRendered.PlayerState.EXITED, "score": score,
		"frames": frames, "checksum": checksum, "engine": engine}


## GDash's check_bonus_score loop: points for every second left (fast count above 60 s). Consumes the time.
static func time_bonus(engine: CaveEngine) -> int:
	var bonus := 0
	while engine.time > 0:
		if engine.time > 60 * engine.timing_factor:
			engine.time -= 9 * engine.timing_factor
			bonus += engine.timevalue * 9
		else:
			engine.time -= engine.timing_factor
			bonus += engine.timevalue
		if engine.time < 0:
			engine.time = 0
	return bonus
