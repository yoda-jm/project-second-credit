class_name BlastHud
extends Control
## Blastyard HUD: the setup screen; in play, one panel per bomber (colour, wins, bombs, fire, speed, kick), the round
## clock (and HURRY UP in sudden death), the countdown, the round and match results; in solo, the stage, lives and
## creatures left.

const E = preload("res://games/blastyard/engine/blast_engine.gd")
const COLORS := BlastView3D.COLORS
const NAMES := ["WHITE", "RED", "BLUE", "YELLOW"]
const ACCENT := Color(1.0, 0.55, 0.2)

@export var game: BlastGame

var _t := 0.0
var _hurry_t := -1.0
var _result := ""
var _result_t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.round_started.connect(func(e):
		_hurry_t = -1.0
		_result = ""
		e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"hurry": _hurry_t = 0.0
		"round_over":
			if game.mode == "solo":
				_result = "OUT OF LIVES" if game.lives <= 1 else "TRY AGAIN"
			elif d["winner"] < 0:
				_result = "DRAW"
			else:
				_result = "%s WINS THE %s" % [NAMES[d["winner"]], "MATCH" if game.match_winner == d["winner"] else "ROUND"]
			_result_t = 0.0
		"stage_clear":
			_result = "STAGE CLEAR"
			_result_t = 0.0


func _process(delta: float) -> void:
	_t += delta
	_result_t += delta
	if _hurry_t >= 0.0:
		_hurry_t += delta
	queue_redraw()


func _draw() -> void:
	var vp := get_viewport_rect().size
	if game.in_setup:
		_draw_setup(vp)
		return
	var e := game.engine
	if e == null:
		return
	# the bombers, two panels on each side
	for p in e.players:
		var s: int = p["slot"]
		var x := 24.0 if s % 2 == 0 else vp.x - 304.0
		var y := 24.0 if s < 2 else vp.y - 134.0
		var col: Color = COLORS[s]
		HudKit.panel(self, Rect2(x, y, 280, 110), col, 14, 0.9 if p["alive"] else 0.5)
		var who := ("CPU" if game.is_bot(s) else "P%d" % (s + 1))
		HudKit.text(self, Vector2(x + 20, y + 32), "%s  %s" % [NAMES[s], who], 16, col, HudKit.label_font())
		if game.mode == "battle":
			for k in BlastGame.WINS:
				HudKit.gem(self, Vector2(x + 200 + k * 26, y + 26), 9.0, HudKit.GOLD if k < game.wins[s] else Color(1, 1, 1, 0.15))
		var stats := [["BOMBS", p["bombs"]], ["FIRE", p["fire"]], ["SPEED", int(round((p["speed"] - E.BASE_SPEED) / E.SPEED_STEP)) + 1]]
		for k in stats.size():
			HudKit.text(self, Vector2(x + 20 + k * 66, y + 64), stats[k][0], 12, HudKit.MUTED, HudKit.label_font())
			HudKit.text(self, Vector2(x + 20 + k * 66, y + 94), str(stats[k][1]), 26, HudKit.INK if p["alive"] else HudKit.MUTED, HudKit.font(true))
		if p["kick"]:
			HudKit.text(self, Vector2(x + 262, y + 94), "KICK", 12, HudKit.GOLD, HudKit.label_font(), HudKit.RIGHT)
		if p["skull"] > 0.0:
			HudKit.text(self, Vector2(x + 262, y + 78), "CURSED", 12, Color(0.8, 0.4, 1.0), HudKit.label_font(), HudKit.RIGHT)
		if not p["alive"]:
			HudKit.text(self, Vector2(x + 140, y + 64), "OUT", 22, HudKit.BAD, HudKit.font(true), HudKit.CENTER)
	# the clock
	var left := maxi(0, int(ceil(e.map.time - e.time)))
	var hurry := e.sudden
	var ccol := HudKit.BAD if hurry else HudKit.INK
	HudKit.panel(self, Rect2(vp.x * 0.5 - 110, 16, 220, 70), ACCENT if not hurry else HudKit.BAD)
	if game.mode == "solo":
		HudKit.text(self, Vector2(vp.x * 0.5, 44), "STAGE %d   LIVES %d" % [game.stage + 1, game.lives], 16, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
		var foes := e.enemies.filter(func(x): return x["alive"]).size()
		HudKit.text(self, Vector2(vp.x * 0.5, 74), "EXIT OPEN" if e.exit_open else "%d TO GO" % foes, 24, HudKit.GOOD if e.exit_open else HudKit.INK, HudKit.font(true), HudKit.CENTER)
	else:
		HudKit.text(self, Vector2(vp.x * 0.5, 72), "HURRY!" if hurry else "%d:%02d" % [left / 60, left % 60], 34, ccol, HudKit.font(true), HudKit.CENTER)
	if _hurry_t >= 0.0 and _hurry_t < 2.2:
		var a := clampf(minf(_hurry_t * 5.0, (2.2 - _hurry_t) * 3.0), 0.0, 1.0)
		HudKit.banner(self, vp, vp.y * 0.42, "HURRY UP!", "THE ARENA IS CLOSING IN", HudKit.BAD, a, 1.0 + 0.3 * exp(-_hurry_t * 8.0))
	# countdown
	if game.countdown > 0.0:
		var n := ceili(game.countdown)
		var k := game.countdown - floorf(game.countdown)
		var title := e.map.name.to_upper() if game.mode == "battle" else "STAGE %d: %s" % [game.stage + 1, e.map.name.to_upper()]
		HudKit.banner(self, vp, vp.y * 0.42, str(n), title, ACCENT, 1.0, 1.0 + 0.4 * k)
	elif game.countdown > -0.6 and e.time < 0.6:
		HudKit.banner(self, vp, vp.y * 0.42, "GO!", "", HudKit.GOOD, clampf((0.6 - e.time) * 3.0, 0.0, 1.0))
	if _result != "":
		var a := clampf(_result_t * 4.0, 0.0, 1.0)
		HudKit.banner(self, vp, vp.y * 0.42, _result, "", HudKit.GOLD, a, 1.0 + 0.25 * exp(-_result_t * 8.0))
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 62, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 32), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)


func _draw_setup(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.02, 0.05, 0.6))
	var w := 720.0
	var r := Rect2(vp.x * 0.5 - w * 0.5, vp.y * 0.5 - 250, w, 470)
	HudKit.panel(self, r, ACCENT, 20, 0.95)
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 80), "BLASTYARD", 56, ACCENT, HudKit.font(true), HudKit.CENTER)
	var rows := [["MODE", "BATTLE" if game.mode == "battle" else "SOLO STAGES"],
		["PLAYERS", "%d  +  %d CPU" % [game.humans, 4 - game.humans] if game.mode == "battle" else "%d" % game.humans],
		["ARENA", "EVERY ARENA IN TURN" if game.arena_choice < 0 else game.arena_names[game.arena_choice].to_upper()],
		["", "START"]]
	var keys := ["mode", "humans", "arena", "start"]
	for i in rows.size():
		var y := r.position.y + 170 + i * 66
		var on: bool = game.setup_row() == keys[i]
		if on:
			draw_rect(Rect2(r.position.x + 40, y - 38, w - 80, 54), Color(ACCENT, 0.16))
			draw_rect(Rect2(r.position.x + 40, y - 38, w - 80, 54), ACCENT, false, 2.0)
		HudKit.text(self, Vector2(r.position.x + 70, y), rows[i][0], 18, HudKit.MUTED, HudKit.label_font())
		HudKit.text(self, Vector2(r.end.x - 70, y), ("<  %s  >" % rows[i][1]) if on and keys[i] != "start" else rows[i][1], 26,
			HudKit.GOLD if keys[i] == "start" else HudKit.INK, HudKit.font(true), HudKit.RIGHT if keys[i] != "start" else HudKit.RIGHT)
	HudKit.hints(self, Vector2(vp.x * 0.5, r.end.y + 44), [["UP / DOWN", "choose"], ["LEFT / RIGHT", "change"], ["ENTER", "play"]])
	var lines := "P1 ARROWS + SPACE    P2 W A S D + SHIFT    P3 I J K L + U    P4 NUMPAD 8 4 5 6 + 0    OR GAMEPADS"
	HudKit.text(self, Vector2(vp.x * 0.5, r.end.y + 90), lines, 14, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
