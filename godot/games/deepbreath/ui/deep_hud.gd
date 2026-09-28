class_name DeepHud
extends Control
## Deep Breath HUD: score and best, lives, the cavern's name, keys left, and the air supply: a long gauge that
## drains, turns red and pulses when it runs low; points popping at keys; the cavern card, LIFT OPEN, CAVERN CLEAR
## with the air bonus counting in, GAME OVER.

const ACCENT := Color(0.5, 0.85, 1.0)

@export var game: DeepGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _open_t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"key": _pops.append({"text": "100", "pos": DeepView3D.world(Vector2(d["cell"]) + Vector2(0.5, 0.2), 0.5), "t": 0.0})
		"open": _open_t = 2.0


func _process(delta: float) -> void:
	_t += delta
	_open_t = maxf(0.0, _open_t - delta)
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
	HudKit.stat(self, vp.x - 48, 20, "CAVERN %d  -  %s" % [game.index + 1, e.level.name.to_upper()], "BEST %07d" % maxi(game.high, e.score),
		HudKit.INK, HudKit.RIGHT, 24)
	for i in mini(e.lives, 8):
		HudKit.gem(self, Vector2(48 + i * 26, 124), 9.0, ACCENT)
	HudKit.text(self, Vector2(vp.x - 48, 136), "KEYS %d" % e.keys.size() if not e.open else "LIFT OPEN", 20,
		HudKit.GOLD if e.open else HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
	# the air gauge
	var w := minf(vp.x * 0.5, 720.0)
	var r := Rect2(vp.x * 0.5 - w * 0.5, vp.y - 44, w, 16)
	var f := clampf(e.air / e.level.air, 0.0, 1.0)
	var low := f < 0.25
	var col := HudKit.BAD if low else (HudKit.GOLD if f < 0.5 else Color(0.45, 0.9, 1.0))
	if low:
		col = col.lerp(Color.WHITE, 0.4 * (0.5 + 0.5 * sin(_t * 12.0)))
	draw_rect(r.grow(4), Color(0, 0, 0, 0.55))
	draw_rect(Rect2(r.position, Vector2(r.size.x * f, r.size.y)), col)
	draw_rect(Rect2(r.position + Vector2(r.size.x * f - 3, 0), Vector2(3, r.size.y)), Color(1, 1, 1, 0.7))
	HudKit.text(self, Vector2(r.position.x - 14, r.end.y), "AIR", 18, col, HudKit.label_font(), HudKit.RIGHT)
	var cam: Camera3D = get_viewport().get_camera_3d()
	for p in _pops:
		if cam:
			var sp := cam.unproject_position(p["pos"]) + Vector2(0, -44.0 * p["t"])
			HudKit.text(self, sp, p["text"], 24, Color(HudKit.GOLD, 1.0 - p["t"] / 1.2), HudKit.font(true), HudKit.CENTER)
	if e.phase == DeepEngine.Phase.READY and e.time < 1.7:
		HudKit.banner(self, vp, vp.y * 0.42, "CAVERN %d" % (game.index + 1), e.level.name.to_upper(), ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif _open_t > 0.0 and e.phase == DeepEngine.Phase.PLAY:
		HudKit.banner(self, vp, vp.y * 0.3, "LIFT OPEN", "", HudKit.GOLD, minf(1.0, _open_t), 1.0 + 0.2 * exp(-(2.0 - _open_t) * 6.0))
	elif e.phase == DeepEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.42, "CAVERN CLEAR", "AIR BONUS", HudKit.GOOD, 1.0)
	if game.over or e.phase == DeepEngine.Phase.OVER:
		HudKit.banner(self, vp, vp.y * 0.5, "GAME OVER", "SCORE %d" % e.score, HudKit.BAD, 1.0)
		if not game.demo and game.over:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.5 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
	elif not game.demo and e.phase == DeepEngine.Phase.READY and game.index == 0:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 80), [["ARROWS", "walk"], ["SPACE", "jump"]])
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 110, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 80), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
