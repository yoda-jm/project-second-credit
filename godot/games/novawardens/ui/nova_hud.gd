class_name NovaHud
extends Control
## Nova Wardens HUD: score, hi-score, the wave, lives as little cannons, points popping where invaders fall (the
## mystery ship's score big), WAVE n, WAVE CLEAR, THE INVASION HAS LANDED, GAME OVER.

const ACCENT := Color(0.3, 1.0, 0.6)

@export var game: NovaGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _landed := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.game_started.connect(func(e):
		e.event.connect(_on_event)
		_landed = 0.0)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"hit":
			_pops.append({"text": str(d["points"]), "pos": NovaView3D.world(d["pos"], 0.3), "t": 0.0,
				"col": NovaView3D.COLORS[d["kind"]], "size": 20})
		"ufo_hit":
			_pops.append({"text": str(d["points"]), "pos": NovaView3D.world(d["pos"], 0.3), "t": -0.6,
				"col": Color(1.0, 0.5, 0.4), "size": 40})
		"extra_life":
			_pops.append({"text": "1UP", "pos": NovaView3D.world(Vector2(112, 200), 0.3), "t": 0.0, "col": ACCENT, "size": 34})
		"land":
			_landed = 3.0


func _process(delta: float) -> void:
	_t += delta
	_landed = maxf(0.0, _landed - delta)
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.0)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "SCORE", "%05d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "WAVE %d" % (e.wave + 1), "HI %05d" % maxi(game.high, e.score), HudKit.INK, HudKit.RIGHT, 24)
	# lives: little cannons
	for i in mini(e.lives, 8):
		var c := Vector2(52 + i * 34, 124)
		draw_rect(Rect2(c + Vector2(-12, -3), Vector2(24, 8)), ACCENT)
		draw_rect(Rect2(c + Vector2(-2, -10), Vector2(4, 8)), ACCENT)
	var cam := get_viewport().get_camera_3d()
	for p in _pops:
		if p["t"] < 0.0 or cam == null or cam.is_position_behind(p["pos"]):
			continue
		var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 40.0)
		var a := clampf(1.0 - p["t"], 0.0, 1.0)
		var col: Color = p["col"]
		HudKit.text(self, sp, p["text"], p["size"], Color(col, a), HudKit.font(true), HudKit.CENTER)
	if e.phase == NovaEngine.Phase.READY and e.lives > 0:
		HudKit.banner(self, vp, vp.y * 0.42, "WAVE %d" % (e.wave + 1), "DEFEND THE COAST", ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif e.phase == NovaEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.42, "WAVE CLEAR", "THE NEXT FLEET COMES LOWER", HudKit.GOLD, clampf((2.5 - e.phase_t) * 3.0, 0.0, 1.0))
	if _landed > 0.0:
		HudKit.banner(self, vp, vp.y * 0.3, "THE INVASION HAS LANDED", "", HudKit.BAD, minf(1.0, _landed))
	elif game.over or e.phase == NovaEngine.Phase.OVER:
		HudKit.banner(self, vp, vp.y * 0.42, "GAME OVER", "PRESS ENTER" if not game.demo else "", HudKit.BAD, 1.0)
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 30), "DEMO  -  PRESS ANY KEY TO PLAY", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
