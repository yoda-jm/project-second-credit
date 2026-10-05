class_name RidgeHud
extends Control
## Ridgefire HUD: the seats (tanks, players or CPUs, rounds); in play the round and its land, a card per tank (health,
## shield, rounds won, money), the wind, whose turn it is with the angle, power and weapon, health bars and a marker
## over the tanks, damage popping up, the round's winner; the shop between rounds; the standings at the end.

const R = preload("res://games/ridgefire/engine/ridge_engine.gd")
const ACCENT := Color(1.0, 0.62, 0.3)
const LANDS := ["MESA DUSK", "ALPINE FRONT", "MOONFALL", "EMBER ISLE", "FROZEN WASTES"]
const ITEM_TEXT := {
	"heavy": "a bigger blast", "mirv": "splits in five at the top", "roller": "rolls down to the lowest point",
	"dirt": "heaps earth: bury them", "digger": "bores a tunnel down", "nuke": "the end of the world", "shield": "soaks up 60 harm",
}

@export var game: RidgeGame

var _pops: Array[Dictionary] = []
var _t := 0.0
var _round_t := 0.0
var _taught := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.round_started.connect(func(e):
		_round_t = 0.0
		if not e.event.is_connected(_on_event):
			e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"hit":
			var q := e.players[d["player"]]
			_pops.append({"text": "-%d" % ceili(d["damage"]), "pos": Vector3(q["x"], q["y"] + 3.2, 0.5), "t": 0.0, "col": HudKit.BAD, "size": 26})
		"shield":
			var q := e.players[d["player"]]
			_pops.append({"text": "SHIELD", "pos": Vector3(q["x"], q["y"] + 3.6, 0.5), "t": 0.0, "col": Color(0.55, 0.9, 1.0), "size": 22})
		"fire":
			if not e.players[d["player"]]["cpu"]:
				_taught = true


func _process(delta: float) -> void:
	_t += delta
	_round_t += delta
	for p in _pops:
		p["t"] += delta
	_pops = _pops.filter(func(p): return p["t"] < 1.4)
	queue_redraw()


func _draw() -> void:
	var vp := size
	match game.mode:
		RidgeGame.Mode.SEATS:
			_draw_seats(vp)
			return
		RidgeGame.Mode.SHOP:
			_draw_play(vp)
			_draw_shop(vp)
			return
		RidgeGame.Mode.FINAL:
			_draw_play(vp)
			_draw_final(vp)
			return
	_draw_play(vp)


func _draw_play(vp: Vector2) -> void:
	var e := game.engine
	if e == null:
		return
	# the round and its land
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "ROUND %d OF %d" % [e.round_i + 1, e.rounds], LANDS[e.theme % LANDS.size()], HudKit.INK, HudKit.LEFT, 26)
	# the wind
	var wc := Vector2(vp.x * 0.5, 54)
	HudKit.panel(self, Rect2(wc.x - 130, 14, 260, 80), ACCENT)
	HudKit.text(self, wc + Vector2(0, -16), "WIND", 15, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
	var wl := clampf(absf(e.wind) / 8.0, 0.0, 1.0) * 90.0
	var dir := signf(e.wind)
	var y := wc.y + 12
	draw_line(Vector2(wc.x - 95, y), Vector2(wc.x + 95, y), Color(1, 1, 1, 0.15), 6.0)
	if wl > 2.0:
		draw_line(Vector2(wc.x, y), Vector2(wc.x + dir * wl, y), Color(0.6, 0.9, 1.0), 6.0)
		var tip := Vector2(wc.x + dir * (wl + 10), y)
		draw_colored_polygon(PackedVector2Array([tip, tip + Vector2(-dir * 14, -9), tip + Vector2(-dir * 14, 9)]), Color(0.6, 0.9, 1.0))
	HudKit.text(self, wc + Vector2(0, 38), "%.1f" % absf(e.wind) if absf(e.wind) > 0.05 else "CALM", 16, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	# a card per tank
	var n := e.players.size()
	for i in n:
		var p := e.players[i]
		var x := vp.x - 24 - (n - i) * 172
		var col: Color = p["colour"]
		var on: bool = e.turn == i and e.phase == R.Phase.AIM
		HudKit.panel(self, Rect2(x, 16, 164, 84), col if on else Color(col, 0.5), 12, 1.0 if p["alive"] else 0.5)
		HudKit.text(self, Vector2(x + 14, 42), p["name"] + ("" if not p["cpu"] else "  CPU"), 16, col.lightened(0.3), HudKit.label_font(), HudKit.LEFT)
		for w in p["wins"]:
			HudKit.gem(self, Vector2(x + 150 - w * 16, 36), 6.0, HudKit.GOLD)
		var hp: float = p["hp"] / 100.0
		draw_rect(Rect2(x + 14, 54, 136, 10), Color(0, 0, 0, 0.5))
		draw_rect(Rect2(x + 14, 54, 136 * hp, 10), HudKit.GOOD.lerp(HudKit.BAD, 1.0 - hp) if p["alive"] else Color(0.4, 0.4, 0.4))
		if float(p["shield"]) > 0.0:
			draw_rect(Rect2(x + 14, 66, 136 * float(p["shield"]) / R.SHIELD, 4), Color(0.55, 0.9, 1.0))
		HudKit.text(self, Vector2(x + 14, 90), "$%d" % p["money"], 15, HudKit.GOLD, HudKit.label_font(), HudKit.LEFT)
		HudKit.text(self, Vector2(x + 150, 90), "%d" % ceili(p["hp"]) if p["alive"] else "WRECKED", 15, HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
	# over the tanks: health and, for the one to play, a bobbing marker
	var cam := get_viewport().get_camera_3d()
	if cam:
		for i in n:
			var p := e.players[i]
			if not p["alive"]:
				continue
			var sp := cam.unproject_position(Vector3(p["x"], p["y"] + 2.7, 0))
			draw_rect(Rect2(sp + Vector2(-26, 0), Vector2(52, 6)), Color(0, 0, 0, 0.6))
			draw_rect(Rect2(sp + Vector2(-26, 0), Vector2(52 * p["hp"] / 100.0, 6)), p["colour"])
			if i == e.turn and e.phase == R.Phase.AIM:
				var b := sp + Vector2(0, -16 - 6 * sin(_t * 5.0))
				draw_colored_polygon(PackedVector2Array([b, b + Vector2(-10, -14), b + Vector2(10, -14)]), Color(p["colour"]).lightened(0.3))
				_protractor(cam, p)
		for p in _pops:
			if cam.is_position_behind(p["pos"]):
				continue
			var sp := cam.unproject_position(p["pos"]) - Vector2(0, p["t"] * 40.0)
			var c: Color = p["col"]
			HudKit.text(self, sp, p["text"], p["size"], Color(c, clampf(1.4 - p["t"], 0.0, 1.0)), HudKit.font(true), HudKit.CENTER)
	# the turn: angle, power, weapon
	if e.phase == R.Phase.AIM or e.phase == R.Phase.FLIGHT or e.phase == R.Phase.SETTLE:
		var p := e.current()
		var col: Color = p["colour"]
		var r := Rect2(vp.x * 0.5 - 330, vp.y - 118, 660, 92)
		HudKit.panel(self, r, col)
		HudKit.text(self, Vector2(r.position.x + 24, r.position.y + 34), "%s%s" % [p["name"], " (CPU)" if p["cpu"] else ""], 24, col.lightened(0.35), HudKit.font(true), HudKit.LEFT)
		HudKit.text(self, Vector2(r.position.x + 24, r.position.y + 70), "ANGLE  %d°" % roundi(p["angle"]), 20, HudKit.INK, HudKit.label_font(), HudKit.LEFT)
		HudKit.text(self, Vector2(r.position.x + 220, r.position.y + 30), "POWER", 15, HudKit.MUTED, HudKit.label_font(), HudKit.LEFT)
		draw_rect(Rect2(r.position.x + 220, r.position.y + 42, 200, 16), Color(0, 0, 0, 0.5))
		var pw: float = p["power"] / 100.0
		draw_rect(Rect2(r.position.x + 220, r.position.y + 42, 200 * pw, 16), HudKit.GOLD.lerp(HudKit.BAD, pw))
		HudKit.text(self, Vector2(r.position.x + 220, r.position.y + 80), "%d" % roundi(p["power"]), 18, HudKit.INK, HudKit.label_font(), HudKit.LEFT)
		var wpn: String = p["weapon"]
		var ammo := int(p["ammo"].get(wpn, 0))
		HudKit.text(self, Vector2(r.end.x - 24, r.position.y + 34), R.WEAPONS[wpn]["name"], 22, HudKit.GOLD, HudKit.font(true), HudKit.RIGHT)
		HudKit.text(self, Vector2(r.end.x - 24, r.position.y + 70), "∞" if ammo < 0 else "x%d" % ammo, 20, HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
		if not _taught and not game.demo and not p["cpu"] and e.phase == R.Phase.AIM:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 150), [["← →", "ANGLE"], ["↑ ↓", "POWER"], ["Q / E", "WEAPON"], ["SPACE", "FIRE"], ["MOUSE", "POINT, HOLD, LET GO"]])
	if _round_t < 2.5 and e.phase == R.Phase.AIM:
		HudKit.banner(self, vp, vp.y * 0.34, "ROUND %d" % (e.round_i + 1), LANDS[e.theme % LANDS.size()], ACCENT, clampf(2.5 - _round_t, 0.0, 1.0))
	if e.phase == R.Phase.ROUND_END and game.mode == RidgeGame.Mode.PLAY:
		var w := e.winner
		if w >= 0:
			HudKit.banner(self, vp, vp.y * 0.34, "%s WINS THE ROUND" % e.players[w]["name"], "+$%d" % R.ROUND_WIN, e.players[w]["colour"], 1.0)
		else:
			HudKit.banner(self, vp, vp.y * 0.34, "NOBODY LEFT", "A DRAW", HudKit.BAD, 1.0)
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 8), "DEMO  -  PRESS ANY KEY TO PLAY", 16, HudKit.INK, HudKit.label_font(), HudKit.CENTER)


## The aim around the tank whose turn it is: a half dial with a tick every 15 degrees, the needle along the barrel
## (as long as the power), the angle at its tip. Directions go through the camera, so the dial matches the scene.
func _protractor(cam: Camera3D, p: Dictionary) -> void:
	var piv := Vector3(p["x"], p["y"] + 1.15, 0)
	var c := cam.unproject_position(piv)
	var scr := func(deg: float) -> Vector2:
		var a := deg_to_rad(deg)
		return (cam.unproject_position(piv + Vector3(cos(a), sin(a), 0) * 3.0) - c).normalized()
	var r := 78.0
	var col: Color = Color(p["colour"]).lightened(0.35)
	var mine: bool = not p["cpu"]
	var alpha := 0.9 if mine else 0.45
	var pts := PackedVector2Array()
	for k in 37:
		pts.append(c + scr.call(k * 5.0) * r)
	draw_polyline(pts, Color(1, 1, 1, 0.35 * alpha), 2.0, true)
	for k in 13:
		var d: Vector2 = scr.call(k * 15.0)
		var big := k % 3 == 0
		draw_line(c + d * (r - (12.0 if big else 6.0)), c + d * r, Color(1, 1, 1, (0.7 if big else 0.4) * alpha), 2.0 if big else 1.0, true)
	var ang: float = p["angle"]
	var nd: Vector2 = scr.call(ang)
	var len := r * (0.3 + 0.7 * float(p["power"]) / 100.0)
	draw_line(c, c + nd * len, Color(0, 0, 0, 0.5 * alpha), 6.0, true)
	draw_line(c, c + nd * len, Color(col, alpha), 3.5, true)
	draw_circle(c + nd * len, 5.0, Color(col, alpha))
	draw_circle(c, 4.0, Color(1, 1, 1, alpha))
	HudKit.text(self, c + nd * (r + 22.0) + Vector2(0, 7), "%d°" % roundi(ang), 20, Color(HudKit.INK, alpha), HudKit.font(true), HudKit.CENTER)


func _draw_seats(vp: Vector2) -> void:
	var r := Rect2(vp.x * 0.5 - 300, vp.y * 0.5 - 220, 600, 440)
	HudKit.panel(self, r, ACCENT)
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 64), "RIDGEFIRE", 48, HudKit.GOLD, HudKit.font(true), HudKit.CENTER)
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 100), "TANKS  %d   (UP / DOWN)" % game.seats, 18, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	for i in game.seats:
		var y := r.position.y + 150 + i * 46
		var col: Color = R.COLOURS[i]
		HudKit.gem(self, Vector2(r.position.x + 150, y - 6), 10.0, col)
		HudKit.text(self, Vector2(r.position.x + 176, y), "%d  %s" % [i + 1, R.NAMES[i]], 22, col.lightened(0.3), HudKit.font(true), HudKit.LEFT)
		HudKit.text(self, Vector2(r.end.x - 150, y), "CPU" if game.cpu[i] else "PLAYER", 22, HudKit.MUTED if game.cpu[i] else HudKit.INK, HudKit.font(true), HudKit.RIGHT)
	HudKit.text(self, Vector2(vp.x * 0.5, r.end.y - 96), "1 - 4: PLAYER OR CPU      ROUNDS %d (LEFT / RIGHT)" % game.rounds, 17, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	HudKit.text(self, Vector2(vp.x * 0.5, r.end.y - 50), "ENTER TO START", 24, HudKit.GOLD.lerp(Color.WHITE, 0.3 * sin(_t * 4.0)), HudKit.font(true), HudKit.CENTER)


func _draw_shop(vp: Vector2) -> void:
	var e := game.engine
	var i := game.shop_player
	if i < 0:
		return
	var p := e.players[i]
	var r := Rect2(vp.x * 0.5 - 330, vp.y * 0.5 - 250, 660, 500)
	HudKit.panel(self, r, p["colour"])
	HudKit.text(self, Vector2(r.position.x + 32, r.position.y + 52), "%s'S SHOP" % p["name"], 30, Color(p["colour"]).lightened(0.3), HudKit.font(true), HudKit.LEFT)
	HudKit.text(self, Vector2(r.end.x - 32, r.position.y + 52), "$%d" % p["money"], 30, HudKit.GOLD, HudKit.font(true), HudKit.RIGHT)
	var items: Array = RidgeGame.SHOP_ITEMS
	for k in items.size() + 1:
		var y := r.position.y + 104 + k * 46
		var sel := k == game.shop_cursor
		if sel:
			draw_rect(Rect2(r.position.x + 18, y - 30, r.size.x - 36, 42), Color(1, 1, 1, 0.08))
		if k == items.size():
			HudKit.text(self, Vector2(vp.x * 0.5, y), "DONE  (TAB)", 22, HudKit.GOLD if sel else HudKit.INK, HudKit.font(true), HudKit.CENTER)
			continue
		var it: String = items[k]
		var name: String = "SHIELD" if it == "shield" else R.WEAPONS[it]["name"]
		var price: int = R.SHIELD_PRICE if it == "shield" else R.WEAPONS[it]["price"]
		var pack: String = "" if it == "shield" else "x%d" % R.WEAPONS[it]["pack"]
		var have := int(p["ammo"].get(it, 0)) if it != "shield" else int(p["shield"])
		var afford: bool = p["money"] >= price
		HudKit.text(self, Vector2(r.position.x + 40, y), "%s %s" % [name, pack], 21, HudKit.INK if afford else HudKit.MUTED, HudKit.font(true), HudKit.LEFT)
		HudKit.text(self, Vector2(r.position.x + 290, y), ITEM_TEXT.get(it, ""), 15, HudKit.MUTED, HudKit.label_font(), HudKit.LEFT)
		HudKit.text(self, Vector2(r.end.x - 120, y), "$%d" % price, 20, HudKit.GOLD if afford else HudKit.MUTED, HudKit.label_font(), HudKit.RIGHT)
		HudKit.text(self, Vector2(r.end.x - 36, y), str(have) if have > 0 else "", 18, HudKit.GOOD, HudKit.label_font(), HudKit.RIGHT)
	HudKit.text(self, Vector2(vp.x * 0.5, r.end.y - 14), "UP / DOWN   ENTER TO BUY", 15, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)


func _draw_final(vp: Vector2) -> void:
	var e := game.engine
	var s := e.standings()
	var r := Rect2(vp.x * 0.5 - 300, vp.y * 0.5 - 200, 600, 380)
	HudKit.panel(self, r, s[0]["colour"])
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 62), "%s WINS THE WAR" % s[0]["name"], 36, Color(s[0]["colour"]).lightened(0.3), HudKit.font(true), HudKit.CENTER)
	for k in s.size():
		var p: Dictionary = s[k]
		var y := r.position.y + 130 + k * 50
		HudKit.text(self, Vector2(r.position.x + 60, y), "%d.  %s" % [k + 1, p["name"]], 24, Color(p["colour"]).lightened(0.3), HudKit.font(true), HudKit.LEFT)
		HudKit.text(self, Vector2(r.end.x - 200, y), "%d ROUNDS" % p["wins"], 20, HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
		HudKit.text(self, Vector2(r.end.x - 50, y), "%d PTS" % p["score"], 20, HudKit.GOLD, HudKit.label_font(), HudKit.RIGHT)
	HudKit.text(self, Vector2(vp.x * 0.5, r.end.y - 30), "PRESS ENTER" if not game.demo else "", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
