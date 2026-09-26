class_name IngotHud
extends Control
## Ingot Run HUD: level and name, gold left, lives, score; banners for the exit opening, a clear, a catch, the end.

const ACCENT := Color(1.0, 0.78, 0.3)

@export var game: IngotGame

var _banner := ""
var _sub := ""
var _col := ACCENT
var _t := 0.0
var _len := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.level_started.connect(func(e):
		e.event.connect(_on_event)
		_show("LEVEL %d" % (game.level + 1), e.level.name.to_upper(), ACCENT, 2.5))
	game.game_over.connect(func(won): _show("THE MINE IS YOURS" if won else "GAME OVER", "SCORE %d" % game.score, HudKit.GOLD if won else HudKit.BAD, 99.0))


func _on_event(kind: String, _d: Dictionary) -> void:
	match kind:
		"all_gold": _show("THE WAY OUT IS OPEN", "CLIMB TO THE TOP", HudKit.GOLD, 2.2)
		"cleared": _show("LEVEL CLEAR", "", HudKit.GOOD, 3.0)
		"died": _show("CAUGHT!", "%d LIVES LEFT" % (game.lives - 1) if game.lives > 1 else "", HudKit.BAD, 3.0)


func _show(text: String, sub: String, col: Color, secs: float) -> void:
	_banner = text
	_sub = sub
	_col = col
	_t = 0.0
	_len = secs


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	HudKit.panel(self, Rect2(24, 16, 360, 84), ACCENT)
	HudKit.stat(self, 48, 20, "LEVEL %d / %d" % [game.level + 1, game.levels.size()], e.level.name.to_upper(), HudKit.INK, HudKit.LEFT, 26)
	HudKit.panel(self, Rect2(vp.x * 0.5 - 130, 16, 260, 84), HudKit.GOLD)
	var left := e._gold_left()
	HudKit.stat(self, vp.x * 0.5, 20, "GOLD LEFT", "EXIT OPEN" if e.revealed else str(left), HudKit.GOLD if not e.revealed else HudKit.GOOD, HudKit.CENTER, 32)
	HudKit.panel(self, Rect2(vp.x - 344, 16, 320, 84), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.RIGHT)
	for i in IngotGame.LIVES:
		HudKit.gem(self, Vector2(vp.x - 320 + i * 22, 58), 7.0, HudKit.BAD if i < game.lives else Color(1, 1, 1, 0.15))
	if _banner != "" and _t < _len:
		var a := clampf(minf(_t * 5.0, (_len - _t) * 4.0), 0.0, 1.0)
		HudKit.banner(self, vp, vp.y * 0.42, _banner, _sub, _col, a, 1.0 + 0.25 * exp(-_t * 8.0))
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 62, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 32), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	elif e.time < 15.0 and game.level == 0:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 30), [["ARROWS", "run, climb"], ["Z / X", "dig left / right"]], clampf((15.0 - e.time) / 2.0, 0.0, 1.0))
	if game.over:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.42 + 130), [["ENTER", "play again"], ["ESC", "menu"]])
