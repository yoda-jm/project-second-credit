class_name BastionHud
extends Control
## Bastion Coast HUD: phase banner, phase timer, score, round, cannons to place, controls hint, game over.
## Versus: a card per player (colour, score, castle status, controls), the F2 chooser and the winner banner.

const P = BastionEngine.Phase
const PHASE_NAME := {P.CHOOSE: "CHOOSE A CASTLE", P.CANNONS: "PLACE CANNONS", P.BATTLE: "BATTLE", P.BUILD: "REPAIR"}
const PHASE_COL := {P.CHOOSE: Color(0.94, 0.95, 1.0), P.CANNONS: Color(1.0, 0.83, 0.35),
	P.BATTLE: Color(1.0, 0.55, 0.3), P.BUILD: Color(0.45, 0.75, 1.0)}
const HINTS := {
	P.CHOOSE: [["ARROWS", "pick a castle"], ["SPACE", "choose it"], ["F2", "versus"]],
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
	game.started.connect(func(e):
		e.event.connect(_on_event)
		if e.versus:
			_show("VERSUS", "%s  -  CHOOSE YOUR CASTLES" % e.map.name.to_upper())
		else:
			_show("CHOOSE YOUR CASTLE", "YOUR HOME FOR THE WHOLE GAME"))
	if game.engine:
		game.engine.event.connect(_on_event)


func _on_event(kind: String, d: Dictionary) -> void:
	if game.engine and game.engine.versus:
		match kind:
			"phase":
				match d["phase"]:
					P.CANNONS: _show("ROUND %d" % d["round"], "PLACE YOUR CANNONS")
					P.BATTLE: _show("BATTLE!", "BREAK THEIR WALLS")
					P.BUILD: _show("REPAIR!", "CLOSE YOUR WALLS AROUND A CASTLE")
			"player_out":
				_show("%s IS OUT" % BastionGame.PLAYER_NAMES[d["player"]], "NO CASTLE ENCLOSED")
		return
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
	if e.versus:
		_draw_versus(e, vp)
	else:
		_draw_solo(e, vp)
	if game.choosing:
		_draw_chooser(vp)


func _draw_solo(e: BastionEngine, vp: Vector2) -> void:
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
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY  -  F2 VERSUS"
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


# ------------------------------------------------------------------ versus

const CONTROLS: Array[String] = ["ARROWS  SPACE  R  /  MOUSE", "W A S D  F  G", "GAMEPAD  A  B"]


func _draw_versus(e: BastionEngine, vp: Vector2) -> void:
	var over := e.phase == P.GAME_OVER
	# top left: the round (and how many the coast is played for)
	HudKit.panel(self, Rect2(24, 16, 240, 84), Color(0.4, 0.7, 1.0))
	HudKit.stat(self, 48, 20, "ROUND", "%d" % maxi(1, e.round_number) + (" / %d" % e.map.rounds if e.map.rounds > 0 else ""), HudKit.INK)
	# top centre: the phase clock, shared by everyone
	if not over:
		_phase_clock(e, vp)
	# top right: the coast
	var name := e.map.name.to_upper()
	var nw := HudKit.width(name, 22, HudKit.label_font()) + 60.0
	HudKit.panel(self, Rect2(vp.x - 24 - nw, 16, nw, 84), HudKit.GOLD)
	HudKit.text(self, Vector2(vp.x - 54, 46), "VERSUS", 15, HudKit.MUTED, HudKit.label_font(), HudKit.RIGHT)
	HudKit.text(self, Vector2(vp.x - 54, 80), name, 22, HudKit.INK, HudKit.label_font(), HudKit.RIGHT)
	# bottom: a card per player
	var n := e.players.size()
	var cw := minf(330.0, (vp.x - 48.0 - (n - 1) * 16.0) / n)
	var total := n * cw + (n - 1) * 16.0
	for pl in e.players:
		_player_card(e, pl, Rect2(vp.x * 0.5 - total * 0.5 + pl.index * (cw + 16.0), vp.y - 132, cw, 116))
	# banner
	if _banner != "" and _banner_t < 2.2 and not over:
		var a := clampf(minf(_banner_t * 4.0, (2.2 - _banner_t) * 3.0), 0.0, 1.0)
		var pop := 1.0 + 0.25 * exp(-_banner_t * 8.0)
		HudKit.banner(self, vp, vp.y * 0.42, _banner, _banner_sub, HudKit.GOLD, a, pop)
	if game.demo and not over:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY THIS MATCH  -  F2 PLAYERS"
		var w := HudKit.width(msg, 20, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5, 122, w, 40), Color(0, 0, 0, 0), 20, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, 150), msg, 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	if over:
		draw_rect(Rect2(Vector2.ZERO, vp), Color(0, 0, 0, 0.35))
		var w := e.winner
		var col: Color = BastionGame.PLAYER_COLORS[maxi(0, w)]
		var sub := "SCORE %d   -   %d ROUNDS" % [e.players[maxi(0, w)].score, e.round_number]
		HudKit.banner(self, vp, vp.y * 0.42, "%s WINS" % BastionGame.PLAYER_NAMES[maxi(0, w)], sub, col, 1.0)
		if not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.42 + 130), [["ENTER", "rematch"], ["F2", "players"], ["ESC", "menu"]])


func _phase_clock(e: BastionEngine, vp: Vector2) -> void:
	var total: float = {P.CHOOSE: BastionEngine.CHOOSE_SECONDS, P.CANNONS: BastionEngine.CANNON_SECONDS,
		P.BATTLE: BastionEngine.BATTLE_SECONDS, P.BUILD: BastionEngine.BUILD_SECONDS}.get(e.phase, 1.0)
	var frac := clampf(e.phase_left / total, 0.0, 1.0)
	var col: Color = PHASE_COL.get(e.phase, HudKit.INK) if frac > 0.25 else HudKit.BAD
	HudKit.panel(self, Rect2(vp.x * 0.5 - 170, 16, 340, 96), col)
	HudKit.stat(self, vp.x * 0.5, 20, PHASE_NAME.get(e.phase, ""), "%d" % ceili(maxf(0.0, e.phase_left)), col, HudKit.CENTER, 40)
	draw_rect(Rect2(vp.x * 0.5 - 140, 98, 280, 4), Color(1, 1, 1, 0.1))
	draw_rect(Rect2(vp.x * 0.5 - 140, 98, 280 * frac, 4), col)


## One player's card: name and score, what they are doing this phase, and their controls.
func _player_card(e: BastionEngine, pl: BastionPlayer, r: Rect2) -> void:
	var col: Color = BastionGame.PLAYER_COLORS[pl.index]
	var a := 1.0 if pl.alive else 0.55
	HudKit.panel(self, r, Color(col, a), 14, a)
	var x0 := r.position.x + 22.0
	var x1 := r.end.x - 22.0
	draw_circle(Vector2(x0 + 8, r.position.y + 34), 8.0, Color(col, a), true, -1.0, true)
	draw_circle(Vector2(x0 + 8, r.position.y + 34), 14.0, Color(col, 0.2 * a), true, -1.0, true)
	HudKit.text(self, Vector2(x0 + 28, r.position.y + 44), BastionGame.PLAYER_NAMES[pl.index], 26, Color(col.lightened(0.3), a), HudKit.font(true))
	HudKit.text(self, Vector2(x1, r.position.y + 44), "%06d" % pl.score, 26, Color(HudKit.GOLD, a), HudKit.font(true), HudKit.RIGHT)
	var status := ""
	var scol := HudKit.INK
	if not pl.alive:
		status = "OUT IN ROUND %d" % pl.out_round
		scol = HudKit.BAD
	else:
		match e.phase:
			P.CHOOSE:
				status = "READY" if pl.home_castle >= 0 else "PICK A CASTLE"
				scol = HudKit.GOOD if pl.home_castle >= 0 else HudKit.INK
			P.CANNONS:
				status = "CANNONS TO PLACE  %d" % pl.cannons_to_place if pl.cannons_to_place > 0 else "READY"
				scol = HudKit.GOLD if pl.cannons_to_place > 0 else HudKit.GOOD
			P.BATTLE:
				status = "CANNONS  %d" % e.active_cannons(pl.index)
			P.BUILD:
				var holes: Array = pl.castle_holes.get(pl.home_castle, [])
				if not pl.enclosed_castles.is_empty():
					status = "SEALED  -  %d CASTLE%s" % [pl.enclosed_castles.size(), "" if pl.enclosed_castles.size() == 1 else "S"]
					scol = HudKit.GOOD
				else:
					status = "OPEN" if holes.size() > BastionEngine.HOLE_LIMIT else "%d HOLE%s" % [holes.size(), "" if holes.size() == 1 else "S"]
					scol = HudKit.BAD
			P.GAME_OVER:
				status = "WINNER" if e.winner == pl.index else ""
				scol = HudKit.GOOD
	HudKit.text(self, Vector2(x0, r.position.y + 78), status, 20, Color(scol, a), HudKit.label_font())
	var ctl := "CPU" if game.demo else CONTROLS[pl.index]
	if not game.demo and pl.index < 2 and game._pads.values().has(pl.index):
		ctl += "  /  PAD"
	HudKit.text(self, Vector2(x0, r.position.y + 102), ctl, 15, Color(HudKit.MUTED, a), HudKit.label_font())


func _draw_chooser(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0, 0, 0, 0.45))
	var r := Rect2(vp.x * 0.5 - 330, vp.y * 0.5 - 200, 660, 400)
	HudKit.panel(self, r, HudKit.GOLD, 18)
	HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 70), "VERSUS", 52, HudKit.GOLD, HudKit.font(true), HudKit.CENTER)
	for i in 2:
		var n := i + 2
		var box := Rect2(vp.x * 0.5 - 290 + i * 300, r.position.y + 100, 280, 150)
		var on := game.choose_count == n
		HudKit.panel(self, box, HudKit.GOLD if on else Color(0, 0, 0, 0), 14, 1.0 if on else 0.6)
		HudKit.text(self, Vector2(box.get_center().x, box.position.y + 70), "%d" % n, 56, HudKit.INK if on else HudKit.MUTED, HudKit.font(true), HudKit.CENTER)
		HudKit.text(self, Vector2(box.get_center().x, box.position.y + 108), "PLAYERS", 20, HudKit.INK if on else HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
		for k in n:
			draw_circle(Vector2(box.get_center().x - (n - 1) * 14 + k * 28, box.position.y + 130), 8.0, BastionGame.PLAYER_COLORS[k], true, -1.0, true)
	var lines := ["BLUE  -  ARROWS, SPACE, R  OR THE MOUSE", "RED  -  W A S D, F, G", "GOLD  -  A GAMEPAD (A, B)"]
	for i in game.choose_count:
		HudKit.text(self, Vector2(vp.x * 0.5, r.position.y + 290 + i * 26), lines[i], 17, BastionGame.PLAYER_COLORS[i].lightened(0.3), HudKit.label_font(), HudKit.CENTER)
	HudKit.hints(self, Vector2(vp.x * 0.5, r.end.y + 50), [["2 / 3", "players"], ["ENTER", "start"], ["F2", "back"]])
