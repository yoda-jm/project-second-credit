class_name NightHud
extends Control
## Nightbite HUD: score and best, the stage, lives, points popping where spirits and gems are eaten, READY, GAME OVER.

const ACCENT := Color(0.75, 0.45, 1.0)

@export var game: NightGame

var _pops: Array[Dictionary] = []  ## {text, pos (world), t}
var _t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.stage_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"eat_spirit": _pops.append({"text": str(d["points"]), "pos": Vector3(d["pos"].x, 0.5, d["pos"].y), "t": 0.0})
		"bonus_eat":
			var b: Vector2i = game.engine.maze.bonus
			_pops.append({"text": str(d["points"]), "pos": Vector3(b.x + 0.5, 0.5, b.y + 0.5), "t": 0.0})


func _process(delta: float) -> void:
	_t += delta
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.2)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "STAGE %d  -  %s" % [game.stage + 1, e.maze.name.to_upper()], "BEST %07d" % maxi(game.high, e.score), HudKit.INK, HudKit.RIGHT, 24)
	for i in e.lives:
		HudKit.gem(self, Vector2(48 + i * 26, 124), 9.0, Color(1.0, 0.75, 0.35))
	var cam: Camera3D = get_viewport().get_camera_3d()
	for p in _pops:
		if cam:
			var sp := cam.unproject_position(p["pos"]) + Vector2(0, -40.0 * p["t"])
			HudKit.text(self, sp, p["text"], 26, Color(0.4, 0.95, 1.0, 1.0 - p["t"] / 1.2), HudKit.font(true), HudKit.CENTER)
	if e.phase == NightEngine.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.5, "READY", "", HudKit.GOLD, 1.0, 1.0 + 0.1 * sin(_t * 8.0))
	elif e.phase == NightEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.5, "STAGE CLEAR", "", HudKit.GOOD, 1.0)
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.5, "GAME OVER", "SCORE %d" % e.score, HudKit.BAD, 1.0)
		if not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.5 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 62, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 32), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
