class_name TunnelHud
extends Control
## Tunnel Pop HUD: score and best, lives, the level, points popping where creatures burst and get crushed (and the
## vegetable's), ROUND n at the start, a hurry when the last one runs, LEVEL CLEAR, GAME OVER, the keys at first.

const D = preload("res://games/tunnelpop/engine/pop_dig_engine.gd")
const ACCENT := Color(1.0, 0.72, 0.3)

@export var game: TunnelGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _last := 0.0
var _moved := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"pop", "crush":
			var p: Vector2 = d.get("pos", game.engine.hero["pos"])
			_pops.append({"text": str(d["points"]), "pos": Vector3(p.x, -p.y + 0.6, 0.6), "t": 0.0, "col": HudKit.GOLD if kind == "crush" else HudKit.INK, "size": 26 if kind == "crush" else 22})
		"veg_take":
			var p: Vector2 = d["pos"]
			_pops.append({"text": str(d["points"]), "pos": Vector3(p.x, -p.y + 0.6, 0.6), "t": 0.0, "col": Color(0.5, 1.0, 0.5), "size": 30})
		"last":
			_last = 2.0
		"dig":
			_moved = true


func _process(delta: float) -> void:
	_t += delta
	_last = maxf(0.0, _last - delta)
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.2)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "ROUND %d" % (e.level + 1), "BEST %07d" % maxi(game.high, e.score), HudKit.INK, HudKit.RIGHT, 24)
	for i in mini(e.lives, 8):
		HudKit.gem(self, Vector2(48 + i * 26, 124), 9.0, ACCENT)
	# the creatures left: the goal, always in view
	var left := e.foes.filter(func(f): return not f["dead"]).size()
	HudKit.panel(self, Rect2(vp.x * 0.5 - 140, 14, 280, 56), ACCENT)
	HudKit.text(self, Vector2(vp.x * 0.5, 50), "CREATURES LEFT  %d" % left, 22, HudKit.INK, HudKit.font(true), HudKit.CENTER)
	var cam := get_viewport().get_camera_3d()
	if cam:
		for p in _pops:
			var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 40.0)
			var c: Color = p["col"]
			HudKit.text(self, sp, p["text"], p["size"], Color(c, clampf(1.2 - p["t"], 0.0, 1.0)), HudKit.font(true), HudKit.CENTER)
	if e.phase == D.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.3, "ROUND %d" % (e.level + 1), "PLAYER 1 READY", ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif e.phase == D.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.3, "ROUND CLEAR", "", HudKit.GOLD, clampf((3.0 - e.phase_t) * 3.0, 0.0, 1.0))
	elif _last > 0.0:
		HudKit.banner(self, vp, vp.y * 0.3, "THE LAST ONE RUNS!", "", HudKit.BAD, minf(1.0, _last))
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.42, "GAME OVER", "PRESS ENTER" if not game.demo else "", HudKit.BAD, 1.0)
	elif not _moved and not game.demo and e.level == 0 and e.phase in [D.Phase.READY, D.Phase.PLAY]:
		# what to do, until the first dig
		var r := Rect2(vp.x * 0.5 - 330, vp.y - 196, 660, 110)
		HudKit.panel(self, r, ACCENT)
		HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 36), "POP EVERY CREATURE TO CLEAR THE ROUND", 22, HudKit.GOLD, HudKit.font(true), HudKit.CENTER)
		HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 66), "dig a tunnel to one, face it and tap the pump four times", 17, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
		HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 92), "or dig under a rock to drop it on them  -  don't let them touch you", 17, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 50), [["ARROWS", "DIG"], ["SPACE", "PUMP (TAP OR HOLD)"]])
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 14), "DEMO  -  PRESS ANY KEY TO PLAY", 18, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
