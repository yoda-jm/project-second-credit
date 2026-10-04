class_name TinHud
extends Control
## Tinplate Turbo HUD: the track's card and the countdown lights, the lap and the position of each player's car, the
## running order down the side (with wrenches), FINAL LAP, the chequered flag, the results with the points, the
## upgrade bench (three wrenches a level), the championship standings at the end; the keys at the first start.

const T = preload("res://games/tinplate/engine/tin_engine.gd")
const ACCENT := Color(1.0, 0.75, 0.25)
const ORD := ["1ST", "2ND", "3RD", "4TH"]

@export var game: TinGame

var _t := 0.0
var _go := 0.0
var _final := {}                 ## car -> time left showing FINAL LAP
var _pops: Array[Dictionary] = []


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.race_started.connect(func(e):
		e.event.connect(_on_event)
		_final.clear())


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"go": _go = 1.2
		"final_lap": _final[d["car"]] = 2.0
		"wrench":
			var p: Vector2 = d["pos"]
			_pops.append({"text": "+WRENCH", "pos": Vector3(p.x, 1.2, p.y), "t": 0.0, "col": T.COLOURS[d["car"]]})
		"lap":
			var c := e.cars[d["car"]]
			if not c["cpu"]:
				var p: Vector2 = c["pos"]
				_pops.append({"text": "LAP %d" % (c["lap"] + 1), "pos": Vector3(p.x, 1.5, p.y), "t": 0.0, "col": HudKit.INK})


func _process(delta: float) -> void:
	_t += delta
	_go = maxf(0.0, _go - delta)
	for k in _final.keys():
		_final[k] -= delta
		if _final[k] <= 0.0:
			_final.erase(k)
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.2)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	match game.mode:
		TinGame.Mode.FINAL:
			_draw_final(vp)
			return
	# the track
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "RACE %d OF %d" % [game.index + 1, game.tracks.size()], e.track.name.to_upper(), HudKit.INK, HudKit.LEFT, 26)
	# the running order down the right
	var order := e.order()
	var y := 16.0
	HudKit.panel(self, Rect2(vp.x - 244, y, 220, 30 + 36 * 4), ACCENT)
	for k in order.size():
		var i := order[k]
		var c := e.cars[i]
		var col: Color = T.COLOURS[i]
		var yy := y + 40 + k * 36
		HudKit.text(self, Vector2(vp.x - 228, yy), ORD[k], 18, HudKit.GOLD if k == 0 else HudKit.INK, HudKit.font(true), HudKit.LEFT)
		HudKit.gem(self, Vector2(vp.x - 166, yy - 7), 8.0, col)
		HudKit.text(self, Vector2(vp.x - 150, yy), T.NAMES[i] + ("" if c["cpu"] else " (YOU)" if game.humans == 1 else " P%d" % (i + 1)), 16,
			col.lightened(0.3), HudKit.label_font(), HudKit.LEFT)
		HudKit.text(self, Vector2(vp.x - 40, yy), "%d" % c["wrenches"] if c["wrenches"] > 0 else "", 16, HudKit.GOLD, HudKit.label_font(), HudKit.RIGHT)
	# each player's lap and place, big, at the bottom
	var slots := 0
	for i in e.cars.size():
		var c := e.cars[i]
		if c["cpu"]:
			continue
		var x := 24.0 + slots * 280.0
		slots += 1
		var col: Color = T.COLOURS[i]
		HudKit.panel(self, Rect2(x, vp.y - 110, 260, 90), col)
		var place := order.find(i)
		HudKit.text(self, Vector2(x + 20, vp.y - 50), ORD[place], 44, col.lightened(0.3), HudKit.font(true), HudKit.LEFT)
		var lap := clampi(c["lap"] + 1, 1, e.track.laps)
		HudKit.text(self, Vector2(x + 240, vp.y - 74), "LAP %d / %d" % [lap, e.track.laps] if not c["done"] else "FINISHED", 18, HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
		HudKit.text(self, Vector2(x + 240, vp.y - 44), "BEST %.2f" % c["best"] if c["best"] < 999.0 else "", 16, HudKit.MUTED, HudKit.label_font(), HudKit.RIGHT)
	# the countdown lights
	if e.phase == T.Phase.COUNTDOWN:
		var n := ceili(e.phase_t)
		var c0 := Vector2(vp.x * 0.5, vp.y * 0.36)
		HudKit.panel(self, Rect2(c0.x - 130, c0.y - 46, 260, 92), ACCENT)
		for k in 3:
			var on := (3 - k) > n - 1 and n <= 3
			draw_circle(c0 + Vector2((k - 1) * 76, 0), 30, Color(0.15, 0.03, 0.03))
			if on:
				draw_circle(c0 + Vector2((k - 1) * 76, 0), 26, Color(1.0, 0.2, 0.12))
		if game.index == 0 and not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.36 + 90), [["← →", "TURN"], ["↑ / SPACE", "ACCELERATE"], ["F2", "SECOND PLAYER (W A S D)"]])
	elif _go > 0.0:
		HudKit.banner(self, vp, vp.y * 0.36, "GO!", "", HudKit.GOOD, minf(1.0, _go * 2.0))
	for i in _final:
		if not e.cars[i]["cpu"] or game.demo:
			HudKit.banner(self, vp, vp.y * 0.3, "FINAL LAP", T.NAMES[i], T.COLOURS[i], minf(1.0, _final[i]))
			break
	var cam := get_viewport().get_camera_3d()
	if cam:
		for p in _pops:
			if cam.is_position_behind(p["pos"]):
				continue
			var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 40.0)
			var c: Color = p["col"]
			HudKit.text(self, sp, p["text"], 20, Color(c.lightened(0.3), clampf(1.2 - p["t"], 0.0, 1.0)), HudKit.font(true), HudKit.CENTER)
		# a tag over each player's car
		for i in e.cars.size():
			var c := e.cars[i]
			if c["cpu"]:
				continue
			var sp := cam.unproject_position(Vector3(c["pos"].x, c["y"] + 1.6, c["pos"].y))
			var b := sp + Vector2(0, -4 * sin(_t * 5.0))
			draw_colored_polygon(PackedVector2Array([b, b + Vector2(-9, -12), b + Vector2(9, -12)]), Color(T.COLOURS[i]).lightened(0.4))
			if game.humans > 1:
				HudKit.text(self, b + Vector2(0, -16), "P%d" % (i + 1), 14, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	if game.mode == TinGame.Mode.RESULTS or (e.phase == T.Phase.DONE and game.mode == TinGame.Mode.RACE):
		_draw_results(vp)
	elif game.mode == TinGame.Mode.BENCH:
		_draw_bench(vp)
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 12), "DEMO  -  PRESS ANY KEY TO PLAY", 16, HudKit.INK, HudKit.label_font(), HudKit.CENTER)


func _draw_results(vp: Vector2) -> void:
	var e := game.engine
	var a := clampf(game.mode_t * 3.0, 0.0, 1.0) if game.mode == TinGame.Mode.RESULTS else clampf(e.phase_t * 2.0, 0.0, 1.0)
	var win := e.order()[0]
	if game.mode != TinGame.Mode.RESULTS:
		HudKit.banner(self, vp, vp.y * 0.3, "%s WINS" % T.NAMES[win], e.track.name.to_upper(), T.COLOURS[win], a)
		return
	var r := Rect2(vp.x * 0.5 - 280, vp.y * 0.5 - 170, 560, 320)
	HudKit.panel(self, r, ACCENT, 14, a)
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 50), e.track.name.to_upper(), 30, Color(HudKit.GOLD, a), HudKit.font(true), HudKit.CENTER)
	var order := e.order()
	for k in order.size():
		var i := order[k]
		var y := r.position.y + 110 + k * 50
		var col: Color = T.COLOURS[i]
		HudKit.text(self, Vector2(r.position.x + 40, y), ORD[k], 24, Color(HudKit.INK, a), HudKit.font(true), HudKit.LEFT)
		HudKit.gem(self, Vector2(r.position.x + 120, y - 8), 9.0, Color(col, a))
		HudKit.text(self, Vector2(r.position.x + 140, y), T.NAMES[i], 22, Color(col.lightened(0.3), a), HudKit.font(true), HudKit.LEFT)
		HudKit.text(self, Vector2(r.end.x - 160, y), "+%d" % T.POINTS[k], 20, Color(HudKit.GOOD, a), HudKit.label_font(), HudKit.RIGHT)
		HudKit.text(self, Vector2(r.end.x - 40, y), "%d PTS" % game.cars[i]["points"], 20, Color(HudKit.GOLD, a), HudKit.label_font(), HudKit.RIGHT)


func _draw_bench(vp: Vector2) -> void:
	var i := game.bench_car
	if i < 0:
		return
	var c: Dictionary = game.cars[i]
	var col: Color = T.COLOURS[i]
	var r := Rect2(vp.x * 0.5 - 280, vp.y * 0.5 - 200, 560, 380)
	HudKit.panel(self, r, col)
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 54), "THE WORKBENCH", 32, HudKit.GOLD, HudKit.font(true), HudKit.CENTER)
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 90), "%s  -  %d WRENCHES (3 A LEVEL)" % [T.NAMES[i], c["wrenches"]], 18, col.lightened(0.3), HudKit.label_font(), HudKit.CENTER)
	var names := ["TOP SPEED", "GRIP", "ACCELERATION", "DONE"]
	var keys := ["speed", "grip", "accel"]
	for k in 4:
		var y := r.position.y + 150 + k * 52
		if k == game.bench_cursor:
			draw_rect(Rect2(r.position.x + 20, y - 32, r.size.x - 40, 44), Color(1, 1, 1, 0.08))
		HudKit.text(self, Vector2(r.position.x + 50, y), names[k], 22, HudKit.INK, HudKit.font(true), HudKit.LEFT)
		if k < 3:
			var lv: int = c["up"][keys[k]]
			for b in 4:
				draw_rect(Rect2(r.end.x - 200 + b * 38, y - 22, 30, 18), HudKit.GOLD if b < lv else Color(1, 1, 1, 0.12))


func _draw_final(vp: Vector2) -> void:
	var st := game.standings()
	var r := Rect2(vp.x * 0.5 - 300, vp.y * 0.5 - 200, 600, 380)
	var w := st[0]
	HudKit.panel(self, r, T.COLOURS[w])
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 62), "%s TAKES THE CUP" % T.NAMES[w], 34, Color(T.COLOURS[w]).lightened(0.3), HudKit.font(true), HudKit.CENTER)
	for k in st.size():
		var i := st[k]
		var y := r.position.y + 130 + k * 52
		HudKit.text(self, Vector2(r.position.x + 70, y), "%s  %s" % [ORD[k], T.NAMES[i]], 24, Color(T.COLOURS[i]).lightened(0.3), HudKit.font(true), HudKit.LEFT)
		HudKit.text(self, Vector2(r.end.x - 70, y), "%d PTS" % game.cars[i]["points"], 22, HudKit.GOLD, HudKit.label_font(), HudKit.RIGHT)
	HudKit.text(self, Vector2(vp.x * 0.5, r.end.y - 30), "PRESS ENTER" if not game.demo else "", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
