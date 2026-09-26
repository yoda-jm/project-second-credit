class_name BootsHud
extends Control
## Muddy Boots HUD: the mission, the squad and the recruits left, grenades and rockets, the goals, banners.

const E = preload("res://games/boots/engine/boots_engine.gd")
const OLIVE := Color(0.6, 0.8, 0.4)
const GOAL_TEXT := {"kill": "WIPE OUT THE ENEMY", "destroy": "DESTROY THE HUTS", "rescue": "RESCUE THE HOSTAGES"}

@export var game: BootsGame

var _banner := ""
var _sub := ""
var _col := HudKit.GOLD
var _t := 10.0
var _len := 2.5


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.mission_started.connect(func(e):
		e.event.connect(_on_event)
		_show("MISSION %d" % (game.mission + 1), e.map.name.to_upper(), OLIVE, 3.0))
	game.campaign_over.connect(func(won): _show("CAMPAIGN COMPLETE" if won else "OUT OF RECRUITS", "", HudKit.GOLD if won else HudKit.BAD, 99.0))


func _on_event(kind: String, _d: Dictionary) -> void:
	match kind:
		"won": _show("MISSION COMPLETE", "", HudKit.GOOD, 3.5)
		"lost": _show("SQUAD LOST", "TRY AGAIN" if game.recruits > 0 else "", HudKit.BAD, 3.5)
		"hut_destroyed": _pop("HUT DESTROYED")
		"rescued": _pop("HOSTAGE RESCUED")
		"pickup": _pop("SUPPLIES")


func _pop(text: String) -> void:
	if _t > _len:
		_show(text, "", HudKit.GOLD, 1.2)


func _show(text: String, sub: String, col: Color, secs: float) -> void:
	_banner = text
	_sub = sub
	_col = col
	_t = 0.0
	_len = secs


func _process(delta: float) -> void:
	if not game.story_open:  # the mission banner waits behind a story card
		_t += delta
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	HudKit.panel(self, Rect2(24, 16, 420, 84), OLIVE)
	HudKit.stat(self, 48, 20, "MISSION %d / %d" % [game.mission + 1, game.missions.size()], e.map.name.to_upper(), HudKit.INK, HudKit.LEFT, 26)
	# squad and recruits
	HudKit.panel(self, Rect2(vp.x * 0.5 - 200, 16, 400, 84), OLIVE)
	HudKit.text(self, Vector2(vp.x * 0.5 - 180, 38), "SQUAD", 15, HudKit.MUTED, HudKit.label_font())
	for i in 4:
		var alive := i < e.alive_soldiers().size()
		_helmet(Vector2(vp.x * 0.5 - 160 + i * 38, 72), alive)
	HudKit.stat(self, vp.x * 0.5 + 170, 20, "RECRUITS", "%d" % game.recruits, HudKit.INK, HudKit.RIGHT)
	# weapons
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), HudKit.GOLD)
	HudKit.stat(self, vp.x - 210, 20, "GRENADES", "%d" % e.grenades, HudKit.GOLD, HudKit.CENTER)
	HudKit.stat(self, vp.x - 90, 20, "ROCKETS", "%d" % e.rockets, HudKit.GOLD, HudKit.CENTER)
	# goals
	var y := 130.0
	HudKit.panel(self, Rect2(24, 116, 360, 40 + e.map.goals.size() * 34), Color(0, 0, 0, 0), 14, 0.85)
	for g in e.map.goals:
		var done := e.goal_done(g)
		draw_circle(Vector2(48, y + 22), 8, HudKit.GOOD if done else Color(1, 1, 1, 0.25), true, -1.0, true)
		HudKit.text(self, Vector2(66, y + 30), GOAL_TEXT.get(g, g.to_upper()), 20, HudKit.GOOD if done else HudKit.INK, HudKit.label_font())
		y += 34.0
	if _banner != "" and _t < _len:
		var a := clampf(minf(_t * 5.0, (_len - _t) * 4.0), 0.0, 1.0)
		HudKit.banner(self, vp, vp.y * 0.42, _banner, _sub, _col, a, 1.0 + 0.2 * exp(-_t * 8.0))
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var w := HudKit.width(msg, 24, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5, vp.y - 66, w, 46), Color(0, 0, 0, 0), 23, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 34), msg, 24, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	elif e.time < 20.0 and game.mission == 0:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 30), [["LEFT CLICK", "move"], ["RIGHT BUTTON", "fire"], ["G / MIDDLE", "grenade"],
			["R", "rocket"]], clampf((20.0 - e.time) / 2.0, 0.0, 1.0))
	if game.over:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.42 + 130), [["ENTER", "play again"], ["ESC", "menu"]])


func _helmet(c: Vector2, alive: bool) -> void:
	var col := OLIVE if alive else Color(1, 1, 1, 0.12)
	draw_circle(c, 13, col, true, -1.0, true)
	draw_rect(Rect2(c + Vector2(-16, 0), Vector2(32, 5)), col)
