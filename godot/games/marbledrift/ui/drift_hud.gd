class_name DriftHud
extends Control
## Marble Drift HUD: a big clock in the middle top (it pulses red in the last ten seconds), the score, the course's name
## and number, the checkpoints passed, READY / GO, the goal's time bonus, a broken marble's cause, TIME UP and the end.

const ACCENT := Color(0.5, 0.85, 1.0)
const DEATHS := {"shatter": "SHATTERED!", "acid": "DISSOLVED!", "fall": "INTO THE VOID!"}

@export var game: DriftGame

var _t := 0.0
var _go := 0.0
var _cp := 0.0
var _cp_n := 0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	game.course_started.connect(func(e): e.event.connect(_on_event))


func _on_event(kind: String, d: Dictionary) -> void:
	match kind:
		"go": _go = 1.0
		"checkpoint":
			_cp = 1.2
			_cp_n = d["n"]


func _process(delta: float) -> void:
	_t += delta
	_go = maxf(0.0, _go - delta)
	_cp = maxf(0.0, _cp - delta)
	queue_redraw()


func _draw() -> void:
	var e := game.engine
	if e == null:
		return
	var vp := size
	HudKit.panel(self, Rect2(24, 16, 300, 84), ACCENT)
	HudKit.stat(self, 48, 20, "SCORE", "%07d" % e.score, HudKit.GOLD, HudKit.LEFT)
	HudKit.panel(self, Rect2(vp.x - 344, 16, 320, 84), ACCENT)
	HudKit.stat(self, vp.x - 48, 20, "COURSE %d OF %d" % [game.index + 1, game.courses.size()], e.course.name.to_upper(),
		HudKit.INK, HudKit.RIGHT, 24)
	# the clock
	var low := e.clock < 10.0 and e.phase == DriftEngine.Phase.PLAY
	var col := HudKit.BAD.lerp(Color.WHITE, 0.4 * (0.5 + 0.5 * sin(_t * 10.0))) if low else HudKit.GOLD
	HudKit.panel(self, Rect2(vp.x * 0.5 - 110, 14, 220, 92), ACCENT)
	HudKit.text(self, Vector2(vp.x * 0.5, 36), "TIME", 16, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	HudKit.text(self, Vector2(vp.x * 0.5, 92), "%d" % ceili(maxf(0.0, e.clock)), 54, col, HudKit.font(true), HudKit.CENTER)
	var n := e.course.route.size()
	if n > 1:
		HudKit.text(self, Vector2(vp.x * 0.5, 130), "CHECKPOINT %d / %d" % [mini(e.checkpoint, n - 1), n - 1], 16,
			ACCENT if _cp > 0.0 else HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	if e.phase == DriftEngine.Phase.READY:
		HudKit.banner(self, vp, vp.y * 0.36, "COURSE %d" % (game.index + 1), e.course.name.to_upper(), ACCENT, clampf(e.phase_t * 2.0, 0.0, 1.0))
	elif _go > 0.0:
		HudKit.banner(self, vp, vp.y * 0.36, "GO!", "", HudKit.GOLD, minf(1.0, _go * 2.0))
	elif e.phase == DriftEngine.Phase.DYING:
		HudKit.banner(self, vp, vp.y * 0.36, DEATHS.get(e.death, "OOPS"), "", HudKit.BAD, minf(1.0, e.phase_t))
	elif e.phase == DriftEngine.Phase.FINISHED:
		var last := game.index + 1 >= game.courses.size()
		HudKit.banner(self, vp, vp.y * 0.36, "ALL COURSES DONE!" if last else "GOAL!",
			"%d SECONDS CARRY OVER" % int(e.clock), HudKit.GOLD, clampf((3.0 - e.phase_t) * 3.0, 0.0, 1.0))
	elif e.phase == DriftEngine.Phase.OVER or game.over:
		HudKit.banner(self, vp, vp.y * 0.42, "TIME UP" if not game.won else "WELL ROLLED!",
			"PRESS ENTER" if not game.demo else "", HudKit.BAD if not game.won else HudKit.GOLD, 1.0)
	if game.demo:
		HudKit.text(self, Vector2(vp.x * 0.5, vp.y - 30), "DEMO  -  PRESS ANY KEY TO PLAY", 20, HudKit.INK, HudKit.label_font(), HudKit.CENTER)
	elif e.time < 6.0 and game.index == 0:
		HudKit.hints(self, Vector2(vp.x * 0.5, vp.y - 50), [["ARROWS / STICK", "roll (screen directions)"], ["MOUSE", "trackball"]])
