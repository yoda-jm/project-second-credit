class_name RelicHud
extends Control
## Relic Run HUD: score and best, lives, bullets and dynamite as rows of pips, the level's name, points popping from
## treasure, the level card at the start, LEVEL CLEAR, GAME OVER.

const ACCENT := Color(1.0, 0.72, 0.35)

@export var game: RelicGame

var _pops: Array[Dictionary] = []
var _t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"pickup":
			var text: String = {"$": "1000", "a": "BULLETS", "x": "DYNAMITE"}[d["kind"]]
			_pops.append({"text": text, "pos": RelicView3D.world(d["pos"], 0.5), "t": 0.0})
		"hit":
			if d["dead"]:
				_pops.append({"text": "200" if d["kind"] == "automaton" else "100", "pos": RelicView3D.world(d["pos"] + Vector2(0, -1.5), 0.5), "t": 0.0})


func _process(delta: float) -> void:
	_t += delta
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.3)
	queue_redraw()


func _pips(x: float, y: float, n: int, of: int, col: Color, label: String) -> void:
	HudKit.text(self, Vector2(x, y + 6), label, 14, Color(HudKit.INK, 0.7), HudKit.label_font(), HudKit.RIGHT)
	for i in of:
		var r := Rect2(x + 10 + i * 16, y - 6, 11, 16)
		draw_rect(r, col if i < n else Color(1, 1, 1, 0.12))


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
	_pips(vp.x - 150, 128, e.bullets, 6, Color(1.0, 0.85, 0.4), "SHOTS")
	_pips(vp.x - 150, 154, e.dynamite, 6, Color(1.0, 0.4, 0.3), "DYNAMITE")
	var cam: Camera3D = get_viewport().get_camera_3d()
	for p in _pops:
		if cam:
			var sp := cam.unproject_position(p["pos"]) + Vector2(0, -44.0 * p["t"])
			HudKit.text(self, sp, p["text"], 24, Color(HudKit.GOLD, 1.0 - p["t"] / 1.3), HudKit.font(true), HudKit.CENTER)
	if e.phase == RelicEngine.Phase.READY and e.time < 2.0:
		HudKit.banner(self, vp, vp.y * 0.42, "LEVEL %d" % (game.index + 1), e.level.name.to_upper(), ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif e.phase == RelicEngine.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.42, "LEVEL CLEAR", "+5000", HudKit.GOOD, 1.0)
	if game.over or e.phase == RelicEngine.Phase.OVER:
		HudKit.banner(self, vp, vp.y * 0.5, "GAME OVER", "SCORE %d" % e.score, HudKit.BAD, 1.0)
		if not game.demo and game.over:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.5 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
	elif not game.demo and e.phase == RelicEngine.Phase.READY and game.index == 0 and e.lives == 6:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 50), [["Z", "jump"], ["SPACE", "fire"], ["C", "dynamite"], ["DOWN", "crawl"]])
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 62, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 32), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
