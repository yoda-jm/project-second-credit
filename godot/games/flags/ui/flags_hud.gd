class_name FlagsHud
extends Control
## Iron Flags HUD: both armies' territories, units and build speed; the minimap (click it to move the camera);
## health bars over hurt or selected units; the selection box; the selected squad or factory (with what it builds,
## 1-6 to change it); banners for territories taken and lost, and the end of the battle.

const E = preload("res://games/flags/engine/flags_engine.gd")
const T = FlagsMap.T
const Team = FlagsMap.Team
const RED := Color(1.0, 0.35, 0.3)
const BLUE := Color(0.4, 0.62, 1.0)
const NAMES := {"grunt": "GRUNTS", "psycho": "PSYCHOS", "sniper": "SNIPERS", "tough": "TOUGHS", "pyro": "PYRO",
	"laser": "LASER", "jeep": "JEEP", "tank_light": "LIGHT TANK", "tank_medium": "MEDIUM TANK", "tank_heavy": "HEAVY TANK",
	"apc": "APC", "missile_launcher": "MISSILES", "gatling": "GATLING", "gun": "GUN", "howitzer": "HOWITZER", "missile": "MISSILE GUN"}
const MINI := 250.0

@export var game: FlagsGame

var _banner := ""
var _sub := ""
var _col := HudKit.GOLD
var _t := 0.0
var _len := 0.0
var _minimap: ImageTexture
var _time := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.map_started.connect(_on_map)
	game.campaign_over.connect(func(won): _show("CAMPAIGN WON" if won else "CAMPAIGN LOST", "", HudKit.GOLD if won else HudKit.BAD, 99.0))
	if game.engine:
		_on_map(game.engine)


func _on_map(e: FlagsEngine) -> void:
	e.event.connect(_on_event)
	_show("MAP %d" % (game.level + 1), e.map.name.to_upper(), HudKit.GOLD, 3.0)
	var m := e.map
	var img := Image.create(m.w, m.h, false, Image.FORMAT_RGBA8)
	var ground: Color = {"desert": Color(0.72, 0.6, 0.42), "arctic": Color(0.85, 0.88, 0.95), "volcanic": Color(0.3, 0.25, 0.24),
		"jungle": Color(0.3, 0.45, 0.25), "city": Color(0.5, 0.5, 0.52)}.get(m.planet, Color(0.6, 0.55, 0.45))
	for y in m.h:
		for x in m.w:
			var c: Color = ground
			match m.at(Vector2i(x, y)):
				T.WATER: c = Color(0.15, 0.35, 0.55)
				T.LAVA: c = Color(0.9, 0.35, 0.1)
				T.ROCK: c = ground.darkened(0.55)
				T.ROAD, T.BRIDGE: c = ground.darkened(0.2)
			img.set_pixel(x, y, c)
	_minimap = ImageTexture.create_from_image(img)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"capture":
			if game.demo:
				return
			if d["team"] == Team.RED:
				_show("TERRITORY TAKEN", "", HudKit.GOOD, 1.8)
			elif d["from"] == Team.RED:
				_show("TERRITORY LOST", "", HudKit.BAD, 1.8)
		"won": _show("VICTORY", "THE ENEMY FORT IS RUBBLE", HudKit.GOLD, 99.0)
		"lost": _show("DEFEAT" if not game.demo else "BLUE WINS", "", HudKit.BAD if not game.demo else BLUE, 99.0)


func _show(text: String, sub: String, col: Color, secs: float) -> void:
	_banner = text
	_sub = sub
	_col = col
	_t = 0.0
	_len = secs


func _process(delta: float) -> void:
	if not game.story_open:  # the map banner waits behind a story card
		_t += delta
	_time += delta
	queue_redraw()


func _gui_input(_event: InputEvent) -> void:
	pass


func _input(event: InputEvent) -> void:
	# a click on the minimap moves the camera there
	if game.engine == null or game.view == null:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var r := _mini_rect()
		var p: Vector2 = get_global_transform_with_canvas().affine_inverse() * event.position
		if r.has_point(p):
			var m := game.engine.map
			game.view.look_at_map((p - r.position) / r.size * Vector2(m.w, m.h))
			get_viewport().set_input_as_handled()


func _mini_rect() -> Rect2:
	var m := game.engine.map
	var vp := get_viewport_rect().size
	var s := MINI / maxf(m.w, m.h)
	var size := Vector2(m.w, m.h) * s
	return Rect2(Vector2(24, vp.y - 24 - size.y), size)


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	_bars(e)
	# armies
	for i in 2:
		var team := Team.RED if i == 0 else Team.BLUE
		var col := RED if i == 0 else BLUE
		var x := 24.0 if i == 0 else vp.x - 364.0
		HudKit.panel(self, Rect2(x, 16, 340, 108), col)
		HudKit.text(self, Vector2(x + 22, 40), ("YOU" if not game.demo else "RED") if i == 0 else "BLUE", 16, col, HudKit.font(true))
		var n := e.team_units(team).filter(func(u): return u["cls"] != "cannon").size()
		HudKit.stat(self, x + 22, 46, "TERRITORY", "%d/%d" % [e.zones_owned(team), e.zones.size()], HudKit.INK, HudKit.LEFT, 32)
		HudKit.stat(self, x + 150, 46, "UNITS", "%d" % n, HudKit.INK, HudKit.LEFT, 32)
		HudKit.stat(self, x + 240, 46, "BUILD", "x%.1f" % e.production_rate(team), HudKit.GOLD, HudKit.LEFT, 32)
	var secs := int(e.time)
	HudKit.panel(self, Rect2(vp.x * 0.5 - 90, 16, 180, 60), HudKit.GOLD)
	HudKit.text(self, Vector2(vp.x * 0.5, 58), "%d:%02d" % [secs / 60, secs % 60], 30, HudKit.GOLD, HudKit.font(true), HudKit.CENTER)
	_draw_minimap(e)
	_draw_selection(e, vp)
	if game.drag_rect.size.length() > 8.0:
		draw_rect(game.drag_rect, Color(0.5, 1.0, 0.5, 0.12))
		draw_rect(game.drag_rect, Color(0.5, 1.0, 0.5, 0.8), false, 2.0)
	if _banner != "" and _t < _len:
		var a := clampf(minf(_t * 5.0, (_len - _t) * 4.0), 0.0, 1.0)
		HudKit.banner(self, vp, vp.y * 0.3, _banner, _sub, _col, a, 1.0 + 0.25 * exp(-_t * 8.0))
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 24, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 66, wd, 46), Color(0, 0, 0, 0), 23, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 34), msg, 24, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	elif e.time < 25.0 and game.level == 0:
		HudKit.hints(self, Vector2(vp.x * 0.5 + 120, vp.y - 30), [["LEFT CLICK", "select (drag: box)"], ["RIGHT CLICK", "move / attack"],
			["A", "whole army"], ["1-6", "factory builds"], ["WHEEL", "zoom"]], clampf((25.0 - e.time) / 2.0, 0.0, 1.0))
	if game.over:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.3 + 130), [["ENTER", "play again"], ["ESC", "menu"]])


func _bars(e: FlagsEngine) -> void:
	var cam: Camera3D = game.view.camera if game.view else null
	if cam == null:
		return
	var sel := {}
	for id in game.selected:
		sel[id] = true
	for u in e.units:
		if u["dead"] or u["team"] == Team.NEUTRAL:
			continue
		if u["hp"] >= u["max_hp"] and not sel.has(u["id"]):
			continue
		var h := 1.0 if u["cls"] == "robot" else 1.4
		var p3 := Vector3(u["pos"].x - 0.5, h, u["pos"].y - 0.5)
		if cam.is_position_behind(p3):
			continue
		var sp := cam.unproject_position(p3)
		var wd := 34.0 if u["cls"] == "robot" else 50.0
		var f: float = clampf(u["hp"] / u["max_hp"], 0.0, 1.0)
		draw_rect(Rect2(sp + Vector2(-wd * 0.5, 0), Vector2(wd, 6)), Color(0, 0, 0, 0.6))
		draw_rect(Rect2(sp + Vector2(-wd * 0.5 + 1, 1), Vector2((wd - 2) * f, 4)), HudKit.GOOD.lerp(HudKit.BAD, 1.0 - f))
	# what each of your factories is building, and how far along (both sides in the demo)
	for b in e.buildings:
		if not b["kind"] in E.FACTORIES or b["team"] == Team.NEUTRAL or (b["team"] == Team.BLUE and not game.demo):
			continue
		var top := Vector3(b["cell"].x + b["size"].x * 0.5 - 0.5, 3.6 if b["kind"] != "fort" else 5.8, b["cell"].y + b["size"].y * 0.5 - 0.5)
		if cam.is_position_behind(top):
			continue
		var sp := cam.unproject_position(top)
		var col := RED if b["team"] == Team.RED else BLUE
		var picked: bool = game.factory == b["id"]
		draw_circle(sp, 22, Color(0.04, 0.05, 0.1, 0.7), true, -1.0, true)
		HudKit.ring(self, sp, 18, b["progress"], HudKit.GOLD if picked else col, 4.0)
		HudKit.text(self, sp + Vector2(0, 5), NAMES.get(b["build"], "?").left(2), 13, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	for b in e.buildings:
		if b["kind"] != "fort" or b["hp"] >= b["max_hp"]:
			continue
		var p3 := Vector3(b["cell"].x + b["size"].x * 0.5 - 0.5, 5.0, b["cell"].y + b["size"].y * 0.5 - 0.5)
		if cam.is_position_behind(p3):
			continue
		var sp := cam.unproject_position(p3)
		var f: float = clampf(float(b["hp"]) / b["max_hp"], 0.0, 1.0)
		draw_rect(Rect2(sp + Vector2(-80, 0), Vector2(160, 10)), Color(0, 0, 0, 0.6))
		draw_rect(Rect2(sp + Vector2(-79, 1), Vector2(158 * f, 8)), RED if b["team"] == Team.RED else BLUE)


func _draw_minimap(e: FlagsEngine) -> void:
	var r := _mini_rect()
	HudKit.panel(self, r.grow(10), HudKit.GOLD, 12, 0.9)
	draw_texture_rect(_minimap, r, false)
	var s := r.size.x / e.map.w
	for z in e.zones:
		if z["owner"] != Team.NEUTRAL:
			var zr: Rect2i = z["rect"]
			draw_rect(Rect2(r.position + Vector2(zr.position) * s, Vector2(zr.size) * s), Color(RED if z["owner"] == Team.RED else BLUE, 0.22))
		if z["flag"].x >= 0:
			var c: Color = {Team.NEUTRAL: Color(0.85, 0.85, 0.8), Team.RED: RED, Team.BLUE: BLUE}[z["owner"]]
			var fp: Vector2 = r.position + (Vector2(z["flag"]) + Vector2(0.5, 0.5)) * s
			draw_colored_polygon(PackedVector2Array([fp + Vector2(0, -6), fp + Vector2(6, -3), fp + Vector2(0, 0)]), c)
			draw_line(fp + Vector2(0, -6), fp + Vector2(0, 3), Color(0.1, 0.1, 0.1), 1.5)
	for b in e.buildings:
		if b["kind"] == "hut":
			continue
		var c: Color = {Team.NEUTRAL: Color(0.75, 0.75, 0.72), Team.RED: RED, Team.BLUE: BLUE}[b["team"]]
		draw_rect(Rect2(r.position + Vector2(b["cell"]) * s, Vector2(b["size"]) * s), c.darkened(0.2))
	for u in e.units:
		if u["dead"] or u["team"] == Team.NEUTRAL:
			continue
		draw_rect(Rect2(r.position + u["pos"] * s - Vector2(1.5, 1.5), Vector2(3, 3)), RED.lightened(0.2) if u["team"] == Team.RED else BLUE.lightened(0.2))
	if game.view:
		var f: Vector2 = game.view.focus()
		var half: Vector2 = Vector2(9.5, 5.5) * game.view._zoom
		draw_rect(Rect2(r.position + (f - half) * s, half * 2.0 * s).intersection(r), Color(1, 1, 1, 0.8), false, 1.5)


func _draw_selection(e: FlagsEngine, vp: Vector2) -> void:
	var x := 24.0 + MINI + 40.0
	var y := vp.y - 130.0
	if game.factory >= 0:
		var b := e.by_id(game.factory)
		var list: Array = E.VEHICLE_BUILDS if b["kind"] == "vehicle_factory" else E.ROBOT_BUILDS
		HudKit.panel(self, Rect2(x, y, 820, 106), RED)
		HudKit.text(self, Vector2(x + 20, y + 30), {"fort": "FORT", "robot_factory": "ROBOT FACTORY", "vehicle_factory": "VEHICLE FACTORY"}[b["kind"]], 16, RED, HudKit.label_font())
		for i in list.size():
			var k: String = list[i]
			var bx := x + 20 + i * 132
			var on: bool = b["build"] == k
			draw_rect(Rect2(bx, y + 42, 124, 50), Color(1, 1, 1, 0.14 if on else 0.05))
			if on:
				draw_rect(Rect2(bx, y + 42, 124, 50), HudKit.GOLD, false, 2.0)
				draw_rect(Rect2(bx, y + 88, 124 * b["progress"], 4), HudKit.GOLD)
			HudKit.text(self, Vector2(bx + 8, y + 60), str(i + 1), 12, HudKit.MUTED, HudKit.label_font())
			HudKit.text(self, Vector2(bx + 62, y + 76), NAMES[k], 13, HudKit.INK if on else HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
		return
	if game.selected.is_empty():
		return
	var counts := {}
	for id in game.selected:
		var u := e.by_id(id)
		counts[u["kind"]] = counts.get(u["kind"], 0) + 1
	HudKit.panel(self, Rect2(x, y + 40, 520, 66), RED)
	var s := ""
	for k in counts:
		s += "%d %s   " % [counts[k], NAMES.get(k, k.to_upper())]
	HudKit.text(self, Vector2(x + 20, y + 82), s.strip_edges(), 18, HudKit.INK, HudKit.label_font())
