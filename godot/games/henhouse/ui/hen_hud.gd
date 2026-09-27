class_name HenHud
extends Control
## Henhouse Heist HUD: score and best, lives, the level, eggs left, the time bonus counting down (it pauses, glowing,
## while grain holds the clock), points popping, the level card, LEVEL CLEAR with the bonus, GAME OVER.

const ACCENT := Color(1.0, 0.78, 0.35)

@export var game: HenGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _bonus := 0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"egg": _pops.append({"text": "100", "pos": HenView3D.world(Vector2(d["cell"]) + Vector2(0.5, 0.0), 0.4), "t": 0.0})
		"grain": _pops.append({"text": "50  CLOCK STOPS", "pos": HenView3D.world(Vector2(d["cell"]) + Vector2(0.5, 0.0), 0.4), "t": 0.0})
		"cleared": _bonus = d["bonus"]


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
	var vp := size
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "LEVEL %d  -  %s" % [game.index + 1, e.level.name.to_upper()], "BEST %07d" % maxi(game.high, e.score),
		HudKit.INK, HudKit.RIGHT, 24)
	for i in mini(e.lives, 8):
		HudKit.gem(self, Vector2(48 + i * 26, 124), 9.0, ACCENT)
	HudKit.text(self, Vector2(vp.x - 48, 136), "EGGS %d" % e.eggs.size(), 20, HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
	# the time bonus
	var w := minf(vp.x * 0.3, 420.0)
	var r := Rect2(vp.x * 0.5 - w * 0.5, 30, w, 12)
	draw_rect(r.grow(3), Color(0, 0, 0, 0.5))
	var f := clampf(e.clock / e.level.time_limit, 0.0, 1.0)
	var col := Color(0.6, 0.9, 1.0) if e.freeze > 0.0 else (HudKit.GOOD if f > 0.3 else (HudKit.GOLD if f > 0.15 else HudKit.BAD))
	draw_rect(Rect2(r.position, Vector2(r.size.x * f, r.size.y)), col)
	HudKit.text(self, Vector2(vp.x * 0.5, 70), "BONUS %d%s" % [int(e.clock) * 10, "   CLOCK STOPPED" if e.freeze > 0.0 else ""], 16, col, HudKit.label_font(), HudKit.CENTER)
	var cam: Camera3D = get_viewport().get_camera_3d()
	for p in _pops:
		if cam:
			var sp := cam.unproject_position(p["pos"]) + Vector2(0, -40.0 * p["t"])
			HudKit.text(self, sp, p["text"], 22, Color(HudKit.GOLD, 1.0 - p["t"] / 1.3), HudKit.font(true), HudKit.CENTER)
	if e.phase == HenEngine.Phase.READY and e.time < 1.6:
		HudKit.banner(self, vp, vp.y * 0.42, "LEVEL %d" % (game.index + 1), e.level.name.to_upper(), ACCENT, 1.0)
	elif e.phase == HenEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.42, "LEVEL CLEAR", "TIME BONUS %d" % _bonus, HudKit.GOOD, 1.0)
	if game.over or e.phase == HenEngine.Phase.OVER:
		HudKit.banner(self, vp, vp.y * 0.5, "GAME OVER", "SCORE %d" % e.score, HudKit.BAD, 1.0)
		if not game.demo and game.over:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.5 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 62, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 32), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
