class_name PrismHud
extends Control
## Prism Breaker HUD: score and best, the wall's number and name, lives, the power in use, capsule names popping at
## the paddle, the wall's title before the serve, STAGE CLEAR, BREAK OUT, GAME OVER.

const ACCENT := Color(0.35, 0.8, 1.0)
const POWER_NAMES := {"wide": "WIDE", "laser": "LASER", "catch": "CATCH", "slow": "SLOW", "multi": "MULTI BALL",
	"life": "EXTRA LIFE", "break": "BREAK OUT"}

@export var game: PrismGame

var _pops: Array[Dictionary] = []  ## {text, pos (world), t, col}
var _t := 0.0
var _warped := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.stage_started.connect(func(e):
		_warped = false
		e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"capsule":
			_pops.append({"text": POWER_NAMES[d["kind"]], "pos": PrismView3D.W(Vector2(e.paddle_x, PrismEngine.PADDLE_Y - 0.8)), "t": 0.0,
				"col": PrismView3D.CAPSULES[d["kind"]][1].lightened(0.3)})
		"drone_pop":
			_pops.append({"text": "100", "pos": PrismView3D.W(d["pos"]), "t": 0.0, "col": Color(1.0, 0.6, 0.95)})
		"warp":
			_warped = true



func _process(delta: float) -> void:
	_t += delta
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.3)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "WALL %d  -  %s" % [game.stage + 1, e.level.name.to_upper()], "BEST %07d" % maxi(game.high, e.score),
		HudKit.INK, HudKit.RIGHT, 24)
	for i in mini(e.lives, 8):
		HudKit.gem(self, Vector2(48 + i * 26, 124), 9.0, ACCENT)
	if e.power != "" and e.power != "life":
		var msg: String = POWER_NAMES[e.power]
		HudKit.text(self, Vector2(vp.x - 48, 136), msg, 24, PrismView3D.CAPSULES[e.power][1].lightened(0.35), HudKit.label_font(), HudKit.RIGHT)
	var cam: Camera3D = get_viewport().get_camera_3d()
	for p in _pops:
		if cam:
			var sp := cam.unproject_position(p["pos"]) + Vector2(0, -50.0 * p["t"])
			var c: Color = p["col"]
			HudKit.text(self, sp, p["text"], 26, Color(c, 1.0 - p["t"] / 1.3), HudKit.font(true), HudKit.CENTER)
	if e.phase == PrismEngine.Phase.SERVE and e.time < 2.2 and e.lives > 0:
		var a := clampf((2.2 - e.time) * 2.0, 0.0, 1.0)
		HudKit.banner(self, vp, vp.y * 0.46, "WALL %d" % (game.stage + 1), e.level.name.to_upper(), ACCENT, a)
	elif e.phase == PrismEngine.Phase.SERVE and not game.demo:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.62), [["SPACE", "launch"], ["MOUSE", "move"]], 0.6 + 0.4 * sin(_t * 4.0))
	elif e.phase == PrismEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.46, "BREAK OUT" if _warped else "WALL CLEAR", "+10000" if _warped else "", HudKit.GOOD, 1.0)
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.5, "GAME OVER", "SCORE %d" % e.score, HudKit.BAD, 1.0)
		if not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.5 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 62, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 32), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
