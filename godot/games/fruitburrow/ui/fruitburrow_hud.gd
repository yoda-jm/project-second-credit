class_name FruitburrowHud
extends Control
## Fruitburrow HUD: garden and lives, fruit left, score, the ball, banners (ready, cleared, ouch, game over).

const P = FruitburrowEngine.Phase
const LEAF := Color(0.55, 1.0, 0.4)

@export var game: FruitburrowGame

var _t := 0.0
var _banner := ""
var _banner_sub := ""
var _banner_col := HudKit.GOLD
var _banner_t := 10.0
var _banner_len := 2.2
var _pops: Array[Dictionary] = []  ## floating score numbers: {text, pos (screen), t}


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.garden_started.connect(func(e):
		if not e.event.is_connected(_on_event):
			e.event.connect(_on_event)
		_show("GARDEN %d" % e.level, e.map.name.to_upper(), LEAF, e.READY_SECONDS))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"phase":
			if d["phase"] == P.PLAY:
				_show("GO!", "", LEAF, 0.7)
			elif d["phase"] == P.READY and game.engine.lives < FruitburrowEngine.LIVES:
				_show("READY", "%d %s LEFT" % [game.engine.lives, "LIFE" if game.engine.lives == 1 else "LIVES"], HudKit.GOLD, 2.0)
		"clear":
			_show("GARDEN CLEARED", "+%d BONUS" % FruitburrowEngine.SCORE_CLEAR, LEAF, 3.0)
		"death":
			_show("OUCH!", "", HudKit.BAD, 1.6)
		"game_over":
			_show("", "", HudKit.GOLD, 0.0)


func _show(text: String, sub: String, col: Color, secs: float) -> void:
	_banner = text
	_banner_sub = sub
	_banner_col = col
	_banner_t = 0.0
	_banner_len = secs


func _process(delta: float) -> void:
	_t += delta
	_banner_t += delta
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	# left: garden number and lives
	HudKit.panel(self, Rect2(24, 16, 360, 84), LEAF)
	HudKit.stat(self, 48, 20, "GARDEN", "%d" % e.level, HudKit.INK)
	HudKit.text(self, Vector2(360, 38), "LIVES", 15, HudKit.MUTED, HudKit.label_font(), HudKit.RIGHT)
	for i in FruitburrowEngine.LIVES:
		var c := Vector2(344 - i * 34, 72)
		var alive := i < e.lives
		_heart(c, 12.0, Color(1.0, 0.35, 0.4) if alive else Color(1, 1, 1, 0.15))
	# centre: fruit left and the ball
	HudKit.panel(self, Rect2(vp.x * 0.5 - 170, 16, 340, 84), Color(1.0, 0.45, 0.4))
	var left := e.fruit.size()
	HudKit.stat(self, vp.x * 0.5 - 30, 20, "FRUIT LEFT", "%d" % left, HudKit.INK, HudKit.CENTER)
	var frac := 1.0 - float(left) / maxf(1.0, float(e.fruit_total))
	draw_rect(Rect2(vp.x * 0.5 - 150, 90, 240, 3), Color(1, 1, 1, 0.1))
	draw_rect(Rect2(vp.x * 0.5 - 150, 90, 240 * frac, 3), Color(1.0, 0.45, 0.4))
	var bc := Vector2(vp.x * 0.5 + 120, 58)
	HudKit.text(self, bc + Vector2(0, -26), "BALL", 13, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
	if e.has_ball:
		draw_circle(bc + Vector2(0, 6), 11.0, HudKit.GOLD, true, -1.0, true)
		draw_circle(bc + Vector2(0, 6), 17.0, Color(HudKit.GOLD, 0.2), true, -1.0, true)
	else:
		var k := 1.0 - clampf(e.ball_regrow / FruitburrowEngine.BALL_REGROW, 0.0, 1.0) if e.ball.is_empty() else 0.0
		HudKit.ring(self, bc + Vector2(0, 6), 12.0, k, Color(HudKit.GOLD, 0.8), 4.0)
	# right: score
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), HudKit.GOLD)
	HudKit.stat(self, vp.x - 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.RIGHT)
	# banner
	if _banner != "" and _banner_t < _banner_len:
		var a := clampf(minf(_banner_t * 5.0, (_banner_len - _banner_t) * 4.0), 0.0, 1.0)
		var pop := 1.0 + 0.25 * exp(-_banner_t * 8.0)
		HudKit.banner(self, vp, vp.y * 0.44, _banner, _banner_sub, _banner_col, a, pop)
	# hints / demo
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var w := HudKit.width(msg, 24, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5, vp.y - 66, w, 46), Color(0, 0, 0, 0), 23, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 34), msg, 24, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	elif e.phase != P.GAME_OVER and e.level == 1 and e.time < 25.0:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 30), [["ARROWS", "dig and walk"], ["SPACE", "throw the ball"], ["ESC", "pause"]],
			clampf((25.0 - e.time) / 2.0, 0.0, 1.0))
	if e.phase == P.GAME_OVER:
		draw_rect(Rect2(Vector2.ZERO, vp), Color(0, 0, 0, 0.45))
		HudKit.banner(self, vp, vp.y * 0.45, "GAME OVER", "SCORE %d   -   GARDEN %d" % [e.score, e.level], HudKit.GOLD, 1.0)
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.45 + 150), [["ENTER", "play again"], ["ESC", "menu"]])


func _heart(c: Vector2, r: float, col: Color) -> void:
	var pts := PackedVector2Array()
	for i in 32:
		var t := TAU * i / 32.0
		var x := 16.0 * pow(sin(t), 3)
		var y := -(13.0 * cos(t) - 5.0 * cos(2 * t) - 2.0 * cos(3 * t) - cos(4 * t))
		pts.append(c + Vector2(x, y) * r / 16.0)
	draw_colored_polygon(pts, col)
