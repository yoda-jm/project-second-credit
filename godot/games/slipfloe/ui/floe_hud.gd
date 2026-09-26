class_name FloeHud
extends Control
## Slipfloe HUD: score and best, the stage, otters left, mites and eggs still to go, points popping where mites are
## crushed, READY, the gem bonus, STAGE CLEAR with the time bonus, GAME OVER.

const ACCENT := Color(0.45, 0.85, 1.0)

@export var game: FloeGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _bonus := 0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.stage_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"crush":
			_pops.append({"text": str(d["points"]), "pos": FloeView3D.cell(d["pos"], 1.0), "t": 0.0, "col": HudKit.GOLD})
		"stomp":
			_pops.append({"text": "100", "pos": FloeView3D.cell(d["pos"], 0.9), "t": 0.0, "col": HudKit.INK})
		"shatter":
			if d.get("egg", false):
				_pops.append({"text": "500", "pos": FloeView3D.cell(Vector2(d["cell"]), 1.0), "t": 0.0, "col": Color(1.0, 0.8, 0.5)})
		"gems":
			_pops.append({"text": "GEMS  +%d" % d["points"], "pos": Vector3(0, 1.5, 0), "t": 0.0, "col": Color(0.6, 1.0, 1.0)})
		"cleared":
			_bonus = d["bonus"]


func _process(delta: float) -> void:
	_t += delta
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.4)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "STAGE %d" % (game.stage + 1), "BEST %07d" % maxi(game.high, e.score), HudKit.INK, HudKit.RIGHT, 24)
	for i in mini(e.lives, 8):
		HudKit.gem(self, Vector2(48 + i * 26, 124), 9.0, ACCENT)
	# mites and eggs left, as a row of dots
	var left := e.mites.size() + e.eggs.size()
	HudKit.text(self, Vector2(vp.x - 48, 136), "MITES %d" % left, 20, HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
	var cam: Camera3D = get_viewport().get_camera_3d()
	for p in _pops:
		if cam:
			var sp := cam.unproject_position(p["pos"]) + Vector2(0, -44.0 * p["t"])
			var c: Color = p["col"]
			HudKit.text(self, sp, p["text"], 28, Color(c, 1.0 - p["t"] / 1.4), HudKit.font(true), HudKit.CENTER)
	if e.phase == FloeEngine.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.42, "READY", "STAGE %d" % (game.stage + 1) if e.time < 2.0 else "", ACCENT, 1.0, 1.0 + 0.08 * sin(_t * 8.0))
	elif e.phase == FloeEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.42, "STAGE CLEAR", "TIME BONUS  %d" % _bonus if _bonus > 0 else "", HudKit.GOOD, 1.0)
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.5, "GAME OVER", "SCORE %d" % e.score, HudKit.BAD, 1.0)
		if not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.5 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
	elif not game.demo and e.phase == FloeEngine.Phase.READY and game.stage == 0:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 50), [["ARROWS", "walk"], ["SPACE", "push / shake the wall"]])
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 62, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 32), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
