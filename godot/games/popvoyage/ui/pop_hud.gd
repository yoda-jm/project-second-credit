class_name PopHud
extends Control
## Pop Voyage HUD: score and best, lives, the stage's name and number, the clock (HURRY when it runs low), the
## weapon and the shield, points popping where balloons burst (bigger for a chain), item names, the stage card,
## STAGE CLEAR with the time bonus counting in, TIME UP and GAME OVER.

const ACCENT := Color(1.0, 0.55, 0.45)
const ITEM_NAMES := {"double": "DOUBLE WIRE", "sticky": "STICKY WIRE", "shield": "SHIELD", "clock": "TIME STOP", "charge": "CHARGE!"}

@export var game: PopGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _chain := 0
var _chain_t := 0.0
var _timeout := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"split", "pop":
			_chain = _chain + 1 if _chain_t > 0.0 else 1
			_chain_t = 1.0
			var pts: int = [100, 70, 50, 30][d["size"]] * _chain
			var p: Vector2 = d["pos"]
			_pops.append({"text": str(pts) + (" x%d" % _chain if _chain > 1 else ""), "pos": Vector3(p.x, p.y + 0.5, 0), "t": 0.0,
				"col": HudKit.GOLD if _chain < 3 else Color(1.0, 0.5, 0.8), "size": 24 + mini(_chain, 5) * 3})
		"take":
			_pops.append({"text": ITEM_NAMES.get(d["kind"], ""), "pos": Vector3(game.engine.hero["x"], 2.2, 0), "t": 0.0,
				"col": Color(0.6, 0.95, 1.0), "size": 26})
		"block":
			var p: Vector2 = d["pos"]
			_pops.append({"text": "200", "pos": Vector3(p.x, p.y, 0), "t": 0.0, "col": HudKit.INK, "size": 22})
		"timeout":
			_timeout = 2.0


func _process(delta: float) -> void:
	_t += delta
	_chain_t = maxf(0.0, _chain_t - delta)
	_timeout = maxf(0.0, _timeout - delta)
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.1)
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
	# the clock
	var low := e.clock < 15.0 and e.phase == PopEngine.Phase.PLAY
	var col := HudKit.BAD.lerp(Color.WHITE, 0.4 * (0.5 + 0.5 * sin(_t * 10.0))) if low else HudKit.INK
	HudKit.panel(self, Rect2(vp.x * 0.5 - 80, 16, 160, 64), ACCENT)
	HudKit.text(self, Vector2(vp.x * 0.5, 62), "%d" % ceili(e.clock), 40, col, HudKit.font(true), HudKit.CENTER)
	if low:
		HudKit.text(self, Vector2(vp.x * 0.5, 104), "HURRY!", 22, col, HudKit.label_font(), HudKit.CENTER)
	# weapon and shield
	var gear := []
	if e.weapon != "wire":
		gear.append(ITEM_NAMES[e.weapon])
	if e.shield:
		gear.append("SHIELD")
	if e.frozen > 0.0:
		gear.append("TIME STOP %.1f" % e.frozen)
	for i in gear.size():
		HudKit.text(self, Vector2(vp.x - 48, 136 + i * 26), gear[i], 20, Color(0.6, 0.95, 1.0), HudKit.label_font(), HudKit.RIGHT)
	var cam := get_viewport().get_camera_3d()
	for p in _pops:
		if cam == null or cam.is_position_behind(p["pos"]):
			continue
		var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 60.0)
		var a := clampf(1.1 - p["t"], 0.0, 1.0)
		var c: Color = p["col"]
		HudKit.text(self, sp, p["text"], p["size"], Color(c, a), HudKit.font(true), HudKit.CENTER)
	if e.phase == PopEngine.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.36, "STAGE %d" % (game.index + 1), e.stage.name.to_upper(), ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif e.phase == PopEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.36, "STAGE CLEAR", "TIME BONUS", HudKit.GOLD, clampf((3.5 - e.phase_t) * 3.0, 0.0, 1.0))
	elif _timeout > 0.0:
		HudKit.banner(self, vp, vp.y * 0.36, "TIME UP", "", HudKit.BAD, minf(1.0, _timeout))
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.42, "GAME OVER", "PRESS ENTER" if not game.demo else "", HudKit.BAD, 1.0)
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 30), "DEMO  -  PRESS ANY KEY TO PLAY", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
