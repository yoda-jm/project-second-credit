class_name BloomHud
extends Control
## Bloomwand HUD: each fairy's score, lives and E X T R A letters (one panel per player, in her colour), the level and
## the flowers left, the clock and HURRY, points popping where creatures burst and things are picked, the level card,
## FULL BLOOM when every flower is picked, LEVEL CLEAR, the end, and the keys at the first level.

const B = preload("res://games/bloomwand/engine/bloom_engine.gd")
const ACCENT := Color(1.0, 0.6, 0.8)
const DRESS := [Color(1.0, 0.45, 0.7), Color(0.25, 0.8, 0.8)]

@export var game: BloomGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _bloom := 0.0
var _hurry := 0.0
var _moved := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"pop":
			var p: Vector2 = d["pos"]
			_pops.append({"text": str(d["points"]), "pos": Vector3(p.x, p.y + 1.2, 0.5), "t": 0.0, "col": HudKit.INK, "size": 24})
		"take":
			var f := game.engine.fairies[d["p"]]
			_pops.append({"text": str(d["points"]), "pos": Vector3(f["pos"].x, f["pos"].y + 1.4, 0.5), "t": 0.0, "col": HudKit.GOLD, "size": 24})
		"letter":
			var f := game.engine.fairies[d["p"]]
			_pops.append({"text": d["letter"], "pos": Vector3(f["pos"].x, f["pos"].y + 1.4, 0.5), "t": 0.0, "col": Color(0.6, 0.9, 1.0), "size": 34})
		"flower":
			var p: Vector2 = d["pos"]
			_pops.append({"text": "100", "pos": Vector3(p.x, p.y + 0.8, 0.5), "t": 0.0, "col": Color(1.0, 0.75, 0.9), "size": 18})
		"bloom": _bloom = 2.5
		"hurry": _hurry = 2.0
		"cast": _moved = true


func _process(delta: float) -> void:
	_t += delta
	_bloom = maxf(0.0, _bloom - delta)
	_hurry = maxf(0.0, _hurry - delta)
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.2)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	for f in e.fairies:
		var i: int = f["i"]
		var col: Color = DRESS[i % 2]
		var x := 24.0 if i == 0 else vp.x - 324.0
		HudKit.panel(self, Rect2(x, 16, 300, 96), col)
		HudKit.stat(self, x + 24 if i == 0 else x + 276, 20, "PLAYER %d" % (i + 1), "%07d" % f["score"], HudKit.GOLD, HudKit.LEFT if i == 0 else HudKit.RIGHT)
		for k in mini(f["lives"], 6):
			HudKit.gem(self, Vector2(x + 30 + k * 22, 100) if i == 0 else Vector2(x + 270 - k * 22, 100), 7.0, col)
		for k in B.LETTERS.size():
			var l: String = B.LETTERS[k]
			var have: bool = f["letters"].has(l)
			var lx := x + 170 + k * 24 if i == 0 else x + 30 + k * 24
			HudKit.text(self, Vector2(lx, 106), l, 20, HudKit.GOLD if have else Color(1, 1, 1, 0.2), HudKit.font(true), HudKit.CENTER)
	# the level, the flowers, the clock
	var c := Vector2(vp.x * 0.5, 56)
	HudKit.panel(self, Rect2(c.x - 170, 14, 340, 84), ACCENT)
	HudKit.text(self, c + Vector2(0, -16), "LEVEL %d  -  %s" % [game.index + 1, e.lv.name.to_upper()], 17, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	var left := e.flowers.size()
	HudKit.text(self, c + Vector2(-60, 22), "FLOWERS %d" % left if left > 0 else "FULL BLOOM", 20, Color(1.0, 0.75, 0.9), HudKit.font(true), HudKit.CENTER)
	var clock := maxf(0.0, B.HURRY_AT - e.time)
	var hcol := HudKit.BAD.lerp(Color.WHITE, 0.4 * (0.5 + 0.5 * sin(_t * 10.0))) if e.hurry else HudKit.INK
	HudKit.text(self, c + Vector2(90, 22), "HURRY" if e.hurry else "%d" % ceili(clock), 22, hcol, HudKit.font(true), HudKit.CENTER)
	var cam := get_viewport().get_camera_3d()
	if cam:
		for p in _pops:
			var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 40.0)
			var col2: Color = p["col"]
			HudKit.text(self, sp, p["text"], p["size"], Color(col2, clampf(1.2 - p["t"], 0.0, 1.0)), HudKit.font(true), HudKit.CENTER)
	if e.phase == B.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.36, "LEVEL %d" % (game.index + 1), e.lv.name.to_upper(), ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif e.phase == B.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.36, "LEVEL CLEAR", "FULL BLOOM  +3000" if e.flowers.is_empty() and e.flowers_total > 0 else "", HudKit.GOLD,
			clampf((3.5 - e.phase_t) * 3.0, 0.0, 1.0))
	elif _bloom > 0.0:
		HudKit.banner(self, vp, vp.y * 0.36, "FULL BLOOM!", "EVERY FLOWER PICKED", Color(1.0, 0.7, 0.9), minf(1.0, _bloom))
	elif _hurry > 0.0:
		HudKit.banner(self, vp, vp.y * 0.36, "HURRY!", "", HudKit.BAD, minf(1.0, _hurry))
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.42, "THE GARDEN IS SAFE" if game.won else "GAME OVER", "PRESS ENTER" if not game.demo else "",
			HudKit.GOLD if game.won else HudKit.BAD, 1.0)
	elif not _moved and not game.demo and game.index == 0 and e.phase == B.Phase.PLAY:
		var r := Rect2(vp.x * 0.5 - 320, vp.y - 170, 640, 80)
		HudKit.panel(self, r, ACCENT)
		HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 32), "ZAP A CREATURE WITH SPACE - IT GETS SMASHED", 21, HudKit.GOLD, HudKit.font(true), HudKit.CENTER)
		HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 60), "clear them all to finish the level  -  UP with no ladder makes a rainbow one", 16, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 50), [["ARROWS", "WALK, CLIMB"], ["SPACE", "WAND"], ["F2", "PLAYER 2"]])
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 14), "DEMO  -  PRESS ANY KEY TO PLAY", 18, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
