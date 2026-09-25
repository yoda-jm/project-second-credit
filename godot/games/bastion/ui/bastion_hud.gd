class_name BastionHud
extends Control
## Bastion Coast HUD: phase banner, phase timer, score, round, cannons to place, controls hint, game over.

const P = BastionEngine.Phase
const GOLD := Color(1.0, 0.83, 0.35)

@export var game: BastionGame

var _banner := ""
var _banner_t := 10.0
var _font: Font
var _big: Font


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_font = load("res://core/fonts/kenney_future_narrow.ttf")
	_big = load("res://core/fonts/kenney_future.ttf")
	game.started.connect(func(e): e.event.connect(_on_event); _show("CHOOSE YOUR CASTLE"))
	if game.engine:
		game.engine.event.connect(_on_event)


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"phase":
			match d["phase"]:
				P.CANNONS: _show("ROUND %d  -  PLACE CANNONS" % d["round"])
				P.BATTLE: _show("BATTLE!")
				P.BUILD: _show("REPAIR!")
		"game_over":
			_show("THE COAST IS LOST")


func _show(text: String) -> void:
	_banner = text
	_banner_t = 0.0


func _process(delta: float) -> void:
	_banner_t += delta
	queue_redraw()


func _text(pos: Vector2, s: String, size: int, col: Color, font: Font = null, center := false) -> void:
	var f := font if font else _font
	if center:
		pos.x -= f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x * 0.5
	draw_string_outline(f, pos, s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, maxi(4, size / 8), Color(0, 0, 0, col.a * 0.85))
	draw_string(f, pos, s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	draw_rect(Rect2(0, 0, vp.x, 70), Color(0.02, 0.03, 0.06, 0.55))
	_text(Vector2(30, 48), "BASTION COAST", 34, GOLD, _big)
	_text(Vector2(vp.x - 30 - _font.get_string_size("%07d" % e.score, HORIZONTAL_ALIGNMENT_LEFT, -1, 38).x, 48),
		"%07d" % e.score, 38, Color.WHITE)
	var info := "ROUND %d" % maxi(1, e.round_number)
	if e.phase == P.CANNONS:
		info += "    CANNONS TO PLACE: %d" % e.cannons_to_place
	elif e.phase == P.BATTLE:
		info += "    SHIPS: %d    CANNONS READY: %d" % [e.ships.size(), e.active_cannons()]
	elif e.phase == P.BUILD:
		info += "    CASTLES ENCLOSED: %d" % e.enclosed_castles.size()
	_text(Vector2(vp.x * 0.5, 46), info, 28, Color(0.9, 0.93, 1.0), null, true)
	# phase timer
	var total: float = {P.CHOOSE: BastionEngine.CHOOSE_SECONDS, P.CANNONS: BastionEngine.CANNON_SECONDS,
		P.BATTLE: BastionEngine.BATTLE_SECONDS, P.BUILD: BastionEngine.BUILD_SECONDS}.get(e.phase, 1.0)
	var frac := clampf(e.phase_left / total, 0.0, 1.0)
	if e.phase != P.GAME_OVER:
		draw_rect(Rect2(0, 70, vp.x, 8), Color(0, 0, 0, 0.4))
		var col := Color(0.35, 0.65, 1.0) if frac > 0.25 else Color(1.0, 0.35, 0.25)
		draw_rect(Rect2(0, 70, vp.x * frac, 8), col)
		_text(Vector2(vp.x * 0.5, 120), "%d" % ceili(maxf(0.0, e.phase_left)), 44, Color(1, 1, 1, 0.9), _big, true)
	# banner
	if _banner != "" and _banner_t < 2.2:
		var a := clampf(minf(_banner_t * 4.0, (2.2 - _banner_t) * 3.0), 0.0, 1.0)
		var size := int(88 * (1.0 + 0.25 * exp(-_banner_t * 8.0)))
		draw_rect(Rect2(0, vp.y * 0.42 - 70, vp.x, 110), Color(0, 0, 0, 0.35 * a))
		_text(Vector2(vp.x * 0.5, vp.y * 0.42 + 10), _banner, size, Color(GOLD, a), _big, true)
	# hints
	var hint := ""
	match e.phase:
		P.CHOOSE: hint = "arrows: pick a castle     space: choose it"
		P.CANNONS: hint = "arrows or mouse: move     space or click: place a cannon inside your walls"
		P.BATTLE: hint = "arrows or mouse: aim     space or click: fire"
		P.BUILD: hint = "arrows or mouse: move     R or right click: rotate     space or click: place the wall"
	if game.demo:
		hint = "DEMO  -  press any key to play"
	_text(Vector2(vp.x * 0.5, vp.y - 30), hint, 26, Color(0.9, 0.93, 1.0, 0.85), null, true)
	if e.phase == P.GAME_OVER:
		draw_rect(Rect2(Vector2.ZERO, vp), Color(0, 0, 0, 0.45))
		_text(Vector2(vp.x * 0.5, vp.y * 0.45), "GAME OVER", 110, GOLD, _big, true)
		_text(Vector2(vp.x * 0.5, vp.y * 0.45 + 80), "score %d   -   %d rounds   -   %d ships sunk" % [e.score, e.round_number, e.ships_sunk],
			34, Color.WHITE, null, true)
		_text(Vector2(vp.x * 0.5, vp.y * 0.45 + 140), "esc: menu", 28, Color(0.8, 0.85, 0.95), null, true)
