class_name BioHud
extends Control
## Biosurge HUD: score, credits and lives; the energy bar (and the shield); the weapons on board; the level's name at
## the start; WARNING and the boss's life at the end; LEVEL CLEAR; the trader's shop between levels; the end.

const B = preload("res://games/biosurge/engine/bio_engine.gd")
const ACCENT := Color(0.35, 1.0, 0.85)

@export var game: BioGame

var _t := 0.0
var _warn := 0.0
var _pops: Array[Dictionary] = []
var _flew := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"warning": _warn = 3.0
		"kill":
			var p: Vector2 = d["pos"]
			_pops.append({"text": str(d["points"]), "pos": Vector3(p.x, 0.5, -p.y), "t": 0.0})
		"shoot": _flew = true


func _process(delta: float) -> void:
	_t += delta
	_warn = maxf(0.0, _warn - delta)
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 0.8)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	if game.mode == BioGame.Mode.SHOP:
		_draw_shop(vp)
		return
	HudKit.panel(self, Rect2(24, 16, 300, 96), ACCENT)
	HudKit.stat(self, 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.text(self, Vector2(48, 100), "CREDITS  %d" % e.credits, 18, ACCENT, HudKit.label_font(), HudKit.LEFT)
	for i in mini(e.lives, 6):
		HudKit.gem(self, Vector2(48 + i * 24, 130), 8.0, ACCENT)
	# energy
	var r := Rect2(vp.x - 324, 16, 300, 96)
	HudKit.panel(self, r, ACCENT)
	HudKit.text(self, Vector2(r.position.x + 24, r.position.y + 30), "ENERGY", 15, HudKit.MUTED, HudKit.label_font(), HudKit.LEFT)
	draw_rect(Rect2(r.position.x + 24, r.position.y + 40, 252, 14), Color(0, 0, 0, 0.5))
	var en := e.energy / 100.0
	draw_rect(Rect2(r.position.x + 24, r.position.y + 40, 252 * en, 14), HudKit.GOOD.lerp(HudKit.BAD, 1.0 - en))
	if e.shield > 0.0:
		draw_rect(Rect2(r.position.x + 24, r.position.y + 56, 252 * clampf(e.shield / 6.0, 0.0, 1.0), 4), Color(0.5, 0.9, 1.0))
	var gear := ["GUN %d" % e.loadout["gun"]]
	for k in ["side", "rear", "homing", "laser", "drone"]:
		if e.loadout[k]:
			gear.append(k.to_upper())
	HudKit.text(self, Vector2(r.position.x + 24, r.position.y + 84), "  ".join(gear), 14, HudKit.INK, HudKit.label_font(), HudKit.LEFT)
	# the boss
	if not e.boss.is_empty() and e.boss["hp"] > 0.0:
		var br := Rect2(vp.x * 0.5 - 260, vp.y - 60, 520, 24)
		HudKit.panel(self, br.grow(8), HudKit.BAD)
		draw_rect(br, Color(0, 0, 0, 0.5))
		draw_rect(Rect2(br.position, Vector2(br.size.x * e.boss["hp"] / e.boss["max"], br.size.y)), HudKit.BAD.lerp(HudKit.GOLD, 0.3 + 0.2 * sin(_t * 6.0)))
	var cam := get_viewport().get_camera_3d()
	if cam:
		for p in _pops:
			var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 50.0)
			HudKit.text(self, sp, p["text"], 18, Color(HudKit.INK, clampf(0.8 - p["t"], 0.0, 1.0) * 1.25), HudKit.font(true), HudKit.CENTER)
	if e.phase == B.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.36, "LEVEL %d" % (e.level + 1), B.NAMES[e.level % 5], ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif _warn > 0.0:
		var a := 0.5 + 0.5 * sin(_t * 12.0)
		HudKit.banner(self, vp, vp.y * 0.36, "WARNING", "SOMETHING HUGE IS COMING", HudKit.BAD, a)
	elif e.phase == B.Phase.CLEARED:
		HudKit.banner(self, vp, vp.y * 0.36, "LEVEL CLEAR", "+400 CREDITS", HudKit.GOLD, clampf((4.0 - e.phase_t) * 3.0, 0.0, 1.0))
	if game.mode == BioGame.Mode.END:
		HudKit.banner(self, vp, vp.y * 0.42, "THE HIVE IS BEATEN" if game.won else "GAME OVER", "PRESS ENTER" if not game.demo else "",
			HudKit.GOLD if game.won else HudKit.BAD, 1.0)
	elif not _flew and not game.demo and e.level == 0 and e.phase == B.Phase.PLAY:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 50), [["ARROWS", "FLY"], ["SPACE", "FIRE (HOLD)"], ["WALLS", "HURT: KEEP CLEAR"]])
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 14), "DEMO  -  PRESS ANY KEY TO PLAY", 18, HudKit.INK, HudKit.label_font(), HudKit.CENTER)


func _draw_shop(vp: Vector2) -> void:
	var e := game.engine
	var r := Rect2(vp.x * 0.5 - 340, vp.y * 0.5 - 260, 680, 520)
	HudKit.panel(self, r, ACCENT)
	HudKit.text(self, Vector2(r.position.x + 32, r.position.y + 52), "THE TRADER", 32, ACCENT, HudKit.font(true), HudKit.LEFT)
	HudKit.text(self, Vector2(r.end.x - 32, r.position.y + 52), "%d CREDITS" % e.credits, 26, HudKit.GOLD, HudKit.font(true), HudKit.RIGHT)
	for k in B.SHOP.size() + 1:
		var y := r.position.y + 100 + k * 44
		if k == game.cursor:
			draw_rect(Rect2(r.position.x + 18, y - 30, r.size.x - 36, 40), Color(1, 1, 1, 0.08))
		if k == B.SHOP.size():
			HudKit.text(self, Vector2(vp.x * 0.5, y), "FLY ON  (ESC)", 22, HudKit.GOLD if k == game.cursor else HudKit.INK, HudKit.font(true), HudKit.CENTER)
			continue
		var it: Array = B.SHOP[k]
		var ok := e.can_buy(it[0], it[2])
		var owned := ""
		match it[0]:
			"gun": owned = "LEVEL %d" % e.loadout["gun"]
			"speed": owned = "LEVEL %d" % e.loadout["speed"]
			"life": owned = "%d SHIPS" % e.lives
			_: owned = "FITTED" if e.loadout[it[0]] else ""
		HudKit.text(self, Vector2(r.position.x + 40, y), it[1], 21, HudKit.INK if ok else HudKit.MUTED, HudKit.font(true), HudKit.LEFT)
		HudKit.text(self, Vector2(r.position.x + 380, y), owned, 16, HudKit.GOOD, HudKit.label_font(), HudKit.LEFT)
		HudKit.text(self, Vector2(r.end.x - 40, y), "%d" % it[2], 20, HudKit.GOLD if ok else HudKit.MUTED, HudKit.label_font(), HudKit.RIGHT)
