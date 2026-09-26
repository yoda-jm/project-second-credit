class_name HopHud
extends Control
## Hopline HUD: score and best, the stage, frogs left, the time bar, points popping where frogs reach home,
## READY, STAGE CLEAR, GAME OVER.

const ACCENT := Color(0.45, 0.9, 0.45)

@export var game: HopGame

var _pops: Array[Dictionary] = []
var _t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.stage_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"home":
			_pops.append({"text": "+%d" % (50 + d["time_bonus"]), "pos": HopView3D.cell(HopEngine.BAYS[d["bay"]], 0, 0.8), "t": 0.0, "col": HudKit.GOLD})
		"fly":
			_pops.append({"text": "FLY +200", "pos": HopView3D.cell(e.x, 0, 1.3), "t": 0.0, "col": Color(0.7, 1.0, 0.5)})
		"lady_home":
			_pops.append({"text": "LADY +200", "pos": HopView3D.cell(e.x, 0, 1.8), "t": 0.0, "col": Color(1.0, 0.6, 0.8)})


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
	# the time bar
	var w := minf(vp.x * 0.36, 520.0)
	var r := Rect2(vp.x * 0.5 - w * 0.5, vp.y - 40, w, 14)
	draw_rect(r.grow(3), Color(0, 0, 0, 0.5))
	var f := clampf(e.life_t / HopEngine.LIFE_TIME, 0.0, 1.0)
	var col := HudKit.GOOD if f > 0.33 else (HudKit.GOLD if f > 0.15 else HudKit.BAD)
	draw_rect(Rect2(r.position, Vector2(r.size.x * f, r.size.y)), col)
	HudKit.text(self, Vector2(r.position.x - 12, r.end.y), "TIME", 16, HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
	var cam: Camera3D = get_viewport().get_camera_3d()
	for p in _pops:
		if cam:
			var sp := cam.unproject_position(p["pos"]) + Vector2(0, -44.0 * p["t"])
			var c: Color = p["col"]
			HudKit.text(self, sp, p["text"], 28, Color(c, 1.0 - p["t"] / 1.4), HudKit.font(true), HudKit.CENTER)
	if e.phase == HopEngine.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.42, "READY", "STAGE %d" % (game.stage + 1) if e.time < 2.0 else "", ACCENT, 1.0, 1.0 + 0.08 * sin(_t * 8.0))
	elif e.phase == HopEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.42, "ALL HOME", "+1000", HudKit.GOOD, 1.0)
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.5, "GAME OVER", "SCORE %d" % e.score, HudKit.BAD, 1.0)
		if not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.5 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 110, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 80), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
