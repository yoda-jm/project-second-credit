class_name TorchHud
extends Control
## Four Torches HUD: a card per hero along the top (class, health ticking down, score, keys and potions, CPU or
## player), the level, warnings when a hero is weak, points and pickups popping up, LEVEL CLEAR on the exit, the end.

const T = preload("res://games/fourtorches/engine/torch_engine.gd")
const TEAM := [Color(0.9, 0.2, 0.15), Color(0.2, 0.45, 0.95), Color(0.95, 0.8, 0.2), Color(0.25, 0.8, 0.3)]
const ACCENT := Color(1.0, 0.65, 0.3)

@export var game: TorchGame

var _t := 0.0
var _pops: Array[Dictionary] = []
var _warn := {}


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"kill":
			if d["points"] > 0:
				var p: Vector2 = d["pos"]
				_pops.append({"text": str(d["points"]), "pos": Vector3(p.x, 1.2, p.y), "t": 0.0, "col": HudKit.INK})
		"food", "key", "potion", "treasure":
			var h := e.heroes[d["h"]]
			var txt: String = {"food": "+100 HEALTH", "key": "KEY", "potion": "POTION", "treasure": "+%d" % d.get("points", 0)}[kind]
			_pops.append({"text": txt, "pos": Vector3(h["pos"].x, 1.6, h["pos"].y), "t": 0.0, "col": TEAM[d["h"] % 4].lightened(0.4)})
		"low":
			_warn[d["h"]] = 3.0
		"food_shot", "potion_shot":
			var p: Vector2 = d["pos"]
			var who: String = T.CLASSES[e.heroes[d["h"]]["cls"]]["name"]
			_pops.append({"text": "%s SHOT THE %s!" % [who, "FOOD" if kind == "food_shot" else "POTION"], "pos": Vector3(p.x, 1.4, p.y), "t": -0.6,
				"col": HudKit.BAD})


func _process(delta: float) -> void:
	_t += delta
	for k in _warn.keys():
		_warn[k] -= delta
		if _warn[k] <= 0.0:
			_warn.erase(k)
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.2)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	var n := e.heroes.size()
	var cw := minf(300.0, (vp.x - 48.0 - (n - 1) * 12.0) / n)
	for i in n:
		var h := e.heroes[i]
		var col: Color = TEAM[i % 4]
		var x := 24.0 + i * (cw + 12.0)
		var r := Rect2(x, 16, cw, 92)
		HudKit.panel(self, r, col, 12, 0.5 if h["dead"] else 1.0)
		HudKit.text(self, Vector2(x + 16, 40), T.CLASSES[h["cls"]]["name"] + ("  CPU" if h["cpu"] else ""), 16, col.lightened(0.35), HudKit.label_font(), HudKit.LEFT)
		var hp: float = maxf(0.0, h["health"])
		var low: bool = hp < 200.0 and not h["dead"]
		var hcol := HudKit.BAD.lerp(Color.WHITE, 0.4 * (0.5 + 0.5 * sin(_t * 10.0))) if low else HudKit.INK
		HudKit.text(self, Vector2(x + 16, 76), "DEAD" if h["dead"] else "%d" % ceili(hp), 30, hcol, HudKit.font(true), HudKit.LEFT)
		HudKit.text(self, Vector2(x + cw - 16, 50), "%d" % h["score"], 18, HudKit.GOLD, HudKit.label_font(), HudKit.RIGHT)
		var items := ""
		if h["keys"] > 0:
			items += "KEY x%d  " % h["keys"]
		if h["potions"] > 0:
			items += "POTION x%d" % h["potions"]
		HudKit.text(self, Vector2(x + cw - 16, 84), items, 14, HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
	HudKit.text(self, Vector2(vp.x * 0.5, 134), "LEVEL %d  -  %s" % [e.level + 1, e.title], 18, ACCENT, HudKit.label_font(), HudKit.CENTER)
	var cam := get_viewport().get_camera_3d()
	if cam:
		for p in _pops:
			if cam.is_position_behind(p["pos"]):
				continue
			var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 40.0)
			var c: Color = p["col"]
			HudKit.text(self, sp, p["text"], 20, Color(c, clampf(1.2 - p["t"], 0.0, 1.0)), HudKit.font(true), HudKit.CENTER)
		for i in _warn:
			var h := e.heroes[i]
			var sp := cam.unproject_position(Vector3(h["pos"].x, 1.8, h["pos"].y))
			HudKit.text(self, sp, "%s NEEDS FOOD!" % T.CLASSES[h["cls"]]["name"], 18, HudKit.BAD, HudKit.font(true), HudKit.CENTER)
	if e.phase == T.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.36, e.title, "LEVEL %d  -  FIND THE EXIT  -  SMASH THE GENERATORS  -  DON'T SHOOT THE FOOD" % (e.level + 1), ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif e.phase == T.Phase.EXIT:
		HudKit.banner(self, vp, vp.y * 0.36, "DOWN THE STAIRS" if e.jump == 1 else "A SHORTCUT!", "LEVEL %d" % (e.level + 1 + e.jump), HudKit.GOLD, clampf((2.5 - e.phase_t) * 3.0, 0.0, 1.0))
	if game.over:
		HudKit.banner(self, vp, vp.y * 0.42, "THE TORCHES ARE OUT", "PRESS ENTER" if not game.demo else "", HudKit.BAD, 1.0)
	elif not game.demo and e.level == 0 and e.time < 14.0:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 50), [["ARROWS", "MOVE"], ["SPACE", "ATTACK"], ["P", "POTION"], ["F2 - F4", "MORE HEROES"]])
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 14), "DEMO  -  PRESS ANY KEY TO PLAY", 18, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
