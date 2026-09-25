extends Node2D
## Plays a cave with a flat debug view: the demo replay runs by itself, arrow keys take over.
## Milestone 1 of game 1; the real 3D presentation replaces the drawing later, the engine stays.

const E = preload("res://games/rocks/engine/cave_elements.gd")
const D = preload("res://games/rocks/engine/cave_directions.gd")

@export_file("*.bd") var cave_file := "res://games/rocks/packs/second-credit/first-light.bd"
@export var cave_index := 0
@export var level := 0

var cave: CaveStored
var engine: CaveEngine
var demo: CaveReplay
var playing_demo := true
var _elapsed_ms := 0.0
var _anim := 0.0
var _finished_ms := 0.0
var _score := 0

@onready var _hud: Label = $Hud


func _ready() -> void:
	var cs := BdcffLoader.load_file(cave_file)
	cave = cs.caves[cave_index]
	demo = cave.replays[0] if not cave.replays.is_empty() else null
	_restart()


func _restart() -> void:
	engine = CaveEngine.new(cave, level, demo.seed if demo else 0)
	playing_demo = demo != null
	if demo:
		demo.rewind()
	_elapsed_ms = 0.0
	_finished_ms = 0.0
	_score = 0


func _process(delta: float) -> void:
	_anim += delta
	var over := engine.player_state == CaveRendered.PlayerState.EXITED \
		or engine.player_state == CaveRendered.PlayerState.TIMEOUT or engine.player_state == CaveRendered.PlayerState.DIED
	if over:
		_finished_ms += delta * 1000.0
		if engine.player_state == CaveRendered.PlayerState.EXITED and engine.time > 0:
			_score += ReplayRunner.time_bonus(engine)
		if _finished_ms > 3000.0:
			_restart()
	else:
		_elapsed_ms += delta * 1000.0
		while _elapsed_ms >= engine.speed:
			_elapsed_ms -= engine.speed
			_step()
	_hud.text = "%s    diamonds %d / %d    time %d    score %d%s" % [cave.name, engine.diamonds_collected,
		engine.diamonds_needed, engine.time_visible(), _score, "    DEMO (arrow keys to play)" if playing_demo else ""]
	queue_redraw()


func _step() -> void:
	var move := D.STILL
	var fire := false
	if playing_demo:
		var m := demo.next_movement()
		if not m.is_empty():
			move = m[0]
			fire = m[1]
	else:
		move = D.from_keypress(Input.is_action_pressed("ui_up"), Input.is_action_pressed("ui_down"),
			Input.is_action_pressed("ui_left"), Input.is_action_pressed("ui_right"))
		fire = Input.is_key_pressed(KEY_SHIFT) or Input.is_key_pressed(KEY_CTRL)
	engine.iterate(move, fire, Input.is_key_pressed(KEY_ESCAPE) and not playing_demo)
	_score += engine.score


func _unhandled_input(event: InputEvent) -> void:
	if playing_demo and event is InputEventKey and event.pressed:
		if event.is_action("ui_up") or event.is_action("ui_down") or event.is_action("ui_left") or event.is_action("ui_right"):
			engine = CaveEngine.new(cave, level, 0)
			playing_demo = false
			_elapsed_ms = 0.0
			_score = 0


func _draw() -> void:
	var vp := get_viewport_rect().size
	var cell := floorf(minf(vp.x / engine.w, (vp.y - 40.0) / engine.h))
	var origin := Vector2((vp.x - cell * engine.w) * 0.5, 40.0 + (vp.y - 40.0 - cell * engine.h) * 0.5)
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.02, 0.05))
	for y in engine.h:
		for x in engine.w:
			_draw_cell(engine.map[y * engine.w + x], Rect2(origin + Vector2(x, y) * cell, Vector2(cell, cell)))


func _draw_cell(e: int, r: Rect2) -> void:
	var c := r.get_center()
	var s := r.size.x
	var pulse := 0.5 + 0.5 * sin(_anim * 6.0)
	e = E.nonscanned_pair(e)
	match e:
		E.SPACE:
			pass
		E.DIRT, E.DIRT2:
			draw_rect(r.grow(-1), Color(0.33, 0.2, 0.1))
			draw_rect(Rect2(r.position + Vector2(s * 0.2, s * 0.3), Vector2(s * 0.12, s * 0.12)), Color(0.4, 0.26, 0.14))
		E.BRICK, E.BRICK_NON_SLOPED:
			draw_rect(r.grow(-1), Color(0.55, 0.28, 0.16))
			draw_line(r.position + Vector2(0, s * 0.5), r.position + Vector2(s, s * 0.5), Color(0.3, 0.14, 0.08), 2)
		E.STEEL:
			draw_rect(r.grow(-1), Color(0.3, 0.34, 0.42))
			draw_rect(r.grow(-s * 0.3), Color(0.42, 0.47, 0.56))
		E.STONE, E.STONE_F:
			draw_circle(c, s * 0.44, Color(0.55, 0.53, 0.5))
			draw_circle(c - Vector2(s, s) * 0.12, s * 0.14, Color(0.7, 0.68, 0.65))
		E.DIAMOND, E.DIAMOND_F:
			var pts := PackedVector2Array([c + Vector2(0, -s * 0.42), c + Vector2(s * 0.36, 0), c + Vector2(0, s * 0.42),
				c + Vector2(-s * 0.36, 0)])
			draw_colored_polygon(pts, Color(0.3, 0.9, 1.0).lerp(Color.WHITE, pulse * 0.4))
		E.PLAYER, E.PLAYER_BOMB, E.PLAYER_GLUED:
			draw_circle(c, s * 0.4, Color(1.0, 0.85, 0.2))
			draw_circle(c + Vector2(-s * 0.13, -s * 0.08), s * 0.07, Color.BLACK)
			draw_circle(c + Vector2(s * 0.13, -s * 0.08), s * 0.07, Color.BLACK)
		E.PRE_OUTBOX, E.PRE_INVIS_OUTBOX:
			draw_rect(r.grow(-1), Color(0.3, 0.34, 0.42))
		E.OUTBOX, E.INVIS_OUTBOX:
			draw_rect(r.grow(-1), Color(0.2, 1.0, 0.4).lerp(Color.WHITE, pulse))
		E.INBOX, E.PRE_PL_1, E.PRE_PL_2, E.PRE_PL_3:
			draw_rect(r.grow(-1), Color(1.0, 0.85, 0.2, 0.3 + 0.7 * pulse))
		E.AMOEBA:
			draw_circle(c, s * 0.46, Color(0.2, 0.8, 0.25))
		E.MAGIC_WALL:
			draw_rect(r.grow(-1), Color(0.55, 0.28, 0.16).lerp(Color(0.9, 0.4, 1.0), pulse * float(engine.magic_wall_state == 1)))
		_:
			if e >= E.FIREFLY_1 and e <= E.FIREFLY_4:
				draw_rect(r.grow(-s * 0.18), Color(1.0, 0.45, 0.1).lerp(Color.YELLOW, pulse))
				draw_rect(r.grow(-s * 0.34), Color.BLACK)
			elif e >= E.BUTTER_1 and e <= E.BUTTER_4:
				draw_colored_polygon(PackedVector2Array([c + Vector2(-s * 0.4, -s * 0.35 * pulse - s * 0.05), c,
					c + Vector2(-s * 0.4, s * 0.35 * pulse + s * 0.05)]), Color(0.95, 0.3, 0.9))
				draw_colored_polygon(PackedVector2Array([c + Vector2(s * 0.4, -s * 0.35 * pulse - s * 0.05), c,
					c + Vector2(s * 0.4, s * 0.35 * pulse + s * 0.05)]), Color(0.95, 0.3, 0.9))
			elif e >= E.EXPLODE_1 and e <= E.EXPLODE_5 or e >= E.PRE_DIA_1 and e <= E.PRE_DIA_5:
				draw_circle(c, s * 0.5, Color(1.0, 0.9, 0.5, 0.9))
			else:
				draw_rect(r.grow(-s * 0.3), Color(0.8, 0.8, 0.8, 0.5))
