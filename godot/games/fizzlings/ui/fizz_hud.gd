class_name FizzHud
extends Control
## Fizzlings HUD: each hero's score and lives (hero 2 on the right, or a "press W to join" hint), the level and best,
## points popping from chains and treats, HURRY UP, READY, LEVEL CLEAR, GAME OVER.

const P_COL := [Color(1.0, 0.62, 0.72), Color(0.6, 0.7, 1.0)]

@export var game: FizzGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _hurry_t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"treat":
			_pops.append({"text": str(d["points"]), "pos": FizzView3D.world(d["pos"], 0.5), "t": 0.0, "col": P_COL[d["p"]]})
		"pop":
			if d["trapped"] and d["n"] > 0:
				_pops.append({"text": "x%d" % (d["n"] + 1), "pos": FizzView3D.world(d["pos"], 0.5), "t": 0.0, "col": HudKit.GOLD})
		"hurry":
			_hurry_t = 2.5


func _process(delta: float) -> void:
	_t += delta
	_hurry_t = maxf(0.0, _hurry_t - delta)
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.2)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	for i in 2:
		var x := 24.0 if i == 0 else vp.x - 324.0
		HudKit.panel(self, Rect2(x, 16, 300, 84), P_COL[i])
		if i < e.heroes.size():
			var h: Dictionary = e.heroes[i]
			HudKit.stat(self, x + (24 if i == 0 else 276), 20, "PLAYER %d" % (i + 1), "%07d" % h["score"], HudKit.GOLD, HudKit.LEFT if i == 0 else HudKit.RIGHT)
			for l in mini(h["lives"], 8):
				HudKit.gem(self, Vector2(x + 24 + l * 26 if i == 0 else x + 276 - l * 26, 124), 9.0, P_COL[i])
		else:
			HudKit.text(self, Vector2(x + 150, 66), "W / F  TO JOIN" if not game.demo else "", 20, Color(HudKit.INK, 0.7), HudKit.label_font(), HudKit.CENTER)
	HudKit.text(self, Vector2(vp.x * 0.5, 44), "LEVEL %d  -  %s" % [game.index + 1, e.level.name.to_upper()], 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	HudKit.text(self, Vector2(vp.x * 0.5, 70), "BEST %07d" % game.high, 16, Color(HudKit.INK, 0.6), HudKit.label_font(), HudKit.CENTER)
	var cam: Camera3D = get_viewport().get_camera_3d()
	for p in _pops:
		if cam:
			var sp := cam.unproject_position(p["pos"]) + Vector2(0, -44.0 * p["t"])
			var c: Color = p["col"]
			HudKit.text(self, sp, p["text"], 26, Color(c, 1.0 - p["t"] / 1.2), HudKit.font(true), HudKit.CENTER)
	if _hurry_t > 0.0:
		HudKit.banner(self, vp, vp.y * 0.5, "HURRY UP", "", HudKit.BAD, minf(1.0, _hurry_t), 1.0 + 0.1 * sin(_t * 12.0))
	if e.phase == FizzEngine.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.42, "LEVEL %d" % (game.index + 1), e.level.name.to_upper(), P_COL[0], 1.0)
	elif e.phase == FizzEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.42, "LEVEL CLEAR", "", HudKit.GOOD, 1.0)
	if game.over or e.phase == FizzEngine.Phase.OVER:
		var best := 0
		for h in e.heroes:
			best = maxi(best, h["score"])
		HudKit.banner(self, vp, vp.y * 0.5, "GAME OVER", "SCORE %d" % best, HudKit.BAD, 1.0)
		if not game.demo and game.over:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.5 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 62, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 32), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
