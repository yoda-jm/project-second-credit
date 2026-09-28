class_name InkHud
extends Control
## Inkstorm HUD: score and best, the land's name, lives, a ring of the land claimed against the target, the share of
## each claim popping where it was made (doubled for slow lines), READY, LAND CLAIMED, GAME OVER.

const ACCENT := Color(1.0, 0.75, 0.35)

@export var game: InkGame

var _pops: Array[Dictionary] = []  ## {text, pos (world), t, col}
var _t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.stage_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"claim":
			var region: Array = d["region"]
			var c := Vector2.ZERO
			var n := 0
			for cell in region:
				c += Vector2(cell)
				n += 1
			if n == 0:
				return
			var pct := float(d["cells"]) / ((InkEngine.W - 2) * (InkEngine.H - 2)) * 100.0
			_pops.append({"text": "+%.1f%%%s" % [pct, "  x2" if d["slow"] else ""], "pos": InkView3D.world(c / n, 0.6), "t": 0.0,
				"col": Color(0.6, 0.85, 1.0) if d["slow"] else HudKit.GOLD, "big": pct > 10.0, "size": clampf(26.0 + pct * 1.2, 28.0, 46.0)})
		"split":
			_pops.append({"text": "SPLIT  +2000", "pos": Vector3(0, 0.8, 0), "t": 0.0, "col": Color(0.8, 0.6, 1.0), "big": false, "size": 30.0})


func _process(delta: float) -> void:
	_t += delta
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < (2.4 if p["big"] else 1.8))
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), ACCENT)
	var land: String = InkView3D.LANDS[e.stage % InkView3D.LANDS.size()]["name"]
	HudKit.stat(self, vp.x - 48, 20, "STAGE %d  -  %s" % [game.stage + 1, land.to_upper()], "BEST %07d" % maxi(game.high, e.score),
		HudKit.INK, HudKit.RIGHT, 24)
	for i in mini(e.lives, 8):
		HudKit.gem(self, Vector2(48 + i * 26, 124), 9.0, ACCENT)
	# the claim ring, with the target marked
	var rc := Vector2(vp.x - 90, 170)
	HudKit.shade(self, rc, 58, 0.55)
	HudKit.ring(self, rc, 46, e.claimed / InkEngine.TARGET, HudKit.GOOD if e.claimed >= InkEngine.TARGET else ACCENT, 9.0)
	HudKit.text(self, rc + Vector2(0, 10), "%d%%" % int(e.claimed * 100.0), 30, HudKit.INK, HudKit.font(true), HudKit.CENTER)
	HudKit.text(self, rc + Vector2(0, 34), "OF %d%%" % int(InkEngine.TARGET * 100.0), 14, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	var cam: Camera3D = get_viewport().get_camera_3d()
	for p in _pops:
		if cam:
			# the share pops in with a springy overshoot, rises, shimmers, and fades
			var t: float = p["t"]
			var life := 2.4 if p["big"] else 1.8
			var pop := 1.0 - exp(-7.0 * t) * cos(11.0 * t)
			var sp := cam.unproject_position(p["pos"]) + Vector2(0, -30.0 * t - 14.0 * pop)
			var c: Color = p["col"]
			var a := clampf((life - t) / 0.5, 0.0, 1.0)
			var shimmer := 0.5 + 0.5 * sin(t * 14.0)
			var col := c.lerp(Color.WHITE, shimmer * 0.35 * a)
			var size := maxi(8, int(float(p["size"]) * maxf(pop, 0.05)))
			HudKit.text(self, sp, p["text"], size, Color(col, a), HudKit.font(true), HudKit.CENTER)
			if p["big"]:
				var bs := maxi(8, int(20.0 * maxf(1.0 - exp(-6.0 * (t - 0.15)) * cos(10.0 * (t - 0.15)), 0.05))) if t > 0.15 else 0
				if bs > 0:
					HudKit.text(self, sp + Vector2(0, -size * 1.05), "GRAND CLAIM!", bs, Color(Color.WHITE.lerp(c, shimmer), a),
						HudKit.label_font(), HudKit.CENTER)
	if e.phase == InkEngine.Phase.READY and e.time < 2.0:
		HudKit.banner(self, vp, vp.y * 0.45, "STAGE %d" % (game.stage + 1), land.to_upper(), ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif e.phase == InkEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.45, "LAND CLAIMED", "%d%%" % int(e.claimed * 100.0), HudKit.GOOD, 1.0)
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.5, "GAME OVER", "SCORE %d" % e.score, HudKit.BAD, 1.0)
		if not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.5 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
	elif not game.demo and e.stage == 0 and e.claimed < 0.06:
		# until the first claims, how to play
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 50), [["ARROWS", "move"], ["SPACE", "pen down, then step off the edge"], ["SHIFT", "draw slowly: x2"]])
	if not game.demo and game.pen and not e.drawing():
		var msg := "PEN DOWN  -  STEP OFF THE EDGE TO DRAW"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 110, wd, 44), HudKit.GOLD, 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 80), msg, 22, HudKit.GOLD, HudKit.label_font(), HudKit.CENTER)
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 62, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 32), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
