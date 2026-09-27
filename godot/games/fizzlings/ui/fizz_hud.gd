class_name FizzHud
extends Control
## Fizzlings HUD: each hero's score and lives (hero 2 on the right, or a "press W to join" hint), the level and best,
## points popping from treats, chain counts growing along a chain and the chain's reward, HURRY UP, READY, LEVEL CLEAR, GAME OVER.

const P_COL := [Color(1.0, 0.62, 0.72), Color(0.6, 0.7, 1.0)]

@export var game: FizzGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _hurry_t := 0.0
var _chain := 0
var _chain_pos := Vector3.ZERO


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"treat":
			var big: bool = d["points"] >= 1000
			_pops.append({"text": str(d["points"]), "pos": FizzView3D.world(d["pos"], 0.5), "t": 0.0, "life": 1.2,
				"size": 30 if big else 24, "col": (P_COL[d["p"]] as Color).lerp(Color.WHITE, 0.35) if not big else HudKit.GOLD})
		"pop":
			if d["trapped"]:
				_chain += 1
				_chain_pos = FizzView3D.world(d["pos"], 0.5)
				if d["n"] > 0:
					_pops.append({"text": "x%d" % (d["n"] + 1), "pos": _chain_pos, "t": 0.0, "life": 1.0,
						"size": mini(22 + d["n"] * 6, 52), "col": HudKit.GOLD})
		"hurry":
			_hurry_t = 2.5


func _process(delta: float) -> void:
	_t += delta
	_hurry_t = maxf(0.0, _hurry_t - delta)
	if _chain > 0:  # the full bubbles popped this frame: the chain's reward, bigger the longer the chain
		var pts: int = FizzEngine.CHAIN_POINTS[mini(_chain, FizzEngine.CHAIN_POINTS.size()) - 1]
		var col: Color = [HudKit.GOLD, Color(1.0, 0.6, 0.25), Color(1.0, 0.4, 0.55), Color(0.75, 0.5, 1.0), Color(0.4, 0.9, 1.0)][mini(_chain - 1, 4)]
		var text := "+%d" % pts if _chain == 1 else "CHAIN x%d  +%d" % [_chain, pts]
		_pops.append({"text": text, "pos": _chain_pos + Vector3(0, 0.6, 0), "t": 0.0, "life": 1.3 + _chain * 0.15,
			"size": mini(26 + _chain * 9, 72), "col": col})
		_chain = 0
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < p["life"])
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
			# pops in with an overshoot, floats up, fades at the end
			var t: float = p["t"]
			var k: float = t / p["life"]
			var grow := minf(1.0, t / 0.12) * (1.0 + 0.35 * exp(-t * 8.0) * sin(t * 30.0))
			var sp := cam.unproject_position(p["pos"]) + Vector2(0, -40.0 * t)
			var c: Color = p["col"]
			var a := clampf((1.0 - k) * 3.0, 0.0, 1.0)
			var fs := maxi(4, int(p["size"] * grow))
			var half := HudKit.width(p["text"], fs, HudKit.font(true)) * 0.5 + 16.0
			sp.x = clampf(sp.x, half, maxf(half, vp.x - half))
			HudKit.text(self, sp, p["text"], fs, Color(c, a), HudKit.font(true), HudKit.CENTER)
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
