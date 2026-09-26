class_name BastionHud
extends Control
## Bastion Coast HUD: phase banner, phase timer, score, round, cannons to place, controls hint, game over.

const P = BastionEngine.Phase
const PHASE_NAME := {P.CHOOSE: "CHOOSE A CASTLE", P.CANNONS: "PLACE CANNONS", P.BATTLE: "BATTLE", P.BUILD: "REPAIR"}
const PHASE_COL := {P.CHOOSE: Color(0.94, 0.95, 1.0), P.CANNONS: Color(1.0, 0.83, 0.35),
	P.BATTLE: Color(1.0, 0.55, 0.3), P.BUILD: Color(0.45, 0.75, 1.0)}
const HINTS := {
	P.CHOOSE: [["ARROWS", "pick a castle"], ["SPACE", "choose it"]],
	P.CANNONS: [["ARROWS / MOUSE", "move"], ["SPACE / CLICK", "place a cannon inside your walls"]],
	P.BATTLE: [["ARROWS / MOUSE", "aim"], ["SPACE / CLICK", "fire"]],
	P.BUILD: [["ARROWS / MOUSE", "move"], ["R / RIGHT CLICK", "rotate"], ["SPACE / CLICK", "place the wall"]],
}

@export var game: BastionGame

var _banner := ""
var _banner_sub := ""
var _blocked := ""
var _blocked_check := 0.0
var _banner_t := 10.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.started.connect(func(e): e.event.connect(_on_event); _show("CHOOSE YOUR CASTLE", "YOUR HOME FOR THE WHOLE GAME"))
	if game.engine:
		game.engine.event.connect(_on_event)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"phase":
			match d["phase"]:
				P.CANNONS: _show("ROUND %d" % d["round"], "PLACE YOUR CANNONS")
				P.BATTLE: _show("BATTLE!", "SINK THE FLEET")
				P.BUILD: _show("REPAIR!", "CLOSE THE WALLS AROUND A CASTLE")
		"game_over":
			_show("THE COAST IS LOST")
		"island_held":
			_show("ISLAND HELD")


func _show(text: String, sub := "") -> void:
	_banner = text
	_banner_sub = sub
	_banner_t = 0.0


func _process(delta: float) -> void:
	_banner_t += delta
	_blocked_check -= delta
	if _blocked_check <= 0.0 and game.engine:
		_blocked = game.engine.blocked()
		_blocked_check = 0.25
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	var over := e.phase == P.GAME_OVER
	# top left: round and the phase's own counter
	HudKit.panel(self, Rect2(24, 16, 380, 84), Color(0.4, 0.7, 1.0))
	HudKit.stat(self, 48, 20, "ROUND", "%d" % maxi(1, e.round_number), HudKit.INK)
	var extra := []  # [label, value] columns after the round
	match e.phase:
		P.CANNONS: extra = [["CANNONS TO PLACE", e.cannons_to_place]]
		P.BATTLE: extra = [["SHIPS", e.ships.size()], ["CANNONS", e.active_cannons()]]
		P.BUILD: extra = [["CASTLES ENCLOSED", e.enclosed_castles.size()]]
		P.CHOOSE: extra = [["CASTLES", e.map.castles.size()]]
	for i in extra.size():
		var x := 380.0 - (extra.size() - 1 - i) * 130.0
		HudKit.stat(self, x, 20, extra[i][0], "%d" % extra[i][1], HudKit.INK, HudKit.RIGHT)
	# top centre: phase name, seconds left and a bar
	if not over:
		var total: float = {P.CHOOSE: BastionEngine.CHOOSE_SECONDS, P.CANNONS: BastionEngine.CANNON_SECONDS,
			P.BATTLE: BastionEngine.BATTLE_SECONDS, P.BUILD: BastionEngine.BUILD_SECONDS}.get(e.phase, 1.0)
		var frac := clampf(e.phase_left / total, 0.0, 1.0)
		var col: Color = PHASE_COL.get(e.phase, HudKit.INK) if frac > 0.25 else HudKit.BAD
		HudKit.panel(self, Rect2(vp.x * 0.5 - 170, 16, 340, 96), col)
		HudKit.stat(self, vp.x * 0.5, 20, PHASE_NAME.get(e.phase, ""), "%d" % ceili(maxf(0.0, e.phase_left)), col, HudKit.CENTER, 40)
		draw_rect(Rect2(vp.x * 0.5 - 140, 98, 280, 4), Color(1, 1, 1, 0.1))
		draw_rect(Rect2(vp.x * 0.5 - 140, 98, 280 * frac, 4), col)
	# top right: score
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), HudKit.GOLD)
	HudKit.stat(self, vp.x - 48, 20, "SCORE", "%07d" % game.total_score(), HudKit.GOLD, HudKit.RIGHT)
	if game.pack:  # campaign: which island, and how long to hold it
		HudKit.panel(self, Rect2(vp.x - 324, 108, 300, 44), Color(1, 1, 1, 0.2), 14, 0.9)
		var left := maxi(0, e.map.rounds - maxi(0, e.round_number - 1))  # a round counts once its repair ends
		HudKit.text(self, Vector2(vp.x - 304, 138), "ISLAND %d / %d" % [game.island + 1, game.pack.levels.size()], 18, HudKit.INK, HudKit.label_font())
		HudKit.text(self, Vector2(vp.x - 44, 138), "HOLD %d MORE" % left if not e.won else "HELD", 18, HudKit.GOLD, HudKit.label_font(), HudKit.RIGHT)
	# castle status: sealed or how many holes are left
	if e.phase != P.CHOOSE and not over and not e.castle_holes.is_empty():
		var castles: Array = e.castle_holes.keys()
		castles.sort_custom(func(a, b): return a == e.home_castle or (b != e.home_castle and a < b))
		var h := 44.0 + castles.size() * 38.0
		HudKit.panel(self, Rect2(24, 124, 330, h), Color(0, 0, 0, 0), 14, 0.9)
		HudKit.text(self, Vector2(44, 152), "CASTLES", 15, HudKit.MUTED, HudKit.label_font())
		var yy := 190.0
		for c in castles:
			var holes: Array = e.castle_holes[c]
			var label := "HOME" if c == e.home_castle else "CASTLE %d" % (c + 1)
			var status := "SEALED" if holes.is_empty() else ("OPEN" if holes.size() > BastionEngine.HOLE_LIMIT
				else "%d HOLE%s" % [holes.size(), "" if holes.size() == 1 else "S"])
			var col := HudKit.GOOD if holes.is_empty() else HudKit.BAD
			var pulse := 1.0 if holes.is_empty() else 0.75 + 0.25 * sin(_banner_t * 6.0)
			draw_circle(Vector2(52, yy - 9), 7.0, Color(col, pulse), true, -1.0, true)
			draw_circle(Vector2(52, yy - 9), 12.0, Color(col, 0.18 * pulse), true, -1.0, true)
			HudKit.text(self, Vector2(72, yy), label, 24, HudKit.INK)
			HudKit.text(self, Vector2(334, yy), status, 24, col, null, HudKit.RIGHT)
			yy += 38.0
	# banner
	if _banner != "" and _banner_t < 2.2 and not over:
		var a := clampf(minf(_banner_t * 4.0, (2.2 - _banner_t) * 3.0), 0.0, 1.0)
		var pop := 1.0 + 0.25 * exp(-_banner_t * 8.0)
		HudKit.banner(self, vp, vp.y * 0.42, _banner, _banner_sub, HudKit.GOLD, a, pop)
	# blocked: nowhere to put the current piece or cannon (the timer keeps running)
	if _blocked != "" and not over:
		var msg := "NO ROOM FOR THIS PIECE  -  WAIT FOR THE TIMER" if _blocked == "piece" else "NO ROOM LEFT FOR CANNONS"
		var a := 0.75 + 0.25 * sin(_banner_t * 6.0)
		var w := HudKit.width(msg, 28, HudKit.font(true)) + 80.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5, vp.y - 150, w, 60), Color(HudKit.BAD, a), 30)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 109), msg, 28, Color(1, 0.88, 0.84, a), HudKit.font(true), HudKit.CENTER)
	# hints
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var w := HudKit.width(msg, 24, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5, vp.y - 66, w, 46), Color(0, 0, 0, 0), 23, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 34), msg, 24, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	elif not over:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 30), HINTS.get(e.phase, []))
	if over and e.won:
		var title := "THE COASTLINE IS OURS" if game.campaign_done else "ISLAND HELD"
		HudKit.banner(self, vp, vp.y * 0.45, title, "%s   -   SCORE %d" % [e.map.name.to_upper(), game.total_score()], HudKit.GOOD, 1.0)
		if game.campaign_done and not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.45 + 150), [["ENTER", "play again"], ["ESC", "menu"]])
	elif over:
		draw_rect(Rect2(Vector2.ZERO, vp), Color(0, 0, 0, 0.45))
		HudKit.banner(self, vp, vp.y * 0.45, "THE ISLAND FALLS" if game.pack else "GAME OVER", "SCORE %d   -   %d ROUNDS   -   %d SHIPS SUNK" % [game.total_score(),
			e.round_number, e.ships_sunk], HudKit.GOLD, 1.0)
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.45 + 150), [["ENTER", "try the island again"], ["ESC", "menu"]] if game.pack and not game.demo else [["ESC", "menu"]])
