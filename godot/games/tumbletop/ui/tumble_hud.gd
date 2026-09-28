class_name TumbleHud
extends Control
## Tumbletop HUD: score and best, lives, the level's name and round, the colour to change the cubes to (with the
## steps on two-step levels), cubes left, points popping over the pyramid, FREEZE with its countdown, ROUND CLEAR
## with the bonus, GAME OVER, and a small compass of the four hops for new players.

const ACCENT := Color(1.0, 0.7, 0.3)

@export var game: TumbleGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _hint := 1.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event.bind(e)))


func _hero_world(e: TumbleEngine) -> Vector3:
	return TumbleEngine.cube3(e.hero_cell()) + Vector3(0, 1.2, 0)


func _on_event(kind: String, d: Dictionary, e: TumbleEngine) -> void:
	match kind:
		"lure": _pops.append({"text": "500", "pos": _hero_world(e), "t": 0.0, "col": HudKit.GOLD})
		"catch": _pops.append({"text": "300", "pos": _hero_world(e), "t": 0.0, "col": Color(0.5, 1.0, 0.5)})
		"freeze": _pops.append({"text": "FREEZE!", "pos": _hero_world(e), "t": 0.0, "col": Color(0.5, 1.0, 0.6)})
		"extra_life": _pops.append({"text": "1UP", "pos": _hero_world(e), "t": 0.0, "col": Color(1.0, 0.5, 0.8)})


func _process(delta: float) -> void:
	_t += delta
	_hint = maxf(0.0, _hint - delta)
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.3)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	var theme: Dictionary = TumbleView3D.THEMES[e.level % TumbleView3D.THEMES.size()]
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "LEVEL %d  ROUND %d  -  %s" % [e.level + 1, e.round + 1, str(theme["name"]).to_upper()],
		"BEST %07d" % maxi(game.high, e.score), HudKit.INK, HudKit.RIGHT, 24)
	for i in mini(e.lives, 8):
		HudKit.gem(self, Vector2(48 + i * 26, 124), 9.0, ACCENT)
	# the colour to reach
	var tops: Array = theme["tops"]
	var x := vp.x - 48.0
	var y := 132.0
	var steps: Array = [tops[0], tops[2]] if e.target() == 1 else [tops[0], tops[1], tops[2]]
	for i in range(steps.size() - 1, -1, -1):
		var r := Rect2(x - 30, y - 14, 30, 30)
		draw_rect(r.grow(3), Color(0, 0, 0, 0.5))
		draw_rect(r, steps[i])
		if i == steps.size() - 1:
			draw_rect(r.grow(5), Color(1, 1, 1, 0.5 + 0.5 * sin(_t * 5.0)), false, 2.0)
		x -= 42.0
		if i > 0:
			HudKit.text(self, Vector2(x + 6, y + 8), ">", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
			x -= 12.0
	HudKit.text(self, Vector2(vp.x - 48, y + 44), "%d TO GO" % e.remaining() + ("   UNDO!" if e.rule["undo"] else ""), 18,
		HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
	var cam := get_viewport().get_camera_3d()
	for p in _pops:
		if cam == null or cam.is_position_behind(p["pos"]):
			continue
		var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 50.0)
		var a := clampf(1.3 - p["t"], 0.0, 1.0)
		var col: Color = p["col"]
		HudKit.text(self, sp, p["text"], 30, Color(col, a), HudKit.font(true), HudKit.CENTER)
	if e.frozen > 0.0:
		HudKit.text(self, Vector2(vp.x * 0.5, 150), "FROZEN  %.1f" % e.frozen, 28, Color(0.5, 1.0, 0.6), HudKit.font(true), HudKit.CENTER)
	if e.phase == TumbleEngine.Phase.READY and e.round_time == 0.0:
		HudKit.banner(self, vp, vp.y * 0.3, "ROUND %d" % (e.round + 1), "LEVEL %d  -  %s" % [e.level + 1, str(theme["name"]).to_upper()],
			ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif e.phase == TumbleEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.3, "ROUND CLEAR", "BONUS %d" % (1000 + 250 * (e.level * TumbleEngine.ROUNDS + e.round)), tops[2],
			clampf((3.0 - e.phase_t) * 3.0, 0.0, 1.0))
	elif e.phase == TumbleEngine.Phase.OVER or game.over:
		HudKit.banner(self, vp, vp.y * 0.42, "GAME OVER", "PRESS ENTER" if not game.demo else "", HudKit.BAD, 1.0)
	# how to hop: a card that stays up until the first hop, then fades
	if not game.hopped:
		_hint = 1.0
	if _hint > 0.0 and not game.demo:
		var a := clampf(_hint, 0.0, 1.0)
		var c := Vector2(vp.x * 0.5, vp.y - 180) if not game.hopped else Vector2(170, vp.y - 150)
		if not game.hopped:
			HudKit.panel(self, Rect2(c.x - 250, c.y - 110, 500, 250), HudKit.GOLD, 16, 0.85)
			HudKit.text(self, c + Vector2(0, -78), "HOP DIAGONALLY", 26, HudKit.GOLD, HudKit.font(true), HudKit.CENTER)
		for k in [["UP + LEFT", "Q", Vector2(-1, -1)], ["UP + RIGHT", "E", Vector2(1, -1)], ["DOWN + LEFT", "Z", Vector2(-1, 1)],
				["DOWN + RIGHT", "C", Vector2(1, 1)]]:
			var at: Vector2 = c + (k[2] as Vector2) * Vector2(92.0, 56.0)
			draw_line(c, c + (k[2] as Vector2) * 30.0, Color(1, 1, 1, 0.5 * a), 3.0)
			HudKit.text(self, at + Vector2(0, 2), k[0], 16, Color(HudKit.GOLD, a), HudKit.label_font(), HudKit.CENTER)
			HudKit.text(self, at + Vector2(0, 22), "or " + k[1], 14, Color(HudKit.INK, a * 0.8), HudKit.label_font(), HudKit.CENTER)
		HudKit.text(self, c + Vector2(0, 110), "press two arrows together  -  or click a cube", 16, Color(HudKit.INK, a * 0.8),
			HudKit.label_font(), HudKit.CENTER)
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 30), "DEMO  -  PRESS ANY KEY TO PLAY", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
