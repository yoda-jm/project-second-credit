class_name KnucklesHud
extends Control
## Neon Knuckles HUD: each player's health and lives, the score, the enemy just hit, "GO" when the street opens,
## stage banners.

const B = preload("res://games/knuckles/engine/brawl_engine.gd")
const PINK := Color(1.0, 0.3, 0.65)
const CYAN := Color(0.3, 0.9, 1.0)
const P_COL: Array[Color] = [Color(0.35, 0.6, 1.0), Color(1.0, 0.35, 0.35)]
const NAMES := {"thug": "THUG", "knifer": "KNIFE", "bruiser": "BRUISER", "boss": "THE BOSS"}

@export var game: KnucklesGame

var _banner := ""
var _sub := ""
var _col := PINK
var _t := 10.0
var _len := 2.5
var _go_t := 10.0
var _foe := -1
var _foe_t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.stage_started.connect(func(e):
		e.event.connect(_on_event)
		_show("STAGE %d" % (game.stage + 1), e.level.name.to_upper(), PINK, 2.8))
	game.run_over.connect(func(won): _show("THE CITY IS YOURS" if won else "GAME OVER", "SCORE %d" % game.engine.score,
		HudKit.GOLD if won else HudKit.BAD, 99.0))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"go": _go_t = 0.0
		"hit":
			var t := game.engine.by_id(d["target"])
			if not t.is_empty() and t["player"] < 0:
				_foe = d["target"]
				_foe_t = 3.0
		"stage_clear": _show("STAGE CLEAR", "", HudKit.GOOD, 3.5)
		"player_down": _show("DOWN!", "%d LIVES LEFT" % d["lives"], HudKit.BAD, 1.5)


func _show(text: String, sub: String, col: Color, secs: float) -> void:
	_banner = text
	_sub = sub
	_col = col
	_t = 0.0
	_len = secs


func _process(delta: float) -> void:
	_t += delta
	_go_t += delta
	_foe_t -= delta
	queue_redraw()


func _bar(r: Rect2, frac: float, col: Color) -> void:
	draw_rect(r, Color(0, 0, 0, 0.5))
	draw_rect(Rect2(r.position, Vector2(r.size.x * clampf(frac, 0.0, 1.0), r.size.y)), col)
	draw_rect(Rect2(r.position, Vector2(r.size.x * clampf(frac, 0.0, 1.0), r.size.y * 0.35)), Color(1, 1, 1, 0.25))


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	var ps := e.players()
	for i in 2:
		var x := 24.0 if i == 0 else vp.x - 444.0
		HudKit.panel(self, Rect2(x, 16, 420, 90), P_COL[i])
		if i < ps.size():
			var p: Dictionary = ps[i]
			HudKit.text(self, Vector2(x + 24, 44), "PLAYER %d" % (i + 1), 16, HudKit.MUTED, HudKit.label_font())
			_bar(Rect2(x + 24, 56, 280, 18), float(p["hp"]) / float(p["max_hp"]), P_COL[i])
			for k in p["lives"]:
				draw_circle(Vector2(x + 330 + k * 26, 65), 9, P_COL[i], true, -1.0, true)
		else:
			HudKit.text(self, Vector2(x + 210, 68), "PLAYER 2: PRESS F TO JOIN", 20, Color(HudKit.INK, 0.5 + 0.5 * sin(_t * 4.0)), HudKit.label_font(), HudKit.CENTER)
	HudKit.panel(self, Rect2(vp.x * 0.5 - 150, 16, 300, 90), HudKit.GOLD)
	HudKit.stat(self, vp.x * 0.5, 22, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.CENTER)
	# the enemy just hit
	if _foe_t > 0.0:
		var f := e.by_id(_foe)
		if not f.is_empty():
			HudKit.text(self, Vector2(vp.x * 0.5 - 200, 150), NAMES.get(f["kind"], "ENEMY"), 20, PINK, HudKit.font(true))
			_bar(Rect2(vp.x * 0.5 - 200, 160, 400, 12), float(maxi(0, f["hp"])) / float(f["max_hp"]), PINK)
	# GO!
	if _go_t < 3.0 and fmod(_go_t, 0.5) < 0.32:
		HudKit.text(self, Vector2(vp.x - 200, vp.y * 0.45), "GO", 90, CYAN, HudKit.font(true), HudKit.CENTER)
		var c := Vector2(vp.x - 90, vp.y * 0.45 - 30)
		draw_colored_polygon(PackedVector2Array([c + Vector2(-30, -35), c + Vector2(30, 0), c + Vector2(-30, 35)]), CYAN)
	if _banner != "" and _t < _len:
		var a := clampf(minf(_t * 5.0, (_len - _t) * 4.0), 0.0, 1.0)
		HudKit.banner(self, vp, vp.y * 0.42, _banner, _sub, _col, a, 1.0 + 0.25 * exp(-_t * 8.0))
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var w := HudKit.width(msg, 24, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5, vp.y - 66, w, 46), Color(0, 0, 0, 0), 23, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 34), msg, 24, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	elif e.time < 20.0 and game.stage == 0:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 30), [["ARROWS", "move"], ["SPACE", "attack"], ["X", "jump"],
			["TOWARD + SPACE", "grab a dazed foe"], ["BACK + SPACE", "elbow"]], clampf((20.0 - e.time) / 2.0, 0.0, 1.0))
	if game.over:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.42 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
