class_name CaveHud
extends Control
## Heads-up display: diamonds, time and score, the hatching countdown, and end-of-cave messages.

@export var game: CaveGame

var _font_size := 34
var _message := ""
var _message_t := 0.0
var _time := 0.0
var _count := -1
var _death_t := -1.0
var _count_t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.cave_finished.connect(func(_e, success): _show(("CAVE CLEARED" if success else "OUT OF TIME") \
		if success or game.engine.player_state == CaveRendered.PlayerState.TIMEOUT else "OUCH"))
	game.cave_started.connect(func(_e): _message = ""; _death_t = -1.0)
	game.cave_finished.connect(func(e, success):
		if not success and e.player_state == CaveRendered.PlayerState.DIED:
			_death_t = 0.0)
	game.countdown_tick.connect(func(n): _count = n; _count_t = 0.0)


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
	var font := get_theme_default_font()
	var vp := get_viewport_rect().size
	# top bar
	draw_rect(Rect2(0, 0, vp.x, 64), Color(0, 0, 0, 0.45))
	var need := maxi(0, engine.diamonds_needed - engine.diamonds_collected)
	var gem_col := Color(0.4, 0.95, 1.0) if not engine.gate_open else Color(0.4, 1.0, 0.55)
	_diamond_icon(Vector2(40, 32), 14.0, gem_col)
	_text(font, Vector2(66, 44), ("%d" % need) if not engine.gate_open else "EXIT OPEN", gem_col)
	_text(font, Vector2(260, 44), "x%d" % engine.diamond_value, Color(0.75, 0.8, 0.9))
	var secs := engine.time_visible()
	var tcol := Color(1, 1, 1) if secs > 10 or fmod(_time, 0.5) < 0.25 else Color(1, 0.35, 0.3)
	_text_centered(font, Vector2(vp.x * 0.5, 44), "%03d" % secs, tcol)
	_text_right(font, Vector2(vp.x - 30, 44), "%06d" % game.score, Color(1, 0.85, 0.35))
	# 3-2-1-GO before the start, then the hatching ring until the player appears
	var c := Vector2(vp.x * 0.5, vp.y * 0.5)
	if game.countdown_left > 0.0 or (_count == 0 and _count_t < 0.8):
		var label := "GO!" if _count == 0 else str(_count)
		var pop := 1.0 + 0.6 * exp(-_count_t * 9.0)
		var alpha := 1.0 if _count > 0 else clampf(1.0 - (_count_t - 0.4) / 0.4, 0.0, 1.0)
		var col := Color(1.0, 0.85, 0.35, alpha) if _count > 0 else Color(0.45, 1.0, 0.6, alpha)
		var frac := clampf(game.countdown_left - floorf(game.countdown_left - 0.0001), 0.0, 1.0) if _count > 0 else 0.0
		if _count > 0:
			draw_arc(c + Vector2(0, -30), 120, 0, TAU, 72, Color(1, 1, 1, 0.12), 12, true)
			draw_arc(c + Vector2(0, -30), 120, -PI * 0.5, -PI * 0.5 + TAU * frac, 72, col, 12, true)
		_text_centered(font, c + Vector2(0, 10), label, col, int(110 * pop))
		_text_centered(font, c + Vector2(0, 150), game.cave.name.to_upper(), Color(1, 1, 1, alpha * 0.9), 36)
	else:
		var f := _hatch_fraction(engine)
		if f > 0.0:
			draw_arc(c, 60, -PI * 0.5, -PI * 0.5 + TAU * f, 48, Color(1.0, 0.85, 0.35, 0.8), 8, true)
	# red vignette pulse when the hero dies
	if _death_t >= 0.0 and _death_t < 2.0:
		var a := (1.0 - _death_t / 2.0) * 0.55
		for i in 12:
			var inset := float(i) * 18.0
			draw_rect(Rect2(inset, inset, vp.x - inset * 2.0, vp.y - inset * 2.0), Color(0.8, 0.05, 0.02, a * 0.12), false, 18.0)
	# message
	if _message != "":
		var a := clampf(_message_t * 3.0, 0.0, 1.0)
		_text_centered(font, Vector2(vp.x * 0.5, vp.y * 0.45), _message, Color(1, 1, 1, a), 72)
		if game.engine.player_state == CaveRendered.PlayerState.EXITED:
			_text_centered(font, Vector2(vp.x * 0.5, vp.y * 0.45 + 70), "score %d" % game.score, Color(1, 0.85, 0.35, a), 40)


func _diamond_icon(c: Vector2, r: float, col: Color) -> void:
	draw_colored_polygon(PackedVector2Array([c + Vector2(0, -r), c + Vector2(r * 0.8, 0), c + Vector2(0, r),
		c + Vector2(-r * 0.8, 0)]), col)


func _text(font: Font, pos: Vector2, s: String, col: Color, size: int = -1) -> void:
	var sz := _font_size if size < 0 else size
	draw_string_outline(font, pos, s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz, 6, Color(0, 0, 0, col.a))
	draw_string(font, pos, s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz, col)


func _text_centered(font: Font, pos: Vector2, s: String, col: Color, size: int = -1) -> void:
	var sz := _font_size if size < 0 else size
	var w := font.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz).x
	_text(font, pos - Vector2(w * 0.5, 0), s, col, sz)


func _text_right(font: Font, pos: Vector2, s: String, col: Color, size: int = -1) -> void:
	var sz := _font_size if size < 0 else size
	var w := font.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz).x
	_text(font, pos - Vector2(w, 0), s, col, sz)
