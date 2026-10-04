class_name FlowHud
extends Control
## Brassflow HUD: score and best, the level and its chances, the pressure gauge (the countdown to the flow, then the
## length filled against the length needed), points rising where the glow fills a piece (a loop bonus for a cross
## filled both ways), the level card, PIPELINE COMPLETE with the extra length counting, LEAK!, and GAME OVER. Until the
## first piece is down, a how-to card shows the keys.

const ACCENT := Color(1.0, 0.7, 0.3)
const GLOW := Color(0.3, 1.0, 0.6)

@export var game: FlowGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _placed := false
var _leak := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		_leak = 0.0)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"place":
			_placed = true
		"replace":
			var c: Vector2i = d["cell"]
			_pops.append({"text": "-50", "pos": Vector3(c.x + 0.5, 0.6, c.y + 0.5), "t": 0.0, "col": HudKit.BAD, "size": 22})
		"fill":
			var c: Vector2i = d["cell"]
			var twice: bool = d["cross_twice"]
			var pts := (100 if game.engine.fast else 50) + (500 if twice else 0)
			_pops.append({"text": ("LOOP! " if twice else "") + str(pts), "pos": Vector3(c.x + 0.5, 0.6, c.y + 0.5), "t": 0.0,
				"col": HudKit.GOLD if twice else GLOW, "size": 30 if twice else 22})
		"spill":
			_leak = 2.5


func _process(delta: float) -> void:
	_t += delta
	_leak = maxf(0.0, _leak - delta)
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
	HudKit.stat(self, vp.x - 48, 20, "LEVEL %d" % (e.level + 1), "BEST %07d" % maxi(game.high, e.score), HudKit.INK, HudKit.RIGHT, 24)
	for i in e.chances:
		HudKit.gem(self, Vector2(vp.x - 56 - i * 26, 124), 9.0, ACCENT)
	# the gauge: the countdown, then the length
	var c := Vector2(vp.x * 0.5, 66)
	HudKit.panel(self, Rect2(c.x - 150, 12, 300, 108), ACCENT)
	if not e.flowing:
		var full := maxf(8.0, 18.0 - e.level * 1.2)
		var frac := clampf(e.countdown / full, 0.0, 1.0)
		var low := e.countdown < 4.0 and e.phase == FlowEngine.Phase.PLAY
		var col := HudKit.BAD.lerp(Color.WHITE, 0.4 * (0.5 + 0.5 * sin(_t * 10.0))) if low else HudKit.INK
		HudKit.ring(self, c + Vector2(-90, 0), 34.0, frac, ACCENT, 8.0)
		HudKit.text(self, c + Vector2(-90, 12), "%d" % ceili(e.countdown), 30, col, HudKit.font(true), HudKit.CENTER)
		HudKit.text(self, c + Vector2(40, -10), "FLOW IN", 18, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
		HudKit.text(self, c + Vector2(40, 24), "NEED %d" % e.length, 30, HudKit.INK, HudKit.font(true), HudKit.CENTER)
	else:
		var frac := clampf(float(e.filled) / e.length, 0.0, 1.0)
		var done := e.filled >= e.length
		HudKit.ring(self, c + Vector2(-90, 0), 34.0, frac, HudKit.GOOD if done else GLOW, 8.0)
		HudKit.text(self, c + Vector2(-90, 12), "%d" % e.filled, 30, HudKit.GOOD if done else HudKit.INK, HudKit.font(true), HudKit.CENTER)
		HudKit.text(self, c + Vector2(40, -10), "FAST FLOW" if e.fast else "FLOWING", 18, GLOW, HudKit.label_font(), HudKit.CENTER)
		HudKit.text(self, c + Vector2(40, 24), "%d / %d" % [e.filled, e.length], 30, HudKit.INK, HudKit.font(true), HudKit.CENTER)
	# points over the board
	var cam := get_viewport().get_camera_3d()
	for p in _pops:
		if cam == null or cam.is_position_behind(p["pos"]):
			continue
		var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 60.0)
		var a := clampf(1.1 - p["t"], 0.0, 1.0)
		var col2: Color = p["col"]
		HudKit.text(self, sp, p["text"], p["size"], Color(col2, a), HudKit.font(true), HudKit.CENTER)
	if e.phase == FlowEngine.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.36, "LEVEL %d" % (e.level + 1), "LAY %d PIPES BEFORE THE GLOW" % e.length, ACCENT,
			clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif e.phase == FlowEngine.Phase.DONE and e.passed():
		HudKit.banner(self, vp, vp.y * 0.36, "PIPELINE COMPLETE", "%d PIECES  -  BONUS %d" % [e.filled, maxi(0, e.filled - e.length) * 100],
			HudKit.GOLD, clampf((3.0 - e.phase_t) * 3.0, 0.0, 1.0))
	elif e.phase == FlowEngine.Phase.DONE:
		HudKit.banner(self, vp, vp.y * 0.36, "LEAK!", "%d OF %d  -  TRY AGAIN" % [e.filled, e.length], HudKit.BAD,
			clampf((3.0 - e.phase_t) * 3.0, 0.0, 1.0))
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.42, "GAME OVER", "PRESS ENTER" if not game.demo else "", HudKit.BAD, 1.0)
	elif not _placed and not game.demo and e.phase == FlowEngine.Phase.PLAY:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 60), [["ARROWS", "MOVE"], ["SPACE", "LAY PIPE"], ["F", "FAST FLOW"]])
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 30), "DEMO  -  PRESS ANY KEY TO PLAY", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
