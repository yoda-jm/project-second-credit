class_name FuseHud
extends Control
## Fuseflight HUD: score and best, lives, the stage's name, fireworks left and lit ones taken, the power's countdown,
## points popping where fireworks are taken and enemies eaten, the stage card, STAGE CLEAR with the lit bonus,
## GAME OVER, and the controls for a new player.

const ACCENT := Color(1.0, 0.7, 0.35)

@export var game: FuseGame

var _pops: Array[Dictionary] = []
var _t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.stage_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"take":
			var p: Vector2 = d["pos"]
			_pops.append({"text": str(d["points"]), "pos": Vector3(p.x, p.y + 0.5, 0.3), "t": 0.0,
				"col": HudKit.GOLD if d["lit"] else HudKit.INK, "size": 26 if d["lit"] else 20})
		"eat":
			var p: Vector2 = d["pos"]
			_pops.append({"text": str(d["points"]), "pos": Vector3(p.x, p.y + 0.5, 0.3), "t": 0.0, "col": Color(1.0, 0.9, 0.5), "size": 26})
		"letter":
			var p: Vector2 = game.engine.hero["pos"]
			_pops.append({"text": "EXTRA LIFE" if d["kind"] == "E" else "BONUS 2000", "pos": Vector3(p.x, p.y + 1.2, 0.3), "t": 0.0,
				"col": Color(0.6, 0.9, 1.0), "size": 24})


func _process(delta: float) -> void:
	_t += delta
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
	HudKit.stat(self, 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "STAGE %d  -  %s" % [game.index + 1, e.stage.name.to_upper()],
		"BEST %07d" % maxi(game.high, e.score), HudKit.INK, HudKit.RIGHT, 24)
	for i in mini(e.lives, 8):
		HudKit.gem(self, Vector2(48 + i * 26, 124), 9.0, ACCENT)
	HudKit.text(self, Vector2(vp.x - 48, 136), "FIREWORKS %d   LIT %d" % [e.left(), e.lit_taken], 18, HudKit.INK,
		HudKit.label_font(), HudKit.RIGHT)
	if e.power > 0.0:
		var col := HudKit.GOLD.lerp(Color.WHITE, 0.4 * (0.5 + 0.5 * sin(_t * 12.0)))
		HudKit.text(self, Vector2(vp.x * 0.5, 60), "POWER  %.1f" % e.power, 30, col, HudKit.font(true), HudKit.CENTER)
	var cam := get_viewport().get_camera_3d()
	for p in _pops:
		if cam == null or cam.is_position_behind(p["pos"]):
			continue
		var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 50.0)
		var c: Color = p["col"]
		HudKit.text(self, sp, p["text"], p["size"], Color(c, clampf(1.0 - p["t"], 0.0, 1.0)), HudKit.font(true), HudKit.CENTER)
	if e.phase == FuseEngine.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.36, "STAGE %d" % (game.index + 1), e.stage.name.to_upper(), ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif e.phase == FuseEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.36, "STAGE CLEAR", "%d LIT  -  BONUS" % e.lit_taken, HudKit.GOLD, clampf((3.0 - e.phase_t) * 3.0, 0.0, 1.0))
	elif game.over or e.phase == FuseEngine.Phase.OVER:
		HudKit.banner(self, vp, vp.y * 0.42, "GAME OVER", "PRESS ENTER" if not game.demo else "", HudKit.BAD, 1.0)
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 30), "DEMO  -  PRESS ANY KEY TO PLAY", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	elif e.time < 8.0 and game.index == 0:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 50), [["ARROWS", "run"], ["SPACE", "leap (hold: higher, glide)"]])
