class_name LinksHud
extends Control
## Lantern Links HUD: the seats screen; the hole card on each fly-over (number, name, par); the hole and par; the
## players with their strokes on this hole and their round against par (the one to play lit); the power meter;
## the controls on the first hole; results (HOLE IN ONE, BIRDIE, PAR...), penalties and pick-ups; the scorecard
## between holes and at the end, with the winner.

const E = preload("res://games/lanternlinks/engine/links_engine.gd")
const HL = preload("res://games/lanternlinks/engine/links_hole.gd")
## What each feature of a hole does, in a line (shown on the hole card and while the first stroke is aimed).
const TIPS := {
	"chasm": "RAVINE: drive up the ramp hard enough to jump it",
	"water": "WATER: a stroke penalty, the ball comes back",
	"sand": "SAND slows the ball",
	"ice": "ICE: the ball hardly slows",
	"boost": "ARROWS push the ball their way",
	"pipe": "GLASS PIPE: roll into the amber mouth, out at the blue end",
	"windmill": "WINDMILL: time the putt between the sails",
	"loop": "LOOP: hit it firmly to go round",
	"mover": "SLIDING GATES open and close",
	"spinner": "TURNSTILE: it knocks the ball aside",
	"bumper": "BUMPERS kick the ball back",
}
const ACCENT := Color(1.0, 0.72, 0.38)
const GREEN := Color(0.45, 0.95, 0.55)

@export var game: LinksGame

var _banner := {}            ## {title, sub, col, t, life}
var _t := 0.0
var _taught := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.game_started.connect(func(e):
		e.event.connect(_on_event)
		_banner = {})


func _on_event(kind: String, d: Dictionary) -> void:
	var e := game.engine
	match kind:
		"holed":
			var over: int = int(d["strokes"]) - int(d["par"])
			var col := HudKit.GOLD if d["strokes"] == 1 or over < 0 else (GREEN if over == 0 else HudKit.INK)
			var sub := "%s  -  %d STROKE%s" % [e.players[d["player"]]["name"], d["strokes"], "" if d["strokes"] == 1 else "S"]
			_show(d["name"], sub, col, 2.2)
		"penalty":
			var water := e.hole.kind_at(e.ball.pos) == LinksHole.WATER
			_show("SPLASH" if water else "OVER THE EDGE", "ONE STROKE PENALTY", HudKit.BAD, 1.4)
		"pickup":
			_show("PICKED UP", "%d STROKES ON THIS HOLE" % d["strokes"], HudKit.MUTED, 1.5)
		"tee":
			if e.players.size() > 1:
				_show("%s TO PLAY" % e.player()["name"], "", e.player()["color"], 1.0)
		"shot":
			_taught = true


func _show(title: String, sub: String, col: Color, life: float) -> void:
	_banner = {"title": title, "sub": sub, "col": col, "t": 0.0, "life": life}


func _process(delta: float) -> void:
	_t += delta
	if not _banner.is_empty():
		_banner["t"] += delta
		if _banner["t"] > _banner["life"]:
			_banner = {}
	queue_redraw()


## The features of a hole, worst hazards first.
func _features(h: LinksHole) -> Array[String]:
	var out: Array[String] = []
	var kinds := {}
	for k in h.kind:
		kinds[k] = true
	if kinds.has(HL.CHASM): out.append("chasm")
	if kinds.has(HL.WATER): out.append("water")
	for g in h.gadgets:
		if not out.has(g["type"]): out.append(g["type"])
	if not h.boost.is_empty(): out.append("boost")
	if kinds.has(HL.ICE): out.append("ice")
	if kinds.has(HL.SAND): out.append("sand")
	return out


func _draw_tips(vp: Vector2, h: LinksHole, a: float) -> void:
	var lines: Array[String] = []
	for f in _features(h):
		if TIPS.has(f) and lines.size() < 3:
			lines.append(TIPS[f])
	if lines.is_empty():
		return
	var y := vp.y * 0.72 + 100.0 if game.engine.phase == E.Phase.INTRO else 140.0
	var w := 0.0
	for l in lines:
		w = maxf(w, HudKit.width(l, 18, HudKit.label_font()))
	HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5 - 24, y - 6, w + 48, lines.size() * 26 + 14), ACCENT, 12, a)
	for i in lines.size():
		HudKit.text(self, Vector2(vp.x * 0.5, y + 18 + i * 26), lines[i], 18, Color(HudKit.INK, a), HudKit.label_font(), HudKit.CENTER)


func _draw() -> void:
	var vp := size
	if game.setup:
		_draw_setup(vp)
		return
	var e := game.engine
	if e == null:
		return
	var h := e.hole
	# the hole
	HudKit.panel(self, Rect2(24, 16, 330, 96), ACCENT)
	HudKit.stat(self, 48, 20, "HOLE %d OF %d" % [e.hole_i + 1, e.holes.size()], h.name.to_upper(), HudKit.INK, HudKit.LEFT, 30)
	HudKit.text(self, Vector2(48, 100), "PAR %d" % h.par, 20, ACCENT, HudKit.label_font())
	# the players
	var rows := e.players.size()
	var ph := 34.0 + rows * 38.0
	var x0 := vp.x - 384
	HudKit.panel(self, Rect2(x0, 16, 360, ph), ACCENT)
	HudKit.text(self, Vector2(x0 + 24, 42), "PLAYER", 16, HudKit.MUTED, HudKit.label_font())
	HudKit.text(self, Vector2(x0 + 250, 42), "HOLE", 16, HudKit.MUTED, HudKit.label_font(), HudKit.RIGHT)
	HudKit.text(self, Vector2(x0 + 336, 42), "ROUND", 16, HudKit.MUTED, HudKit.label_font(), HudKit.RIGHT)
	for p in rows:
		var y := 80.0 + p * 38.0
		var pl: Dictionary = e.players[p]
		var active := e.player_index() == p and e.phase in [E.Phase.TEE, E.Phase.AIM, E.Phase.ROLL, E.Phase.SUNK, E.Phase.LOST]
		if active:
			draw_rect(Rect2(x0 + 8, y - 28, 344, 36), Color(pl["color"], 0.16 + 0.06 * sin(_t * 4.0)))
		draw_circle(Vector2(x0 + 30, y - 10), 8.0, pl["color"])
		HudKit.text(self, Vector2(x0 + 48, y), pl["name"], 22, HudKit.INK if active else HudKit.MUTED, HudKit.font())
		var here: int = pl["scores"][e.hole_i]
		var hs := str(here) if here > 0 else (str(e.strokes) if active and e.strokes > 0 else "-")
		HudKit.text(self, Vector2(x0 + 250, y), hs, 22, HudKit.INK, HudKit.font(), HudKit.RIGHT)
		HudKit.text(self, Vector2(x0 + 336, y), _par_str(e.to_par(p)), 22, _par_col(e.to_par(p)), HudKit.font(), HudKit.RIGHT)
	# the stroke and power while aiming
	if e.phase == E.Phase.AIM:
		var pl2 := e.player()
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 150), "%s  -  STROKE %d" % [pl2["name"], e.strokes + 1], 24, pl2["color"],
			HudKit.label_font(), HudKit.CENTER)
		if game.cpu_thinking:
			var dots := ".".repeat(1 + int(_t * 3.0) % 3)
			HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 116), "READING THE GREEN" + dots, 20, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
		_meter(vp, game.aim_power if game.charging else 0.0)
		if not _taught and not game.demo and not pl2["cpu"]:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 34), [["MOUSE", "aim"], ["CLICK + PULL BACK", "putt"],
				["SPACE", "hold and release"], ["TAB", "overview"]], 0.9)
	# the hole card on the fly-over
	if e.phase == E.Phase.INTRO:
		var a := clampf(e.phase_t * 3.0, 0.0, 1.0) * clampf((E.INTRO_T - e.phase_t) * 2.5, 0.0, 1.0)
		HudKit.banner(self, vp, vp.y * 0.72, h.name.to_upper(), "HOLE %d   -   PAR %d" % [e.hole_i + 1, h.par], ACCENT, a)
		_draw_tips(vp, h, a)
	elif e.phase == E.Phase.AIM and e.strokes == 0 and e.player_index() == 0:
		_draw_tips(vp, h, 0.85)
	if not _banner.is_empty():
		var bt: float = _banner["t"]
		var life: float = _banner["life"]
		var a2 := clampf(bt * 4.0, 0.0, 1.0) * clampf((life - bt) * 3.0, 0.0, 1.0)
		var pop := 1.0 + 0.25 * exp(-bt * 8.0)
		HudKit.banner(self, vp, vp.y * 0.36, _banner["title"], _banner["sub"], _banner["col"], a2, pop)
	if e.phase == E.Phase.CARD or e.phase == E.Phase.FINAL:
		_card(vp, e)
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 24), "DEMO  -  PRESS ANY KEY TO PLAY", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)


func _meter(vp: Vector2, p: float) -> void:
	var w := 420.0
	var r := Rect2(vp.x * 0.5 - w * 0.5, vp.y - 100, w, 22)
	HudKit.panel(self, r.grow(8), Color(0, 0, 0, 0), 10, 0.9)
	var segs := 40
	for i in segs:
		var f := float(i) / segs
		var col := Color(0.45, 1.0, 0.55).lerp(Color(1.0, 0.85, 0.3), smoothstep(0.3, 0.65, f)).lerp(Color(1.0, 0.35, 0.3), smoothstep(0.7, 1.0, f))
		var lit := f < p
		draw_rect(Rect2(r.position.x + f * w + 1, r.position.y, w / segs - 2, r.size.y), Color(col, 0.95 if lit else 0.14))
	HudKit.text(self, Vector2(r.end.x + 22, r.position.y + 19), "%d%%" % roundi(p * 100.0), 20, HudKit.INK if p > 0 else HudKit.MUTED,
		HudKit.label_font())


func _card(vp: Vector2, e: LinksEngine) -> void:
	var n := e.holes.size()
	var cw := 56.0
	var name_w := 190.0
	var w := name_w + cw * n + 150.0
	var rows := e.players.size()
	var hgt := 150.0 + rows * 48.0 + (70.0 if e.phase == E.Phase.FINAL else 0.0)
	var r := Rect2(vp.x * 0.5 - w * 0.5, vp.y * 0.5 - hgt * 0.5, w, hgt)
	var a := clampf(e.phase_t * 3.0, 0.0, 1.0)
	HudKit.panel(self, r, ACCENT, 16, a)
	var title := "SCORECARD" if e.phase == E.Phase.CARD else "FINAL CARD"
	HudKit.text(self, Vector2(r.position.x + 28, r.position.y + 48), title, 30, Color(ACCENT, a), HudKit.font(true))
	HudKit.text(self, Vector2(r.end.x - 28, r.position.y + 46), "THE LANTERN GARDEN", 18, Color(HudKit.MUTED, a), HudKit.label_font(), HudKit.RIGHT)
	var y := r.position.y + 92
	HudKit.text(self, Vector2(r.position.x + 28, y), "HOLE", 16, Color(HudKit.MUTED, a), HudKit.label_font())
	for i in n:
		var cx := r.position.x + name_w + cw * (i + 0.5)
		if i == e.hole_i:
			draw_rect(Rect2(cx - cw * 0.5 + 2, y - 22, cw - 4, 46 + rows * 48), Color(ACCENT, 0.12 * a))
		HudKit.text(self, Vector2(cx, y), str(i + 1), 18, Color(HudKit.INK, a), HudKit.label_font(), HudKit.CENTER)
		HudKit.text(self, Vector2(cx, y + 24), "PAR %d" % e.holes[i].par, 12, Color(HudKit.MUTED, a), HudKit.label_font(), HudKit.CENTER)
	HudKit.text(self, Vector2(r.end.x - 90, y), "TOTAL", 16, Color(HudKit.MUTED, a), HudKit.label_font(), HudKit.CENTER)
	var wins := e.winners() if e.phase == E.Phase.FINAL else ([] as Array[int])
	for p in rows:
		var yy := y + 70 + p * 48
		var pl: Dictionary = e.players[p]
		draw_circle(Vector2(r.position.x + 36, yy - 8), 8, Color(pl["color"], a))
		HudKit.text(self, Vector2(r.position.x + 54, yy), pl["name"], 22, Color(HudKit.INK, a), HudKit.font())
		for i in n:
			var s: int = pl["scores"][i]
			if s <= 0:
				continue
			var cx2 := r.position.x + name_w + cw * (i + 0.5)
			var over := s - e.holes[i].par
			if s == 1 or over < 0:
				draw_arc(Vector2(cx2, yy - 9), 17, 0, TAU, 28, Color(HudKit.GOLD, a), 2.0, true)
			elif over >= 2:
				draw_rect(Rect2(cx2 - 16, yy - 25, 32, 32), Color(HudKit.BAD, 0.6 * a), false, 2.0)
			HudKit.text(self, Vector2(cx2, yy), str(s), 22, Color(HudKit.INK, a), HudKit.font(), HudKit.CENTER)
		var tp := e.to_par(p)
		HudKit.text(self, Vector2(r.end.x - 90, yy), "%d  %s" % [e.total(p), _par_str(tp)], 22, Color(_par_col(tp), a), HudKit.font(), HudKit.CENTER)
	if e.phase == E.Phase.FINAL:
		var names: Array[String] = []
		for wi in wins:
			names.append(e.players[wi]["name"])
		var line := (" AND ".join(names) + (" WIN" if names.size() > 1 else " WINS")) if rows > 1 else \
			"ROUND OF %d  (%s)" % [e.total(0), _par_str(e.to_par(0))]
		HudKit.text(self, Vector2(vp.x * 0.5, r.end.y - 36), line, 30, Color(HudKit.GOLD, a), HudKit.font(true), HudKit.CENTER)
		if not game.demo:
			HudKit.text(self, Vector2(vp.x * 0.5, r.end.y + 44), "PRESS ENTER FOR A NEW ROUND", 20, Color(HudKit.INK, a),
				HudKit.label_font(), HudKit.CENTER)
	elif not game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, r.end.y + 40), "PRESS ENTER FOR THE NEXT HOLE", 20, Color(HudKit.INK, a * 0.8),
			HudKit.label_font(), HudKit.CENTER)


func _draw_setup(vp: Vector2) -> void:
	var w := 640.0
	var hgt := 250.0 + game.seats.size() * 56.0
	var r := Rect2(vp.x * 0.5 - w * 0.5, vp.y * 0.5 - hgt * 0.5, w, hgt)
	HudKit.panel(self, r, ACCENT)
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 70), "LANTERN LINKS", 54, ACCENT, HudKit.font(true), HudKit.CENTER)
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 108), "NINE HOLES FROM GOLDEN HOUR INTO THE NIGHT", 18, HudKit.MUTED,
		HudKit.label_font(), HudKit.CENTER)
	for i in game.seats.size():
		var s: Dictionary = game.seats[i]
		var y := r.position.y + 170 + i * 56
		draw_circle(Vector2(r.position.x + 70, y - 9), 10, E.COLORS[i])
		HudKit.text(self, Vector2(r.position.x + 96, y), s["name"], 26, HudKit.INK, HudKit.font())
		HudKit.keycap(self, Vector2(r.end.x - 200, y), str(i + 1), "CPU" if s["cpu"] else "PERSON", 1.0)
	HudKit.hints(self, Vector2(vp.x * 0.5, r.end.y - 30), [["LEFT RIGHT", "players"], ["1-4", "person or CPU"], ["ENTER", "tee off"]])


static func _par_str(v: int) -> String:
	return "E" if v == 0 else ("%+d" % v)


static func _par_col(v: int) -> Color:
	return HudKit.GOLD if v < 0 else (HudKit.INK if v == 0 else Color(1.0, 0.7, 0.6))
