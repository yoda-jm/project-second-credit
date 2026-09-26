class_name CratesHud
extends Control
## Crate Keeper HUD: the puzzle's number and name, moves, pushes and par, crates in place, the controls, stars and
## the solved card.

const ACCENT := Color(0.95, 0.72, 0.35)

@export var game: CratesGame

var _t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.puzzle_started.connect(func(_e): _t = 0.0)


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := get_viewport_rect().size
	var lv := e.level
	HudKit.panel(self, Rect2(24, 16, 400, 84), ACCENT)
	HudKit.stat(self, 48, 20, "PUZZLE %d / %d" % [game.index + 1, game.puzzles.size()], lv.name.to_upper(), HudKit.INK, HudKit.LEFT, 26)
	HudKit.panel(self, Rect2(vp.x * 0.5 - 200, 16, 400, 84), Color(1, 1, 1, 0.25))
	HudKit.stat(self, vp.x * 0.5 - 120, 20, "MOVES", str(e.moves), HudKit.INK, HudKit.CENTER, 32)
	HudKit.stat(self, vp.x * 0.5, 20, "PUSHES", str(e.pushes), HudKit.INK, HudKit.CENTER, 32)
	HudKit.stat(self, vp.x * 0.5 + 120, 20, "PAR", str(lv.par) if lv.par > 0 else "-", HudKit.GOLD, HudKit.CENTER, 32)
	HudKit.panel(self, Rect2(vp.x - 324, 16, 300, 84), HudKit.GOOD)
	HudKit.stat(self, vp.x - 48, 20, "CRATES IN PLACE", "%d / %d" % [e.on_goal_count(), e.goals.size()], HudKit.GOOD, HudKit.RIGHT, 32)
	var best: int = game.best.get(lv.name, 0)
	if best > 0:
		var st := game.stars(lv, best)
		HudKit.text(self, Vector2(vp.x - 304, 124), "BEST %d" % best, 16, HudKit.MUTED, HudKit.label_font())
		for i in 3:
			HudKit.gem(self, Vector2(vp.x - 150 + i * 30, 118), 9.0, HudKit.GOLD if i < st else Color(1, 1, 1, 0.15))
	var st_t := game.solved_time()
	if st_t >= 0.0:
		var a := clampf(st_t * 3.0, 0.0, 1.0)
		var st := game.stars(lv, e.moves)
		HudKit.banner(self, vp, vp.y * 0.4, "SOLVED", "%d MOVES   -   %d PUSHES" % [e.moves, e.pushes], HudKit.GOOD, a, 1.0 + 0.25 * exp(-st_t * 8.0))
		for i in 3:
			var k := clampf((st_t - 0.4 - i * 0.25) * 4.0, 0.0, 1.0)
			HudKit.gem(self, Vector2(vp.x * 0.5 - 50 + i * 50, vp.y * 0.4 + 110), 18.0 * (0.6 + 0.4 * k), Color(HudKit.GOLD if i < st else Color(1, 1, 1, 0.2), k))
		if not game.demo:
			HudKit.hints(self, Vector2(vp.x * 0.5, vp.y * 0.4 + 170), [["ENTER", "next puzzle"], ["Z", "undo"], ["R", "again"]], a)
	if game.demo:
		var msg := "DEMO  -  PRESS ANY KEY TO PLAY"
		var wd := HudKit.width(msg, 22, HudKit.label_font()) + 60.0
		HudKit.panel(self, Rect2(vp.x * 0.5 - wd * 0.5, vp.y - 62, wd, 44), Color(0, 0, 0, 0), 22, 0.9)
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 32), msg, 22, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	elif st_t < 0.0:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 30), [["ARROWS", "walk and push"], ["CLICK", "walk there"], ["Z", "undo"], ["Y", "redo"], ["R", "restart"], ["N / P", "next / previous"]], 0.85)
