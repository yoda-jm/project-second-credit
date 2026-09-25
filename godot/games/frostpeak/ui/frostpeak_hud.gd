class_name FrostpeakHud
extends Control
## Frostpeak Games HUD: players' setup, event cards, the events' live read-outs (stride meter, balance gauge),
## results, standings, the medal ceremony and the final medal table.

const S := preload("res://games/frostpeak/scenes/frostpeak_game.gd").Stage
const ICE := Color(0.6, 0.85, 1.0)
const HOWTO := {
	"speed_skating": "ALTERNATE LEFT AND RIGHT  -  PUSH WHEN THE METER IS GREEN",
	"ski_jump": "HOLD DOWN TO TUCK  -  SPACE AT THE LIP  -  UP / DOWN IN THE AIR  -  SPACE TO LAND",
}

@export var game: FrostpeakGame

var _t := 0.0
var _pop := ""
var _pop_t := 10.0
var _pop_col := HudKit.GOOD
var _banner := ""
var _banner_t := 10.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.attempt_started.connect(func(ev):
		ev.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"stride":
			_popup({"perfect": "PERFECT!", "good": "GOOD", "weak": "TOO EARLY"}.get(d["quality"], ""),
				{"perfect": HudKit.GOOD, "good": HudKit.GOLD, "weak": HudKit.BAD}.get(d["quality"], HudKit.INK))
		"stumble": _popup("WRONG FOOT!", HudKit.BAD)
		"false_start":
			_banner = "FALSE START" if d["count"] < 2 else "DISQUALIFIED"
			_banner_t = 0.0
		"takeoff":
			var q: float = d["quality"]
			_popup("PERFECT TAKE-OFF!" if q > 0.85 else ("GOOD TAKE-OFF" if q > 0.5 else "LATE TAKE-OFF" if q > 0.0 else "MISSED THE LIP"),
				HudKit.GOOD if q > 0.85 else (HudKit.GOLD if q > 0.5 else HudKit.BAD))
		"landed":
			_popup("TELEMARK!" if d["telemark"] else ("FALL!" if d["fell"] else "TWO-FOOTED"), HudKit.GOOD if d["telemark"] else HudKit.BAD)


func _popup(text: String, col: Color) -> void:
	_pop = text
	_pop_col = col
	_pop_t = 0.0


func _process(delta: float) -> void:
	_t += delta
	_pop_t += delta
	_banner_t += delta
	queue_redraw()


func _flag(r: Rect2, nation: int) -> void:
	var cols: Array = Competition.NATIONS[nation]["flag"]
	for i in 3:
		draw_rect(Rect2(r.position + Vector2(r.size.x * i / 3.0, 0), Vector2(r.size.x / 3.0 + 0.5, r.size.y)), cols[i])
	draw_rect(r, Color(0, 0, 0, 0.4), false, 1.5)


func _draw() -> void:
	var vp := get_viewport_rect().size
	match game.stage:
		S.SETUP: _draw_setup(vp)
		S.INTRO: _draw_intro(vp)
		S.ATTEMPT, S.RESULT: _draw_attempt(vp)
		S.STANDINGS: _draw_standings(vp)
		S.PODIUM: _draw_podium(vp)
		S.FINAL: _draw_final(vp)
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var w := HudKit.width(msg, 24, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5, vp.y - 66, w, 46), Color(0, 0, 0, 0), 23, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 34), msg, 24, HudKit.INK, HudKit.label_font(), HudKit.CENTER)


func _draw_setup(vp: Vector2) -> void:
	HudKit.text(self, Vector2(vp.x * 0.5, 190), "FROSTPEAK GAMES", 96, ICE, HudKit.font(true), HudKit.CENTER)
	HudKit.text(self, Vector2(vp.x * 0.5, 240), "SPEED SKATING  -  SKI JUMP", 26, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
	var y := 320.0
	for i in game.setup_players.size():
		var p := game.setup_players[i]
		var sel := i == game.setup_cursor
		HudKit.panel(self, Rect2(vp.x * 0.5 - 330, y, 660, 76), ICE if sel else Color(0, 0, 0, 0), 14, 1.0 if sel else 0.7)
		_flag(Rect2(vp.x * 0.5 - 300, y + 18, 60, 40), p["nation"])
		HudKit.text(self, Vector2(vp.x * 0.5 - 220, y + 50), p["name"], 30, HudKit.INK, HudKit.font(true))
		HudKit.text(self, Vector2(vp.x * 0.5 + 300, y + 50), Competition.NATIONS[p["nation"]]["name"].to_upper(), 28,
			ICE if sel else HudKit.MUTED, HudKit.label_font(), HudKit.RIGHT)
		y += 92.0
	HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 110), [["LEFT / RIGHT", "nation"], ["UP / DOWN", "player"], ["+ / -", "players"],
		["ENTER", "start the games"]])


func _draw_intro(vp: Vector2) -> void:
	var ev := game.comp.event_name()
	var a := clampf(minf(game.stage_t * 3.0, (3.5 - game.stage_t) * 3.0), 0.0, 1.0)
	HudKit.banner(self, vp, vp.y * 0.42, Competition.EVENT_TITLES[ev], "EVENT %d OF %d" % [game.comp.current + 1, game.comp.programme.size()], ICE, a)
	HudKit.text(self, Vector2(vp.x * 0.5, vp.y * 0.42 + 130), HOWTO[ev], 24, Color(HudKit.INK, a), HudKit.label_font(), HudKit.CENTER)


func _athlete_panel(vp: Vector2) -> void:
	var idx: int = game.humans()[mini(game.athlete, game.humans().size() - 1)]
	var at: Dictionary = game.comp.athletes[idx]
	HudKit.panel(self, Rect2(24, 16, 420, 84), ICE)
	_flag(Rect2(46, 36, 54, 36), at["nation"])
	HudKit.stat(self, 120, 20, Competition.NATIONS[at["nation"]]["name"].to_upper(), at["name"], HudKit.INK, HudKit.LEFT, 30)


func _draw_attempt(vp: Vector2) -> void:
	var ev := game.ev
	_athlete_panel(vp)
	if ev is SpeedSkating:
		var s := ev as SpeedSkating
		HudKit.panel(self, Rect2(vp.x * 0.5 - 220, 16, 440, 84), ICE)
		HudKit.stat(self, vp.x * 0.5 - 110, 20, "TIME", "%.2f" % s.time, HudKit.INK, HudKit.CENTER)
		HudKit.stat(self, vp.x * 0.5 + 110, 20, "DISTANCE", "%d M" % mini(int(s.pos), 500), HudKit.INK, HudKit.CENTER)
		HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), HudKit.GOLD)
		HudKit.stat(self, vp.x - 48, 20, "SPEED", "%d KM/H" % int(s.speed * 3.6), HudKit.GOLD, HudKit.RIGHT)
		# the stride meter: fills up; push in the green zone, with the right foot
		var bar := Rect2(vp.x * 0.5 - 300, vp.y - 170, 600, 26)
		HudKit.panel(self, bar.grow(14), Color(0, 0, 0, 0), 14, 0.9)
		draw_rect(bar, Color(1, 1, 1, 0.08))
		var gz := Rect2(bar.position.x + bar.size.x * SpeedSkating.GREEN.x / 1.3, bar.position.y, bar.size.x * (SpeedSkating.GREEN.y - SpeedSkating.GREEN.x) / 1.3, bar.size.y)
		draw_rect(gz, Color(HudKit.GOOD, 0.35))
		var fill := clampf(s.meter / 1.3, 0.0, 1.0)
		var in_green := s.meter >= SpeedSkating.GREEN.x and s.meter <= SpeedSkating.GREEN.y
		draw_rect(Rect2(bar.position, Vector2(bar.size.x * fill, bar.size.y)), HudKit.GOOD if in_green else ICE)
		var left := s.next_foot == "left"
		var glow := 0.55 + 0.45 * sin(_t * 12.0) if in_green else 0.5
		HudKit.keycap(self, Vector2(bar.position.x - 150, bar.end.y), "LEFT", "", glow if left else 0.25)
		HudKit.keycap(self, Vector2(bar.end.x + 40, bar.end.y), "RIGHT", "", glow if not left else 0.25)
		if s.phase == WinterEvent.Phase.READY:
			_countdown(vp, s.phase_left)
	elif ev is SkiJump:
		var j := ev as SkiJump
		HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), HudKit.GOLD)
		HudKit.stat(self, vp.x - 48, 20, "SPEED", "%d KM/H" % int(j.speed * 3.6), HudKit.GOLD, HudKit.RIGHT)
		HudKit.panel(self, Rect2(vp.x * 0.5 - 170, 16, 340, 84), ICE)
		var dist := j.distance if j.stage == SkiJump.Stage.LANDED else maxf(0.0, j.fly.x)
		HudKit.stat(self, vp.x * 0.5, 20, "DISTANCE", "%.1f M" % dist, HudKit.INK, HudKit.CENTER)
		match j.stage:
			SkiJump.Stage.INRUN:
				var k := clampf(j.along / SkiJump.INRUN, 0.0, 1.0)
				var bar := Rect2(vp.x * 0.5 - 300, vp.y - 160, 600, 16)
				draw_rect(bar, Color(1, 1, 1, 0.1))
				draw_rect(Rect2(bar.position, Vector2(bar.size.x * k, bar.size.y)), ICE)
				draw_rect(Rect2(bar.end.x - 20, bar.position.y - 6, 20, bar.size.y + 12), HudKit.GOOD)
				HudKit.text(self, Vector2(bar.end.x, bar.position.y - 14), "THE LIP", 16, HudKit.MUTED, HudKit.label_font(), HudKit.RIGHT)
				if j.phase == WinterEvent.Phase.READY:
					_countdown(vp, j.phase_left)
				else:
					HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 100), [["DOWN", "tuck"], ["SPACE", "jump at the lip"]])
			SkiJump.Stage.FLIGHT:
				# the balance gauge: keep the needle in the green
				var c := Vector2(vp.x * 0.5, vp.y - 120)
				draw_arc(c, 90, PI * 1.15, PI * 1.85, 40, Color(1, 1, 1, 0.15), 14, true)
				draw_arc(c, 90, PI * 1.5 - 0.22, PI * 1.5 + 0.22, 20, Color(HudKit.GOOD, 0.6), 14, true)
				var a := PI * 1.5 + clampf(j.angle, -0.9, 0.9) * 0.75
				draw_line(c, c + Vector2(cos(a), sin(a)) * 100.0, HudKit.GOLD if absf(j.angle) < 0.3 else HudKit.BAD, 5.0, true)
				draw_circle(c, 8, HudKit.INK, true, -1.0, true)
				HudKit.text(self, c + Vector2(0, 40), "UP / DOWN: BALANCE    SPACE: LAND", 20, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
	if _pop != "" and _pop_t < 0.9:
		var a := clampf(1.0 - (_pop_t - 0.5) / 0.4, 0.0, 1.0)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y * 0.34 - _pop_t * 30.0), _pop, int(44 * (1.0 + 0.2 * exp(-_pop_t * 10.0))), Color(_pop_col, a), HudKit.font(true), HudKit.CENTER)
	if _banner != "" and _banner_t < 1.8:
		HudKit.banner(self, vp, vp.y * 0.45, _banner, "", HudKit.BAD, clampf(minf(_banner_t * 5.0, (1.8 - _banner_t) * 4.0), 0.0, 1.0))
	if game.stage == S.RESULT:
		var a := clampf(game.stage_t * 4.0, 0.0, 1.0)
		HudKit.banner(self, vp, vp.y * 0.5, ev.result_text, Competition.EVENT_TITLES[game.comp.event_name()], HudKit.GOLD, a)


func _countdown(vp: Vector2, left: float) -> void:
	var n := ceili(left)
	var frac := left - floorf(left - 0.0001)
	var c := Vector2(vp.x * 0.5, vp.y * 0.42)
	HudKit.shade(self, c, 200.0, 0.6)
	HudKit.ring(self, c, 90.0, frac, HudKit.GOLD, 8.0)
	HudKit.text(self, c + Vector2(0, 40), str(n), 110, HudKit.GOLD, HudKit.font(true), HudKit.CENTER)


func _draw_standings(vp: Vector2) -> void:
	var ev := game.comp.event_name()
	var rk := game.comp.ranking(ev)
	var w := 760.0
	var top := 170.0
	HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5, top, w, 110 + rk.size() * 64), ICE)
	HudKit.text(self, Vector2(vp.x * 0.5, top + 60), Competition.EVENT_TITLES[ev], 38, ICE, HudKit.font(true), HudKit.CENTER)
	var medal := [HudKit.GOLD, Color(0.8, 0.82, 0.88), Color(0.85, 0.55, 0.3)]
	for i in rk.size():
		var at: Dictionary = game.comp.athletes[rk[i]]
		var y := top + 120 + i * 64
		if i < 3:
			draw_circle(Vector2(vp.x * 0.5 - w * 0.5 + 50, y), 16, medal[i], true, -1.0, true)
		HudKit.text(self, Vector2(vp.x * 0.5 - w * 0.5 + 50, y + 10), str(i + 1), 24, Color(0.05, 0.05, 0.1) if i < 3 else HudKit.INK, HudKit.font(true), HudKit.CENTER)
		_flag(Rect2(vp.x * 0.5 - w * 0.5 + 90, y - 16, 48, 32), at["nation"])
		HudKit.text(self, Vector2(vp.x * 0.5 - w * 0.5 + 160, y + 10), at["name"].to_upper(), 28, HudKit.GOLD if not at["cpu"] else HudKit.INK, HudKit.font(true))
		var v: float = game.comp.results[ev][rk[i]]
		var txt := ("%.2f S" % v) if Competition.LOWER_IS_BETTER[ev] else ("%.1f PTS" % v)
		HudKit.text(self, Vector2(vp.x * 0.5 + w * 0.5 - 40, y + 10), txt, 28, HudKit.INK, HudKit.font(true), HudKit.RIGHT)


func _draw_podium(vp: Vector2) -> void:
	var ev := game.comp.event_name()
	var rk := game.comp.ranking(ev)
	HudKit.text(self, Vector2(vp.x * 0.5, 150), "MEDAL CEREMONY", 56, HudKit.GOLD, HudKit.font(true), HudKit.CENTER)
	HudKit.text(self, Vector2(vp.x * 0.5, 195), Competition.EVENT_TITLES[ev], 26, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
	var names := ["GOLD", "SILVER", "BRONZE"]
	var cols := [HudKit.GOLD, Color(0.8, 0.82, 0.88), Color(0.85, 0.55, 0.3)]
	for place in mini(3, rk.size()):
		var at: Dictionary = game.comp.athletes[rk[place]]
		var x: float = vp.x * 0.5 + [0.0, -420.0, 420.0][place]
		HudKit.panel(self, Rect2(x - 180, vp.y - 210, 360, 100), cols[place])
		HudKit.stat(self, x, vp.y - 206, names[place], at["name"].to_upper(), cols[place], HudKit.CENTER, 30)


func _draw_final(vp: Vector2) -> void:
	var m := game.comp.medals()
	var order: Array = m.keys()
	order.sort_custom(func(a, b): return m[a][0] * 10000 + m[a][1] * 100 + m[a][2] > m[b][0] * 10000 + m[b][1] * 100 + m[b][2])
	var w := 820.0
	var top := 150.0
	HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5, top, w, 150 + order.size() * 62), HudKit.GOLD)
	HudKit.text(self, Vector2(vp.x * 0.5, top + 64), "MEDAL TABLE", 48, HudKit.GOLD, HudKit.font(true), HudKit.CENTER)
	var cols := [HudKit.GOLD, Color(0.8, 0.82, 0.88), Color(0.85, 0.55, 0.3)]
	for k in 3:
		draw_circle(Vector2(vp.x * 0.5 + 170 + k * 90, top + 110), 14, cols[k], true, -1.0, true)
	for i in order.size():
		var at: Dictionary = game.comp.athletes[order[i]]
		var y := top + 160 + i * 62
		_flag(Rect2(vp.x * 0.5 - w * 0.5 + 40, y - 16, 48, 32), at["nation"])
		HudKit.text(self, Vector2(vp.x * 0.5 - w * 0.5 + 110, y + 10), at["name"].to_upper(), 28, HudKit.GOLD if not at["cpu"] else HudKit.INK, HudKit.font(true))
		for k in 3:
			HudKit.text(self, Vector2(vp.x * 0.5 + 170 + k * 90, y + 10), str(m[order[i]][k]), 30, HudKit.INK, HudKit.font(true), HudKit.CENTER)
	if not game.demo:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 60), [["ENTER", "new games"], ["ESC", "menu"]])
