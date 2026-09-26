class_name CaveHud
extends Control
## Heads-up display: diamonds, time and score, the hatching countdown, and end-of-cave messages.

@export var game: CaveGame

var _message := ""
var _message_t := 0.0
var _time := 0.0
var _count := -1
var _death_t := -1.0
var _count_t := 0.0
var _time_total := 1


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.cave_finished.connect(func(_e, success): _show(("CAVE CLEARED" if success else "OUT OF TIME") \
		if success or game.engine.player_state == CaveRendered.PlayerState.TIMEOUT else "OUCH"))
	game.cave_started.connect(func(_e): _message = ""; _death_t = -1.0; _time_total = 1)
	game.cave_finished.connect(func(e, success):
		if not success and e.player_state == CaveRendered.PlayerState.DIED:
			_death_t = 0.0)
	game.countdown_tick.connect(func(n): _count = n; _count_t = 0.0)
	game.campaign_over.connect(func(won): _show("THE DESCENT IS DONE" if won else "GAME OVER"))


func _show(text: String) -> void:
	_message = text
	_message_t = 0.0


func _process(delta: float) -> void:
	_time += delta
	_message_t += delta
	_count_t += delta
	if _death_t >= 0.0:
		_death_t += delta
	queue_redraw()


func _hatch_fraction(engine: CaveEngine) -> float:
	## 1 at the start of the cave, 0 when the player hatches.
	if engine.hatched:
		return 0.0
	if engine.scheduling == CaveScheduling.MILLISECONDS:
		return float(engine.hatching_delay_frame) / maxf(1.0, float(engine.cave_hatching_frames))
	return float(engine.hatching_delay_time) / maxf(1.0, float(engine.cave_hatching_ms))


func _draw() -> void:
	var engine := game.engine
	if engine == null:
		return
	var vp := get_viewport_rect().size
	var secs := engine.time_visible()
	_time_total = maxi(_time_total, secs)
	# top: three floating panels (gems, time, score)
	var need := maxi(0, engine.diamonds_needed - engine.diamonds_collected)
	var gem_col := Color(0.4, 0.92, 1.0) if not engine.gate_open else HudKit.GOOD
	HudKit.panel(self, Rect2(24, 16, 330, 84), gem_col)
	HudKit.gem(self, Vector2(64, 58), 20.0, gem_col)
	if engine.gate_open:
		HudKit.stat(self, 100, 20, "GEMS", "EXIT OPEN", gem_col, HudKit.LEFT, 32)
	else:
		HudKit.stat(self, 100, 20, "GEMS NEEDED", "%d" % need, gem_col)
		HudKit.text(self, Vector2(338, 86), "x%d EACH" % engine.diamond_value, 16, HudKit.MUTED, HudKit.label_font(), HudKit.RIGHT)
	var low := secs <= 10 and engine.hatched
	var tcol := HudKit.BAD if low and fmod(_time, 0.5) < 0.25 else (HudKit.BAD if low else HudKit.INK)
	HudKit.panel(self, Rect2(vp.x * 0.5 - 110, 16, 220, 84), tcol if low else Color(1, 1, 1, 0.25))
	HudKit.stat(self, vp.x * 0.5, 20, "TIME", "%03d" % secs, tcol, HudKit.CENTER)
	var tf := float(secs) / maxf(1.0, float(_time_total))
	draw_rect(Rect2(vp.x * 0.5 - 86, 90, 172, 3), Color(1, 1, 1, 0.1))
	draw_rect(Rect2(vp.x * 0.5 - 86, 90, 172 * tf, 3), tcol)
	HudKit.panel(self, Rect2(vp.x - 314, 16, 290, 84), HudKit.GOLD)
	HudKit.stat(self, vp.x - 44, 20, "SCORE", "%06d" % game.score, HudKit.GOLD, HudKit.RIGHT)
	if game.pack:  # campaign: which cave, and the lives left
		HudKit.panel(self, Rect2(vp.x - 314, 108, 290, 44), Color(1, 1, 1, 0.2), 14, 0.9)
		HudKit.text(self, Vector2(vp.x - 294, 138), "CAVE %d / %d" % [game.cave_no + 1, game.caves.size()], 18, HudKit.INK, HudKit.label_font())
		for i in CaveGame.LIVES:
			HudKit.gem(self, Vector2(vp.x - 52 - i * 30, 130), 10.0, HudKit.BAD if i < game.lives else Color(1, 1, 1, 0.15))
	# 3-2-1-GO before the start, then the hatching ring until the player appears
	var c := Vector2(vp.x * 0.5, vp.y * 0.5)
	if game.countdown_left > 0.0 or (_count == 0 and _count_t < 0.8):
		var go := _count == 0
		var alpha := 1.0 if not go else clampf(1.0 - (_count_t - 0.3) / 0.5, 0.0, 1.0)
		var col := Color(HudKit.GOLD, alpha) if not go else Color(HudKit.GOOD, alpha)
		HudKit.shade(self, c, 330.0, 0.8 * alpha)
		var pop := 1.0 + 0.45 * exp(-_count_t * 10.0)
		if go:  # a shock ring flies out
			var k := clampf(_count_t / 0.6, 0.0, 1.0)
			draw_arc(c, 130.0 + 260.0 * k, 0, TAU, 96, Color(HudKit.GOOD, (1.0 - k) * 0.8), 10.0 * (1.0 - k) + 1.0, true)
		else:
			var frac := clampf(game.countdown_left - floorf(game.countdown_left - 0.0001), 0.0, 1.0)
			HudKit.ring(self, c, 130.0, frac, col, 9.0)
			HudKit.text(self, c + Vector2(0, -170), "GET READY", 22, Color(HudKit.MUTED, alpha), HudKit.label_font(), HudKit.CENTER)
		var label := "GO!" if go else str(_count)
		var size := int((120 if go else 150) * pop)
		HudKit.text(self, c + Vector2(0, size * 0.36), label, size, col, HudKit.font(true), HudKit.CENTER)
		var name_s: String = game.cave.name.to_upper()
		var nw := HudKit.width(name_s, 30, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(c.x - nw * 0.5, c.y + 178, nw, 56), Color(HudKit.GOLD, alpha * 0.8), 28, alpha)
		HudKit.text(self, c + Vector2(0, 217), name_s, 30, Color(HudKit.INK, alpha), HudKit.label_font(), HudKit.CENTER)
	else:
		var f := _hatch_fraction(engine)
		if f > 0.0:
			HudKit.ring(self, c, 60, f, Color(HudKit.GOLD, 0.85), 6.0)
	# red vignette pulse when the hero dies
	if _death_t >= 0.0 and _death_t < 2.0:
		var a := (1.0 - _death_t / 2.0) * 0.55
		for i in 12:
			var inset := float(i) * 18.0
			draw_rect(Rect2(inset, inset, vp.x - inset * 2.0, vp.y - inset * 2.0), Color(0.8, 0.05, 0.02, a * 0.12), false, 18.0)
	# end-of-cave banner
	if _message != "":
		var a := clampf(_message_t * 3.0, 0.0, 1.0)
		var won := game.engine.player_state == CaveRendered.PlayerState.EXITED
		var pop := 1.0 + 0.2 * exp(-_message_t * 8.0)
		HudKit.banner(self, vp, vp.y * 0.45, _message, ("SCORE %d" % game.score) if won or game.campaign_done else "",
			HudKit.GOOD if won else HudKit.BAD, a, pop)
		if game.campaign_done:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.45 + 130), [["ENTER", "play again"], ["ESC", "menu"]], a)
	if game.player == 0 and game.playing_demo:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 30), [["ARROWS", "play"], ["F2", "two-player race"]], 0.9)
