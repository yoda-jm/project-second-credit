class_name WhiskerHud
extends Control
## Whisker Alley HUD: nine lives as paw prints, rooms won, score; in a room its name, goal, time and the air.

const P = WhiskerEngine.Phase
const PURPLE := Color(0.75, 0.55, 1.0)
const ROOM_NAMES := ["THE FISHBOWL", "THE BIG CHEESE", "THE BIRD CAGE"]
const ROOM_GOALS := ["CATCH THE FISH - MIND THE EEL AND YOUR AIR", "CATCH FIVE MICE", "KNOCK DOWN THE CAGE, CATCH THE BIRD"]

@export var game: WhiskerGame

var _t := 0.0
var _banner := ""
var _banner_sub := ""
var _banner_col := HudKit.GOLD
var _banner_t := 10.0
var _banner_len := 2.0
var _fade := 0.0  ## iris wipe when going through a window


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.started.connect(func(e):
		e.event.connect(_on_event)
		_show("WHISKER ALLEY", "JUMP INTO AN OPEN WINDOW", PURPLE, 2.2))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"enter_room":
			_fade = 1.0
			_show(ROOM_NAMES[d["kind"]], ROOM_GOALS[d["kind"]], HudKit.GOLD, 2.4)
		"leave_room":
			_fade = 1.0
		"room_won":
			_show("PURR-FECT!", "+%d" % d["bonus"], HudKit.GOOD, 2.0)
		"room_failed":
			_show("SWEPT OUT!", "", HudKit.BAD, 1.6)
		"death":
			_show("OUCH!", "%d LIVES LEFT" % d["lives"], HudKit.BAD, 1.8)


func _show(text: String, sub: String, col: Color, secs: float) -> void:
	_banner = text
	_banner_sub = sub
	_banner_col = col
	_banner_t = 0.0
	_banner_len = secs


func _process(delta: float) -> void:
	_t += delta
	_banner_t += delta
	_fade = maxf(0.0, _fade - delta * 2.2)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	# left: nine lives as paw prints
	HudKit.panel(self, Rect2(24, 16, 400, 84), PURPLE)
	HudKit.text(self, Vector2(48, 38), "NINE LIVES", 15, HudKit.MUTED, HudKit.label_font())
	for i in WhiskerEngine.LIVES:
		_paw(Vector2(58 + i * 38, 72), 11.0, Color(1.0, 0.75, 0.5) if i < e.lives else Color(1, 1, 1, 0.12))
	# centre: rooms, or the room's goal and time
	if e.room:
		var r := e.room
		HudKit.panel(self, Rect2(vp.x * 0.5 - 200, 16, 400, 96), HudKit.GOLD)
		HudKit.stat(self, vp.x * 0.5 - 90, 20, ROOM_NAMES[r.kind], "%d / %d" % [r.caught, r.goal], HudKit.INK, HudKit.CENTER, 36)
		HudKit.stat(self, vp.x * 0.5 + 140, 20, "TIME", "%d" % ceili(maxf(0.0, r.time_left)),
			HudKit.BAD if r.time_left < 5.0 else HudKit.INK, HudKit.CENTER, 36)
		var frac := clampf(r.time_left / WhiskerRoom.ROOM_SECONDS, 0.0, 1.0)
		draw_rect(Rect2(vp.x * 0.5 - 170, 100, 340, 4), Color(1, 1, 1, 0.1))
		draw_rect(Rect2(vp.x * 0.5 - 170, 100, 340 * frac, 4), HudKit.GOLD if frac > 0.2 else HudKit.BAD)
		if r is FishbowlRoom:
			var air := (r as FishbowlRoom).air / FishbowlRoom.AIR_SECONDS
			if air < 0.999:
				var c := Vector2(vp.x * 0.5, vp.y - 110)
				HudKit.text(self, c + Vector2(0, -44), "AIR", 16, HudKit.MUTED, HudKit.label_font(), HudKit.CENTER)
				HudKit.ring(self, c, 26.0, air, Color(0.5, 0.85, 1.0) if air > 0.3 else HudKit.BAD, 6.0)
	else:
		HudKit.panel(self, Rect2(vp.x * 0.5 - 150, 16, 300, 84), PURPLE)
		HudKit.stat(self, vp.x * 0.5 - 60, 20, "ROOMS", "%d" % e.rooms_won, HudKit.INK, HudKit.CENTER)
		HudKit.stat(self, vp.x * 0.5 + 70, 20, "LEVEL", "%d" % e.level, HudKit.INK, HudKit.CENTER)
	# right: score
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), HudKit.GOLD)
	HudKit.stat(self, vp.x - 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.RIGHT)
	# iris wipe through the window
	if _fade > 0.0:
		var k := 1.0 - absf(_fade * 2.0 - 1.0)
		draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.02, 0.06, k))
	# banner
	if _banner != "" and _banner_t < _banner_len:
		var a := clampf(minf(_banner_t * 5.0, (_banner_len - _banner_t) * 4.0), 0.0, 1.0)
		HudKit.banner(self, vp, vp.y * 0.44, _banner, _banner_sub, _banner_col, a, 1.0 + 0.25 * exp(-_banner_t * 8.0))
	# hints
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var w := HudKit.width(msg, 24, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - w * 0.5, vp.y - 66, w, 46), Color(0, 0, 0, 0), 23, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 34), msg, 24, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	elif e.phase != P.GAME_OVER and e.time < 25.0:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 30), [["ARROWS", "walk"], ["SPACE", "jump"], ["DOWN + SPACE", "drop"],
			["ESC", "pause"]], clampf((25.0 - e.time) / 2.0, 0.0, 1.0))
	if e.phase == P.GAME_OVER:
		draw_rect(Rect2(Vector2.ZERO, vp), Color(0, 0, 0, 0.45))
		HudKit.banner(self, vp, vp.y * 0.45, "GAME OVER", "SCORE %d   -   %d ROOMS" % [e.score, e.rooms_won], HudKit.GOLD, 1.0)
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.45 + 150), [["ENTER", "play again"], ["ESC", "menu"]])


func _paw(c: Vector2, r: float, col: Color) -> void:
	draw_circle(c + Vector2(0, r * 0.35), r * 0.75, col, true, -1.0, true)
	for i in 4:
		var a := deg_to_rad(-135.0 + i * 30.0)
		draw_circle(c + Vector2(cos(a), sin(a)) * r * 0.95 + Vector2(0, r * 0.1), r * 0.3, col, true, -1.0, true)
