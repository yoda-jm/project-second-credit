class_name FrostpeakHud
extends Control
## Frostpeak Games HUD: the menu (competition or practice), players' setup, event cards, the events' live read-outs
## (stride meter, balance gauge), results, the TV replay's branding and wipes, standings, the medal ceremony and
## the final medal table.

const S := preload("res://games/frostpeak/scenes/frostpeak_game.gd").Stage
const ICE := Color(0.6, 0.85, 1.0)
const HOWTO := {
	"speed_skating": "ALTERNATE LEFT AND RIGHT  -  PUSH WHEN THE METER IS GREEN",
	"ski_jump": "HOLD DOWN TO TUCK  -  SPACE AT THE LIP  -  UP / DOWN IN THE AIR  -  SPACE TO LAND",
	"biathlon": "LEFT / RIGHT IN RHYTHM  -  DOWN TO TUCK  -  AT THE RANGE: ARROWS TO AIM, SPACE TO FIRE",
	"bobsled": "LEFT / RIGHT IN RHYTHM TO PUSH  -  SPACE TO JUMP IN  -  LEFT / RIGHT TO STEER: KEEP OFF THE TOP OF THE BANKS",
}

@export var game: FrostpeakGame
@export var view: FrostpeakView3D

var _t := 0.0
var _pop := ""
var _pop_t := 10.0
var _pop_col := HudKit.GOOD
var _banner := ""
var _banner_t := 10.0
var _banner_col := HudKit.BAD
var _map: PackedVector2Array  ## the biathlon course, for the little map
var _bob_map: PackedVector2Array  ## the bobsled run, for its map
var _split_t := 10.0
var _quote := ""  ## a crash's card, with a little bounce
var _quote_t := 10.0
## Said to a crew that has just flipped: our own cheerful lines, as a laid-back island crew might shout.
const CRASH_LINES: Array[String] = ["YO MAN...  YOU STILL ALIVE IN THERE?", "EASY, BROTHER  -  THE ICE WON THAT ROUND",
	"SLED UPSIDE DOWN, SMILE RIGHT WAY UP!", "NO WORRY, MAN  -  WE WALK DOWN IN STYLE", "HEY!  WHO PUT THE SKY DOWN THERE?"]


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
			_banner_col = HudKit.BAD
			_banner_t = 0.0
		"takeoff":
			var q: float = d["quality"]
			_popup("PERFECT TAKE-OFF!" if q > 0.85 else ("GOOD TAKE-OFF" if q > 0.5 else "LATE TAKE-OFF" if q > 0.0 else "MISSED THE LIP"),
				HudKit.GOOD if q > 0.85 else (HudKit.GOLD if q > 0.5 else HudKit.BAD))
		"landed":
			_popup("TELEMARK!" if d["telemark"] else ("FALL!" if d["fell"] else "TWO-FOOTED"), HudKit.GOOD if d["telemark"] else HudKit.BAD)
		"shot":
			_popup("HIT" if d["hit"] else "MISS", HudKit.GOOD if d["hit"] else HudKit.BAD)
		"range_done":
			var m: int = d["misses"]
			_banner = "CLEAN!  5 / 5" if m == 0 else "%d / 5  -  %d PENALTY LOOP%s" % [5 - m, m, "S" if m > 1 else ""]
			_banner_col = HudKit.GOOD if m == 0 else HudKit.GOLD
			_banner_t = 0.0
		"penalty":
			_popup("PENALTY LOOP", HudKit.BAD)
		"load": _popup("JUMP IN!", HudKit.GOOD)
		"late":
			_banner = "LATE ON BOARD"
			_banner_col = HudKit.BAD
			_banner_t = 0.0
		"wall": _popup("WALL!" if d["strength"] > 1.2 else "SCRAPE", HudKit.BAD)
		"crash":
			_banner = "CRASH!"
			_banner_col = HudKit.BAD
			_banner_t = 0.0
			_quote = CRASH_LINES[int(float(d.get("at", 0.0)) * 7.0) % CRASH_LINES.size()]
			_quote_t = -0.9  # after the banner
		"split": _split_t = 0.0


func _popup(text: String, col: Color) -> void:
	_pop = text
	_pop_col = col
	_pop_t = 0.0


func _process(delta: float) -> void:
	_t += delta
	_pop_t += delta
	_banner_t += delta
	_split_t += delta
	_quote_t += delta
	queue_redraw()


func _flag(r: Rect2, nation: int) -> void:
	var cols: Array = Competition.NATIONS[nation]["flag"]
	for i in 3:
		draw_rect(Rect2(r.position + Vector2(r.size.x * i / 3.0, 0), Vector2(r.size.x / 3.0 + 0.5, r.size.y)), cols[i])
	draw_rect(r, Color(0, 0, 0, 0.4), false, 1.5)


func _draw() -> void:
	var vp := get_viewport_rect().size
	match game.stage:
		S.MENU: _draw_menu(vp)
		S.SETUP: _draw_setup(vp)
		S.INTRO: _draw_intro(vp)
		S.ATTEMPT, S.RESULT: _draw_attempt(vp)
		S.REPLAY: _draw_replay(vp)
		S.NEXT: _draw_next(vp)
		S.STANDINGS: _draw_standings(vp)
		S.PODIUM: _draw_podium(vp)
		S.FINAL: _draw_final(vp)
	if game.practice != "" and game.stage in [S.INTRO, S.ATTEMPT, S.RESULT, S.REPLAY, S.NEXT]:
		_draw_practice(vp)
	if view and view.wipe_time() >= 0.0:
		_draw_wipe(vp, view.wipe_time())
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var w := HudKit.width(msg, 24, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5, vp.y - 66, w, 46), Color(0, 0, 0, 0), 23, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 34), msg, 24, HudKit.INK, HudKit.label_font(), HudKit.CENTER)


func _event_list() -> String:
	var names: Array[String] = []
	for e in Competition.EVENTS:
		names.append(Competition.EVENT_SHORT[e])
	return "  -  ".join(names)


func _draw_menu(vp: Vector2) -> void:
	HudKit.text(self, Vector2(vp.x * 0.5, 190), "FROSTPEAK GAMES", 96, ICE, HudKit.font(true), HudKit.CENTER)
	HudKit.text(self, Vector2(vp.x * 0.5, 240), _event_list(), 26, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
	var items := game.menu_items()
	var y := 300.0
	for i in items.size():
		var sel := i == game.menu_cursor
		var h := 84.0 if i == 0 else 64.0
		var pulse := 0.85 + 0.15 * sin(_t * 5.0) if sel else 0.7
		HudKit.panel(self, Rect2(vp.x * 0.5 - 360, y, 720, h), (HudKit.GOLD if i == 0 else ICE) if sel else Color(0, 0, 0, 0), 14, pulse)
		var label: String = items[i] if i == 0 else Competition.EVENT_TITLES[Competition.EVENTS[i - 1]]
		if i == 0:
			HudKit.text(self, Vector2(vp.x * 0.5, y + 54), label, 40, HudKit.GOLD if sel else HudKit.INK, HudKit.font(true), HudKit.CENTER)
		else:
			HudKit.text(self, Vector2(vp.x * 0.5 - 330, y + 43), "PRACTICE", 22, ICE if sel else HudKit.MUTED, HudKit.label_font())
			HudKit.text(self, Vector2(vp.x * 0.5 - 170, y + 45), label, 30, HudKit.INK if sel else HudKit.MUTED, HudKit.font(true))
		y += h + 14.0
		if i == 0:
			y += 20.0
	HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 110), [["UP / DOWN", "choose"], ["ENTER", "go"], ["ESC", "leave"]])


func _draw_setup(vp: Vector2) -> void:
	HudKit.text(self, Vector2(vp.x * 0.5, 190), "FROSTPEAK GAMES", 96, ICE, HudKit.font(true), HudKit.CENTER)
	var sub: String = _event_list() if game.practice == "" else "PRACTICE  -  " + Competition.EVENT_TITLES[game.practice]
	HudKit.text(self, Vector2(vp.x * 0.5, 240), sub, 26, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
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
		["ENTER", "start the games" if game.practice == "" else "start practice"], ["BACKSPACE", "back"]])


func _draw_intro(vp: Vector2) -> void:
	var ev := game.comp.event_name()
	var card := game.intro_card()  # the card shows while the venue comes into view
	var a := clampf(minf((game.stage_t - card.x) * 2.5, (card.y - game.stage_t) * 2.5), 0.0, 1.0)
	var y := vp.y * 0.7  # low on the screen, under the venue
	var sub := "PRACTICE" if game.practice != "" else "EVENT %d OF %d" % [game.comp.current + 1, game.comp.programme.size()]
	if a > 0.0:
		HudKit.banner(self, vp, y, Competition.EVENT_TITLES[ev], sub, ICE, a)
		HudKit.text(self, Vector2(vp.x * 0.5, y + 130), HOWTO[ev], 24, Color(HudKit.INK, a), HudKit.label_font(), HudKit.CENTER)
	_up_next(vp, clampf(minf((game.stage_t - card.y - 0.4) * 2.5, (game.stage_seconds(S.INTRO) - game.stage_t) * 2.5), 0.0, 1.0))


## The next athlete up, in a lower third, while the camera flies to the start.
func _draw_next(vp: Vector2) -> void:
	var dur := game.stage_seconds(S.NEXT)
	_up_next(vp, clampf(minf((game.stage_t - 0.6) * 2.5, (dur - game.stage_t) * 2.5), 0.0, 1.0))


func _up_next(vp: Vector2, a: float) -> void:
	if a <= 0.0:
		return
	var at: Dictionary = game.comp.athletes[game.current_athlete()]
	var r := Rect2(70, vp.y - 250, 620, 96)
	HudKit.panel(self, r, ICE, 14, a)
	_flag(Rect2(r.position + Vector2(24, 26), Vector2(66, 44)), at["nation"])
	HudKit.text(self, r.position + Vector2(112, 38), "AT THE START" if game.comp.event_name() in ["speed_skating", "bobsled"] else "AT THE GATE", 20,
		Color(ICE, a), HudKit.label_font())
	HudKit.text(self, r.position + Vector2(112, 76), "%s  -  %s" % [at["name"].to_upper(), Competition.NATIONS[at["nation"]]["code"]], 32,
		Color(HudKit.INK, a), HudKit.font(true))


func _athlete_panel(vp: Vector2) -> void:
	var idx: int = game.humans()[mini(game.athlete, game.humans().size() - 1)]
	var at: Dictionary = game.comp.athletes[idx]
	HudKit.panel(self, Rect2(24, 16, 420, 84), ICE)
	_flag(Rect2(46, 36, 54, 36), at["nation"])
	HudKit.stat(self, 120, 20, Competition.NATIONS[at["nation"]]["name"].to_upper(), at["name"], HudKit.INK, HudKit.LEFT, 30)


func _draw_attempt(vp: Vector2) -> void:
	var ev := game.ev
	if ev is Biathlon and view:
		_scope(vp, ev as Biathlon, view.bview.scope_k)
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
	elif ev is Biathlon:
		_draw_biathlon(vp, ev as Biathlon)
	elif ev is Bobsled:
		_draw_bob(vp, ev as Bobsled)
	elif ev is SkiJump:
		var j := ev as SkiJump
		HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), HudKit.GOLD)
		HudKit.stat(self, vp.x - 48, 20, "SPEED", "%d KM/H" % int(j.speed * 3.6), HudKit.GOLD, HudKit.RIGHT)
		HudKit.panel(self, Rect2(vp.x * 0.5 - 170, 16, 340, 84), ICE)
		var dist := j.current_distance()
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
	if _banner != "" and _banner_t < (2.6 if _banner_col != HudKit.BAD else 1.8):
		HudKit.banner(self, vp, vp.y * 0.45, _banner, "", _banner_col, clampf(minf(_banner_t * 5.0, (1.8 - _banner_t) * 4.0), 0.0, 1.0))
	if game.stage == S.RESULT:
		var a := clampf(game.stage_t * 4.0, 0.0, 1.0)
		var sub: String = Competition.EVENT_TITLES[game.comp.event_name()]
		if game.practice != "" and game.best.get(game.current_athlete(), INF) == ev.result:
			sub = "PERSONAL BEST"
		HudKit.banner(self, vp, vp.y * 0.5, ev.result_text, sub, HudKit.GOLD, a)


## The TV replay: a REPLAY bug in the corner, SLOW MOTION while it is slowed, the result in a strip along the foot.
func _draw_replay(vp: Vector2) -> void:
	if view == null or view.rp_shot() == "":
		return
	var r := Rect2(40, 34, 300, 70)
	HudKit.panel(self, r, HudKit.BAD, 12, 0.95)
	var blink := 0.55 + 0.45 * sin(_t * 6.0)
	draw_circle(r.position + Vector2(36, 35), 11, Color(HudKit.BAD, blink), true, -1.0, true)
	HudKit.text(self, r.position + Vector2(62, 50), "REPLAY", 40, HudKit.INK, HudKit.font(true))
	var slow := view.rp_rate() < 0.7
	if slow:
		var s := Rect2(r.end.x + 14, r.position.y + 14, 230, 42)
		HudKit.panel(self, s, ICE, 10, 0.9)
		HudKit.text(self, s.get_center() + Vector2(0, 9), "SLOW MOTION", 24, ICE, HudKit.label_font(), HudKit.CENTER)
	var label: String = {"takeoff": "THE TAKE-OFF", "flight": "IN THE AIR", "impact": "THE LANDING"}.get(view.rp_shot(), "")
	HudKit.text(self, Vector2(r.position.x + 4, r.end.y + 40), label, 22, Color(HudKit.INK, 0.85), HudKit.label_font())
	var at: Dictionary = game.comp.athletes[game.current_athlete()]
	var strip := Rect2(vp.x * 0.5 - 420, vp.y - 128, 840, 76)
	HudKit.panel(self, strip, HudKit.GOLD, 12, 0.92)
	_flag(Rect2(strip.position + Vector2(22, 18), Vector2(60, 40)), at["nation"])
	HudKit.text(self, strip.position + Vector2(100, 50), at["name"].to_upper(), 30, HudKit.INK, HudKit.font(true))
	HudKit.text(self, strip.end - Vector2(24, 26), game.ev.result_text, 30, HudKit.GOLD, HudKit.font(true), HudKit.RIGHT)
	if not game.demo:
		HudKit.hints(self, Vector2(vp.x - 200, vp.y - 24), [["ENTER", "skip"]], 0.8)


## A TV wipe: a slanted band in the games' colours sweeps across and covers the screen for the cut beneath it.
func _draw_wipe(vp: Vector2, t: float) -> void:
	var cover := FrostpeakView3D.WIPE_COVER
	var u := t / (2.0 * cover)  # 0 .. 1 across the whole wipe
	var e := u * u * (3.0 - 2.0 * u)
	var slant := vp.y * 0.45
	var w := vp.x + slant * 2.0  # wide enough to cover everything at the middle
	var x := lerpf(-w - slant, vp.x + slant, e)
	var band := func(x0: float, width: float, col: Color) -> void:
		draw_colored_polygon(PackedVector2Array([Vector2(x0 + slant, 0), Vector2(x0 + slant + width, 0),
			Vector2(x0 + width, vp.y), Vector2(x0, vp.y)]), col)
	band.call(x - 60.0, w + 120.0, Color(HudKit.GOLD, 0.95))
	band.call(x - 22.0, w + 44.0, Color(0.95, 0.97, 1.0))
	band.call(x, w, Color(0.06, 0.16, 0.42))
	var c := Vector2(x + w * 0.5 + slant * 0.5, vp.y * 0.5)
	if c.x > -300.0 and c.x < vp.x + 300.0:
		HudKit.text(self, c + Vector2(0, 30), "FROSTPEAK", 96, Color(1, 1, 1, 0.95), HudKit.font(true), HudKit.CENTER)
		HudKit.text(self, c + Vector2(0, 86), view.wipe_text(), 30, HudKit.GOLD, HudKit.label_font(), HudKit.CENTER)


## Practice: the event and each player's best, top right under the read-outs.
func _draw_practice(vp: Vector2) -> void:
	var at := game.current_athlete()
	var ev := game.practice
	var r := Rect2(vp.x - 324, 112, 300, 64)
	HudKit.panel(self, r, ICE, 12, 0.85)
	var b: String = "- - -"
	if game.best.has(at):
		b = Competition.format(ev, game.best[at])
	HudKit.text(self, r.position + Vector2(18, 26), "PRACTICE  -  BEST", 18, ICE, HudKit.label_font())
	HudKit.text(self, r.position + Vector2(18, 54), b, 26, HudKit.INK, HudKit.font(true))
	if not game.demo and game.stage in [S.RESULT, S.REPLAY, S.NEXT]:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 24), [["ENTER", "next attempt"], ["ESC", "menu"]], 0.8)


## The biathlon read-outs: the race clock and the lap, speed and heart rate (the pulse drawn as it beats), the stride
## meter while skiing, the five targets at the range, and a little map of the course.
func _draw_biathlon(vp: Vector2, b: Biathlon) -> void:
	var scoped := view != null and view.bview.scope_k > 0.5
	HudKit.panel(self, Rect2(vp.x * 0.5 - 230, 16, 460, 84), ICE)
	HudKit.stat(self, vp.x * 0.5 - 110, 20, "TIME", Competition.format("biathlon", b.time), HudKit.INK, HudKit.CENTER)
	var where := "LAP %d / %d" % [b.lap() + 1, Biathlon.LAPS]
	if b.stage == Biathlon.Stage.RANGE:
		where = "RANGE"
	elif b.stage == Biathlon.Stage.PENALTY:
		where = "PENALTY %d / %d" % [mini(int(b.pen_done / BiathlonCourse.pen_loop()) + 1, b.misses), b.misses]
	HudKit.stat(self, vp.x * 0.5 + 110, 20, "STAGE", where, HudKit.INK if b.stage != Biathlon.Stage.PENALTY else HudKit.BAD, HudKit.CENTER)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), HudKit.GOLD)
	HudKit.stat(self, vp.x - 48, 20, "SPEED", "%d KM/H" % int(b.speed * 3.6), HudKit.GOLD, HudKit.RIGHT)
	# the heart: rate, a beating heart and a trace
	var hr_col := HudKit.GOOD if b.hr < 130.0 else (HudKit.GOLD if b.hr < 165.0 else HudKit.BAD)
	var hp := Rect2(vp.x - 324, 112 if game.practice == "" else 188, 300, 70)
	HudKit.panel(self, hp, hr_col, 12, 0.9)
	var beat := fposmod(b._beat, 1.0)
	var pump := 1.0 + 0.25 * exp(-beat * 9.0)
	_heart(hp.position + Vector2(38, 36), 13.0 * pump, hr_col)
	HudKit.text(self, hp.position + Vector2(70, 48), "%d" % int(b.hr), 34, HudKit.INK, HudKit.font(true))
	HudKit.text(self, hp.position + Vector2(146, 48), "BPM", 18, HudKit.MUTED, HudKit.label_font())
	var trace := PackedVector2Array()
	for i in 40:
		var u := float(i) / 39.0
		var ph := fposmod(b._beat - (1.0 - u) * 1.6, 1.0)
		var y := -exp(-pow((ph - 0.1) * 30.0, 2.0)) * 18.0 + exp(-pow((ph - 0.16) * 28.0, 2.0)) * 7.0
		trace.append(hp.position + Vector2(196 + u * 90, 36 + y))
	draw_polyline(trace, Color(hr_col, 0.9), 2.0, true)
	if not scoped:
		_course_map(vp, b)
	if b.phase == WinterEvent.Phase.READY:
		_countdown(vp, b.phase_left)
		return
	match b.stage:
		Biathlon.Stage.SKI, Biathlon.Stage.PENALTY:
			# the stride meter: fill, push in the green with the right foot
			var bar := Rect2(vp.x * 0.5 - 300, vp.y - 170, 600, 22)
			HudKit.panel(self, bar.grow(14), Color(0, 0, 0, 0), 14, 0.85)
			draw_rect(bar, Color(1, 1, 1, 0.08))
			var gz := Rect2(bar.position.x + bar.size.x * Biathlon.GREEN.x / 1.3, bar.position.y,
				bar.size.x * (Biathlon.GREEN.y + 0.08 - Biathlon.GREEN.x) / 1.3, bar.size.y)
			draw_rect(gz, Color(HudKit.GOOD, 0.35))
			var in_green := b.meter >= Biathlon.GREEN.x and b.meter <= Biathlon.GREEN.y + 0.08
			draw_rect(Rect2(bar.position, Vector2(bar.size.x * clampf(b.meter / 1.3, 0.0, 1.0), bar.size.y)), HudKit.GOOD if in_green else ICE)
			var left := b.next_foot == "left"
			var glow := 0.55 + 0.45 * sin(_t * 12.0) if in_green else 0.5
			HudKit.keycap(self, Vector2(bar.position.x - 150, bar.end.y), "LEFT", "", glow if left else 0.25)
			HudKit.keycap(self, Vector2(bar.end.x + 40, bar.end.y), "RIGHT", "", glow if not left else 0.25)
			var sl := b.slope()
			var tip := "DOWN  -  tuck" if sl < -0.03 else ("UPHILL  -  quicker rhythm" if sl > 0.05 else "")
			if b.hr > 170.0:
				tip = "EASE OFF  -  heart racing"
			if tip != "":
				HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 196), tip, 22, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
		Biathlon.Stage.RANGE:
			# the five targets: black until hit, white once hit, crossed out when missed
			var c := Vector2(vp.x * 0.5, vp.y - 112)
			HudKit.panel(self, Rect2(c.x - 190, c.y - 40, 380, 80), ICE, 14, 0.9)
			for i in Biathlon.SHOTS:
				var p := c + Vector2((i - 2) * 66, 0)
				draw_circle(p, 24, Color(0.95, 0.95, 0.97), true, -1.0, true)
				if i < b.hits.size():
					if not b.hits[i]:
						draw_circle(p, 17, Color(0.02, 0.02, 0.03), true, -1.0, true)
						draw_line(p - Vector2(15, 15), p + Vector2(15, 15), HudKit.BAD, 4.0, true)
						draw_line(p + Vector2(-15, 15), p + Vector2(15, -15), HudKit.BAD, 4.0, true)
				else:
					draw_circle(p, 17, Color(0.02, 0.02, 0.03), true, -1.0, true)
				if i == b.shot and not b.shooting_done:
					draw_arc(p, 30, 0, TAU, 32, HudKit.GOLD, 3.0, true)
			if scoped and not b.shooting_done:
				HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 36), [["ARROWS", "aim"], ["SPACE", "fire"]], 0.85)


## The bobsled read-outs: the race clock and the speed, the splits as they come, a map of the run, the push meter
## and the prompt to jump in at the start; on the run a section of the channel with the sled on it (where it rides
## the banks, red near the top where it would flip) and the g-force.
func _draw_bob(vp: Vector2, b: Bobsled) -> void:
	HudKit.panel(self, Rect2(vp.x * 0.5 - 230, 16, 460, 84), ICE)
	HudKit.stat(self, vp.x * 0.5 - 110, 20, "TIME", "%.2f" % b.clock if b.timing else "0.00", HudKit.INK, HudKit.CENTER)
	var where := "START"
	if b.stage == Bobsled.Stage.RIDE or b.stage == Bobsled.Stage.CRASH:
		var c := BobTrack.curve_at(b.s)
		where = "CURVE %d" % (c + 1) if c >= 0 else ("FINISH" if b.s > BobTrack.FINISH - 60.0 else "STRAIGHT")
		if b.phase == WinterEvent.Phase.DONE:
			where = "FINISH"
		if b.crashed:
			where = "CRASHED"
	HudKit.stat(self, vp.x * 0.5 + 110, 20, "ON THE RUN", where, HudKit.BAD if b.crashed else HudKit.INK, HudKit.CENTER)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), HudKit.GOLD)
	var sp := view.bobview.shown_speed if view else b.speed
	HudKit.stat(self, vp.x - 48, 20, "SPEED", "%d KM/H" % int(sp * 3.6), HudKit.GOLD, HudKit.RIGHT)
	# the splits, under the athlete
	var names := ["START", "INTERMEDIATE 1", "INTERMEDIATE 2"]
	var y := 118.0
	for i in b.splits.size():
		var fresh := i == b.splits.size() - 1 and _split_t < 3.0
		var r := Rect2(24, y, 420, 46)
		HudKit.panel(self, r, HudKit.GOLD if fresh else ICE, 10, 0.9 if fresh else 0.7)
		HudKit.text(self, r.position + Vector2(18, 31), names[i], 20, ICE if not fresh else HudKit.GOLD, HudKit.label_font())
		HudKit.text(self, r.end - Vector2(18, 15), "%.2f" % b.splits[i], 26, HudKit.INK, HudKit.font(true), HudKit.RIGHT)
		y += 54.0
	_bob_map_draw(vp, b)
	if b.phase == WinterEvent.Phase.READY:
		_countdown(vp, b.phase_left)
		return
	match b.stage:
		Bobsled.Stage.PUSH:
			var bar := Rect2(vp.x * 0.5 - 300, vp.y - 170, 600, 22)
			HudKit.panel(self, bar.grow(14), Color(0, 0, 0, 0), 14, 0.85)
			draw_rect(bar, Color(1, 1, 1, 0.08))
			var gz := Rect2(bar.position.x + bar.size.x * Bobsled.GREEN.x / 1.3, bar.position.y,
				bar.size.x * (Bobsled.GREEN.y + 0.08 - Bobsled.GREEN.x) / 1.3, bar.size.y)
			draw_rect(gz, Color(HudKit.GOOD, 0.35))
			var in_green := b.meter >= Bobsled.GREEN.x and b.meter <= Bobsled.GREEN.y + 0.08
			draw_rect(Rect2(bar.position, Vector2(bar.size.x * clampf(b.meter / 1.3, 0.0, 1.0), bar.size.y)), HudKit.GOOD if in_green else ICE)
			var left := b.next_foot == "left"
			var glow := 0.55 + 0.45 * sin(_t * 12.0) if in_green else 0.5
			HudKit.keycap(self, Vector2(bar.position.x - 150, bar.end.y), "LEFT", "", glow if left else 0.25)
			HudKit.keycap(self, Vector2(bar.end.x + 40, bar.end.y), "RIGHT", "", glow if not left else 0.25)
			# how far down the ramp: jump in before its end
			var ramp := Rect2(vp.x * 0.5 - 300, vp.y - 214, 600, 8)
			draw_rect(ramp, Color(1, 1, 1, 0.12))
			draw_rect(Rect2(ramp.position, Vector2(ramp.size.x * clampf(b.s / BobTrack.PUSH_END, 0.0, 1.0), ramp.size.y)), HudKit.GOLD)
			if b.s >= Bobsled.LOAD_EARLIEST:
				var urge := smoothstep(28.0, 44.0, b.s)
				var a := 0.5 + 0.5 * urge * (0.5 + 0.5 * sin(_t * 10.0))
				HudKit.keycap(self, Vector2(vp.x * 0.5 - 40, vp.y - 236), "SPACE", "jump in", a)
		Bobsled.Stage.RIDE, Bobsled.Stage.CRASH, Bobsled.Stage.LOAD:
			if b.phase != WinterEvent.Phase.DONE:
				_bank_gauge(vp, b)
	if b.crashed and _quote != "" and _quote_t > 0.0:
		_crash_card(vp)


## The crash's card: a sticker-like panel that pops in with a bounce and a tilt, and the line on it.
func _crash_card(vp: Vector2) -> void:
	var t := _quote_t
	var k := clampf(t * 5.0, 0.0, 1.0) * (1.0 + 0.3 * exp(-t * 4.0) * sin(t * 20.0))
	var a := clampf(minf(t * 4.0, (7.0 - t) * 2.0), 0.0, 1.0)
	if a <= 0.0 or k <= 0.01:
		return
	var c := Vector2(vp.x * 0.5, vp.y * 0.3)
	draw_set_transform(c, -0.05 + 0.03 * sin(t * 3.0), Vector2(k, k))
	var w := HudKit.width(_quote, 40, HudKit.font(true)) + 90.0
	var r := Rect2(-w * 0.5, -58, w, 116)
	draw_rect(r.grow(8), Color(0.05, 0.05, 0.05, 0.85 * a))
	for i in 3:  # three stripes along the top: green, gold, black
		draw_rect(Rect2(r.position + Vector2(r.size.x * i / 3.0, 0), Vector2(r.size.x / 3.0 + 1.0, 10)),
			Color([Color(0.1, 0.55, 0.25), HudKit.GOLD, Color(0.1, 0.1, 0.1)][i], a))
	HudKit.text(self, Vector2(0, 22), _quote, 40, Color(HudKit.GOLD, a), HudKit.font(true), HudKit.CENTER)
	HudKit.text(self, Vector2(0, 48), "- THE CREW, FROM UNDER THE SLED -", 16, Color(HudKit.INK, 0.8 * a), HudKit.label_font(), HudKit.CENTER)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


## The channel's section with the sled on it: the floor, the walls curving up to the top; the outside of a curve
## shaded towards red where the sled would flip over.
func _bank_gauge(vp: Vector2, b: Bobsled) -> void:
	var c := Vector2(vp.x * 0.5, vp.y - 150)
	var r := 72.0
	var fl := 38.0
	HudKit.panel(self, Rect2(c.x - 180, c.y - 92, 360, 132), ICE, 16, 0.8)
	var pt := func(w: float) -> Vector2:
		var side := signf(w) if w != 0.0 else 1.0
		var a := absf(w)
		if a <= BobTrack.FLOOR:
			return c + Vector2(w / BobTrack.FLOOR * fl, 20.0)
		var al := minf(a - BobTrack.FLOOR, PI * 0.5)
		return c + Vector2(side * (fl + r * sin(al)), 20.0 - r * (1.0 - cos(al)))
	var line := PackedVector2Array()
	var n := 40
	for i in n + 1:
		var w := lerpf(-BobTrack.FLOOR - PI * 0.5, BobTrack.FLOOR + PI * 0.5, float(i) / n)
		line.append(pt.call(w))
	draw_polyline(line, Color(1, 1, 1, 0.55), 5.0, true)
	# the danger at the top of the outside bank of the curve now (or coming)
	var k := BobTrack.kappa(b.s + b.speed * 0.4)
	if absf(k) > 0.002:
		var out := -signf(k)
		for part in [[Bobsled.DANGER, Bobsled.FLIP, HudKit.GOLD], [Bobsled.FLIP, PI * 0.5, HudKit.BAD]]:
			var arc := PackedVector2Array()
			for i in 9:
				var al := lerpf(part[0], part[1], i / 8.0)
				arc.append(pt.call(out * (BobTrack.FLOOR + al)))
			draw_polyline(arc, part[2], 7.0, true)
	var danger := b.alpha >= Bobsled.DANGER and not b.crashed
	var dot: Vector2 = pt.call(b.w)
	var col := HudKit.BAD if danger else HudKit.GOOD
	draw_circle(dot, 11.0 + (3.0 * sin(_t * 14.0) if danger else 0.0), col, true, -1.0, true)
	draw_arc(dot, 13.0, 0, TAU, 20, Color(0, 0, 0, 0.6), 2.0, true)
	HudKit.text(self, c + Vector2(-164, -58), "%.1f G" % b.g_force, 24, HudKit.INK, HudKit.font(true))
	if danger:
		HudKit.text(self, c + Vector2(0, -58), "TOO HIGH  -  STEER DOWN", 20, HudKit.BAD, HudKit.label_font(), HudKit.CENTER)
	if not game.demo and b.stage == Bobsled.Stage.RIDE:
		HudKit.text(self, c + Vector2(164, -58), "LEFT / RIGHT", 16, HudKit.MUTED, HudKit.label_font(), HudKit.RIGHT)


## The run from above, bottom right: its line, the curves' numbers, the timing eyes and the sled.
func _bob_map_draw(vp: Vector2, b: Bobsled) -> void:
	if _bob_map.is_empty():
		var s := 0.0
		while s <= BobTrack.length():
			_bob_map.append(BobTrack.xz(s))
			s += 5.0
	var box := Rect2(vp.x - 214, vp.y - 400, 190, 350)
	HudKit.panel(self, box, ICE, 12, 0.75)
	var lo := Vector2(INF, INF)
	var hi := -lo
	for p in _bob_map:
		lo = Vector2(minf(lo.x, p.x), minf(lo.y, p.y))
		hi = Vector2(maxf(hi.x, p.x), maxf(hi.y, p.y))
	var k := minf((box.size.x - 40) / (hi.x - lo.x), (box.size.y - 40) / (hi.y - lo.y))
	var off := box.position + (box.size - (hi - lo) * k) * 0.5
	var to := func(p: Vector2) -> Vector2: return off + (p - lo) * k
	var line := PackedVector2Array()
	for p in _bob_map:
		line.append(to.call(p))
	draw_polyline(line, Color(ICE, 0.35), 6.0, true)
	var done := PackedVector2Array()
	for i in _bob_map.size():
		if i * 5.0 > b.s:
			break
		done.append(line[i])
	if done.size() > 1:
		draw_polyline(done, HudKit.GOLD, 4.0, true)
	var cs := BobTrack.curves()
	for i in cs.size():
		var q: Vector2 = to.call(BobTrack.xz((cs[i][0] + cs[i][1]) * 0.5))
		var out := -signf(cs[i][2])
		var d := BobTrack.dir((cs[i][0] + cs[i][1]) * 0.5)
		var n := Vector2(-d.y, d.x) * out * 14.0
		HudKit.text(self, q + n + Vector2(0, 6), str(i + 1), 14, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
	for sp in [BobTrack.START_LINE, BobTrack.FINISH]:
		draw_circle(to.call(BobTrack.xz(sp)), 5, HudKit.INK, true, -1.0, true)
	var dot: Vector2 = to.call(BobTrack.xz(minf(b.s, BobTrack.length())))
	draw_circle(dot, 7 + 2 * sin(_t * 8.0), HudKit.BAD if b.crashed else HudKit.GOOD, true, -1.0, true)
	draw_arc(dot, 10, 0, TAU, 20, Color(0, 0, 0, 0.6), 2.0, true)


## A heart shape.
func _heart(c: Vector2, r: float, col: Color) -> void:
	var pts := PackedVector2Array()
	for i in 32:
		var t := TAU * i / 32.0
		pts.append(c + Vector2(16.0 * pow(sin(t), 3.0), -(13.0 * cos(t) - 5.0 * cos(2.0 * t) - 2.0 * cos(3.0 * t) - cos(4.0 * t))) * r / 16.0)
	draw_colored_polygon(pts, col)


## The course from above, bottom right: the loop, the range, the penalty loop and the skier.
func _course_map(vp: Vector2, b: Biathlon) -> void:
	if _map.is_empty():
		var s := 0.0
		while s <= BiathlonCourse.lap():
			_map.append(BiathlonCourse.xz(s))
			s += 6.0
	var box := Rect2(vp.x - 264, vp.y - 250, 240, 200)
	HudKit.panel(self, box, ICE, 12, 0.75)
	var lo := Vector2(-440, -305)
	var hi := Vector2(-220, -180)
	var k := minf((box.size.x - 30) / (hi.x - lo.x), (box.size.y - 30) / (hi.y - lo.y))
	var to := func(p: Vector2) -> Vector2: return box.position + Vector2(15, 15) + (p - lo) * k
	var line := PackedVector2Array()
	for p in _map:
		line.append(to.call(p))
	draw_polyline(line, Color(ICE, 0.8), 3.0, true)
	var m := BiathlonCourse.mat()
	draw_circle(to.call(Vector2(m.x, m.z)), 5, HudKit.GOLD, true, -1.0, true)
	var t := BiathlonCourse.targets()
	draw_line(to.call(Vector2(t.x - 12, t.z)), to.call(Vector2(t.x + 12, t.z)), Color(HudKit.INK, 0.6), 3.0)
	var pen := PackedVector2Array()
	for u in range(0, int(BiathlonCourse.pen_loop()) + 1, 4):
		var q := BiathlonCourse.pen_point(u)
		pen.append(to.call(Vector2(q.x, q.z)))
	draw_polyline(pen, Color(HudKit.BAD, 0.7), 2.0, true)
	if view:
		var sp: Vector3 = view.bview.pos
		var dot: Vector2 = to.call(Vector2(sp.x, sp.z))
		draw_circle(dot, 7 + 2 * sin(_t * 8.0), HudKit.GOOD, true, -1.0, true)
		draw_arc(dot, 10, 0, TAU, 20, Color(0, 0, 0, 0.6), 2.0, true)


## The rifle's sight: the world closes down to a circle, a ring the size of the target in its middle (the aim is the
## middle of the screen: the rifle's sway moves the targets, as it would through a real sight).
func _scope(vp: Vector2, b: Biathlon, k: float) -> void:
	if k <= 0.01:
		return
	var c := vp * 0.5
	var e := k * k * (3.0 - 2.0 * k)
	var r := lerpf(vp.length() * 0.6, vp.y * 0.44, e)
	var w := 3000.0
	draw_arc(c, r + w * 0.5, 0.0, TAU, 160, Color(0.0, 0.0, 0.0, 0.97 * e), w)
	for i in 8:  # the soft inner edge of the tube
		draw_arc(c, r - i * 5.0, 0.0, TAU, 160, Color(0.0, 0.0, 0.0, 0.28 * e * (1.0 - i / 8.0)), 5.0)
	var ring: float = view.target_px() * 1.45
	var col := Color(0.03, 0.03, 0.04, 0.9 * e)
	draw_arc(c, ring, 0.0, TAU, 64, col, 3.0, true)
	draw_arc(c, ring + 6.0, 0.0, TAU, 64, Color(1, 1, 1, 0.25 * e), 1.5, true)
	for dir in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]:
		draw_line(c + dir * (ring + 14.0), c + dir * (r * 0.92), col, 2.0, true)


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
		var txt := Competition.format(ev, v)
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
